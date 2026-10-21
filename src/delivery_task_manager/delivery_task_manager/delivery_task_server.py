"""Expose a two-stop delivery action backed by Nav2 NavigateToPose."""

from copy import deepcopy
import math
from threading import Event, Lock
import time

from action_msgs.msg import GoalStatus
from delivery_task_interfaces.action import DeliveryTask
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient, ActionServer
from rclpy.action import CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.clock import Clock, ClockType
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.task import Future

from delivery_task_manager.sequence import DeliveryOutcome, DeliveryStatus
from delivery_task_manager.sequence import NavigationOutcome, NavigationStatus
from delivery_task_manager.sequence import run_delivery


def validate_map_pose(pose, stage):
    """Return a reason when a delivery target is not a usable map pose."""
    if pose.header.frame_id != 'map':
        return f'{stage} pose must use the map frame'

    position = pose.pose.position
    orientation = pose.pose.orientation
    values = (
        position.x, position.y, position.z,
        orientation.x, orientation.y, orientation.z, orientation.w,
    )
    if not all(math.isfinite(value) for value in values):
        return f'{stage} pose contains a non-finite value'

    orientation_norm = sum(value * value for value in values[3:])
    if not 0.98 <= orientation_norm <= 1.02:
        return f'{stage} pose needs a unit quaternion orientation'

    return ''


class DeliveryTaskServer(Node):
    """Accept one delivery request and visit its two targets in order."""

    def __init__(self):
        super().__init__('delivery_task_server')
        self._goal_lock = Lock()
        self._busy = False
        self._cancel_event = None
        self._steady_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self.declare_parameter('leg_timeout_sec', 120.0)
        self._leg_timeout_sec = self.get_parameter(
            'leg_timeout_sec'
        ).value
        if (not isinstance(self._leg_timeout_sec, (int, float)) or
                not math.isfinite(self._leg_timeout_sec) or
                self._leg_timeout_sec <= 0):
            raise ValueError('leg_timeout_sec must be a positive finite number')
        callbacks = ReentrantCallbackGroup()
        self._nav_client = ActionClient(
            self, NavigateToPose, '/navigate_to_pose',
            callback_group=callbacks,
        )
        self._task_server = ActionServer(
            self, DeliveryTask, '/delivery_task',
            execute_callback=self._execute_delivery,
            goal_callback=self._accept_if_idle,
            cancel_callback=self._accept_cancel,
            callback_group=callbacks,
        )

    def _accept_if_idle(self, _request):
        with self._goal_lock:
            if self._busy:
                self.get_logger().warning('A delivery task is already active.')
                return GoalResponse.REJECT
            self._busy = True
            self._cancel_event = Event()
        return GoalResponse.ACCEPT

    def _accept_cancel(self, goal_handle):
        with self._goal_lock:
            if not self._busy or not goal_handle.is_active:
                return CancelResponse.REJECT
            self._cancel_event.set()
        return CancelResponse.ACCEPT

    async def _wait_step(self):
        """Yield to the ROS executor using a steady-clock timer."""
        wake = Future()
        timer = self.create_timer(
            0.05,
            lambda: wake.set_result(None) if not wake.done() else None,
            clock=self._steady_clock,
        )
        try:
            await wake
        finally:
            self.destroy_timer(timer)

    async def _wait_until_settled(self, future, cancel_event, deadline):
        """Notice a stop request without abandoning an unsettled Nav2 future."""
        while not future.done():
            if cancel_event.is_set():
                return NavigationStatus.CANCELED
            if time.monotonic() >= deadline:
                return NavigationStatus.TIMED_OUT
            await self._wait_step()
        return None

    async def _wait_for_cancel_state(self, goal_handle):
        """Let rclpy move the accepted cancel request to CANCELING."""
        while not goal_handle.is_cancel_requested:
            await self._wait_step()

    async def _navigate(self, pose, cancel_event, stage):
        if cancel_event.is_set():
            return NavigationOutcome(NavigationStatus.CANCELED)
        if not self._nav_client.server_is_ready():
            return NavigationOutcome(
                NavigationStatus.UNAVAILABLE, '/navigate_to_pose is not ready'
            )

        deadline = time.monotonic() + self._leg_timeout_sec
        goal = NavigateToPose.Goal()
        goal.pose = deepcopy(pose)
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        send_future = self._nav_client.send_goal_async(goal)
        stop_reason = await self._wait_until_settled(
            send_future, cancel_event, deadline
        )
        # A goal that has not been accepted cannot be canceled yet. Keep the
        # delivery action open until Nav2 answers, then cancel if accepted.
        try:
            nav_handle = await send_future
        except Exception as exc:
            return NavigationOutcome(
                NavigationStatus.INTERNAL,
                f'Nav2 goal acceptance failed: {exc}',
            )

        if nav_handle is None or not nav_handle.accepted:
            if stop_reason is not None:
                return NavigationOutcome(stop_reason)
            if cancel_event.is_set():
                return NavigationOutcome(NavigationStatus.CANCELED)
            return NavigationOutcome(
                NavigationStatus.REJECTED, 'Nav2 rejected the goal'
            )

        try:
            result_future = nav_handle.get_result_async()
        except Exception as exc:
            nav_handle.cancel_goal_async()
            return NavigationOutcome(
                NavigationStatus.INTERNAL,
                f'Cannot observe Nav2 goal result: {exc}',
            )

        if stop_reason is None:
            stop_reason = await self._wait_until_settled(
                result_future, cancel_event, deadline
            )
        if stop_reason is None and cancel_event.is_set():
            stop_reason = NavigationStatus.CANCELED
        if stop_reason is None and time.monotonic() >= deadline and not result_future.done():
            stop_reason = NavigationStatus.TIMED_OUT

        if stop_reason is not None and not result_future.done():
            try:
                nav_handle.cancel_goal_async()
            except Exception as exc:
                self.get_logger().error(
                    f'Could not request Nav2 cancellation for {stage}: {exc}'
                )
                # Even if the cancel service fails, do not close the delivery
                # action while this accepted goal may still be running.

        try:
            response = await result_future
        except Exception as exc:
            return NavigationOutcome(
                NavigationStatus.INTERNAL,
                f'Cannot confirm Nav2 goal ended: {exc}',
            )

        if stop_reason is NavigationStatus.CANCELED:
            return NavigationOutcome(
                NavigationStatus.CANCELED,
                f'{stage} canceled after Nav2 goal ended',
            )
        if stop_reason is NavigationStatus.TIMED_OUT:
            return NavigationOutcome(
                NavigationStatus.TIMED_OUT,
                f'{stage} navigation timed out after '
                f'{self._leg_timeout_sec:g} s; Nav2 goal ended with status '
                f'{response.status}',
            )

        if response.status == GoalStatus.STATUS_SUCCEEDED:
            return NavigationOutcome(NavigationStatus.SUCCEEDED)
        return NavigationOutcome(
            NavigationStatus.FAILED,
            f'Nav2 goal finished with status {response.status}',
        )

    @staticmethod
    def _result(success, failed_stage='', message=''):
        result = DeliveryTask.Result()
        result.success = success
        result.failed_stage = failed_stage
        result.message = message
        return result

    async def _execute_delivery(self, goal_handle):
        cancel_event = self._cancel_event
        try:
            request = goal_handle.request
            for stage, pose in (
                ('pickup', request.pickup_pose),
                ('dropoff', request.dropoff_pose),
            ):
                error = validate_map_pose(pose, stage)
                if error:
                    if cancel_event.is_set():
                        await self._wait_for_cancel_state(goal_handle)
                    with self._goal_lock:
                        if cancel_event.is_set():
                            goal_handle.canceled()
                            return self._result(
                                False, '', 'Delivery canceled before navigation.'
                            )
                        goal_handle.abort()
                    return self._result(False, 'validation', error)

            def report_stage(stage):
                feedback = DeliveryTask.Feedback()
                feedback.stage = stage
                feedback.message = f'Navigating to {stage}.'
                goal_handle.publish_feedback(feedback)
                self.get_logger().info(feedback.message)

            outcome = await run_delivery(
                request.pickup_pose,
                request.dropoff_pose,
                lambda stage, pose: self._navigate(pose, cancel_event, stage),
                report_stage,
                cancel_event.is_set,
            )
            if (outcome.status is DeliveryStatus.CANCELED or
                    (cancel_event.is_set() and outcome.success)):
                await self._wait_for_cancel_state(goal_handle)
            with self._goal_lock:
                if (cancel_event.is_set() and
                        outcome.status is DeliveryStatus.SUCCEEDED):
                    outcome = DeliveryOutcome(
                        DeliveryStatus.CANCELED,
                        message='Delivery canceled after navigation ended.',
                    )
                if outcome.status is DeliveryStatus.CANCELED:
                    goal_handle.canceled()
                elif outcome.success:
                    goal_handle.succeed()
                else:
                    goal_handle.abort()
            return self._result(
                outcome.success, outcome.failed_stage, outcome.message
            )
        except Exception as exc:
            self.get_logger().error(f'Delivery task failed: {exc}')
            with self._goal_lock:
                if goal_handle.is_active:
                    goal_handle.abort()
            return self._result(False, 'internal', str(exc))
        finally:
            with self._goal_lock:
                self._busy = False
                self._cancel_event = None


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryTaskServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
