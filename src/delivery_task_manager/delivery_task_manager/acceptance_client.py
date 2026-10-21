"""Manual acceptance client for the two-stop delivery action."""

import argparse
import math
import time
from uuid import UUID

from action_msgs.msg import GoalStatus
from delivery_task_interfaces.action import DeliveryTask
from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.action import ActionClient
from rclpy.clock import Clock, ClockType
from rclpy.node import Node


STATUS_NAMES = {
    GoalStatus.STATUS_UNKNOWN: 'UNKNOWN',
    GoalStatus.STATUS_ACCEPTED: 'ACCEPTED',
    GoalStatus.STATUS_EXECUTING: 'EXECUTING',
    GoalStatus.STATUS_CANCELING: 'CANCELING',
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED',
    GoalStatus.STATUS_CANCELED: 'CANCELED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
}


def parse_options(args=None):
    """Parse only the inputs needed for one manual delivery run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pickup', nargs=2, type=float, required=True,
                        metavar=('X', 'Y'), help='Pickup map coordinates.')
    parser.add_argument('--dropoff', nargs=2, type=float, required=True,
                        metavar=('X', 'Y'), help='Drop-off map coordinates.')
    parser.add_argument('--pickup-yaw', type=float, default=0.0,
                        help='Pickup yaw in radians (default: 0).')
    parser.add_argument('--dropoff-yaw', type=float, default=0.0,
                        help='Drop-off yaw in radians (default: 0).')
    parser.add_argument('--cancel-at', choices=('none', 'pickup', 'dropoff'),
                        default='none', help='Stage at which to request cancel.')
    parser.add_argument('--cancel-delay-sec', type=float, default=0.0,
                        help='Steady-clock delay after stage feedback.')
    options = parser.parse_args(args)
    values = (*options.pickup, *options.dropoff,
              options.pickup_yaw, options.dropoff_yaw,
              options.cancel_delay_sec)
    if not all(math.isfinite(value) for value in values):
        parser.error('coordinates, yaw, and delay must be finite')
    if options.cancel_delay_sec < 0:
        parser.error('--cancel-delay-sec must be nonnegative')
    return options


def make_map_pose(x, y, yaw):
    """Create a map-frame PoseStamped; the task server refreshes its stamp."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def goal_id_text(goal_id):
    """Render the UUID carried by this client's own goal handle."""
    return str(UUID(bytes=bytes(goal_id.uuid)))


class DeliveryAcceptanceClient(Node):
    """Send one task goal and optionally cancel that exact goal handle."""

    def __init__(self, options):
        super().__init__('delivery_acceptance_client')
        self._options = options
        self._client = ActionClient(self, DeliveryTask, '/delivery_task')
        self._steady_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self._goal_handle = None
        self._stage = None
        self._cancel_timer = None
        self._cancel_sent = False
        self._cancel_response_seen = False
        self._result_seen = False
        self.done = False

    @staticmethod
    def _emit(message):
        print(f'[{time.time():.3f}] {message}', flush=True)

    def start(self):
        """Wait for the task server and submit a single delivery goal."""
        if not self._client.wait_for_server(timeout_sec=5.0):
            self._emit('/delivery_task action server unavailable')
            self.done = True
            return

        goal = DeliveryTask.Goal()
        goal.pickup_pose = make_map_pose(
            *self._options.pickup, self._options.pickup_yaw
        )
        goal.dropoff_pose = make_map_pose(
            *self._options.dropoff, self._options.dropoff_yaw
        )
        self._emit(
            f'Sending pickup={tuple(self._options.pickup)} '
            f'dropoff={tuple(self._options.dropoff)} frame=map '
            f'cancel_at={self._options.cancel_at} '
            f'cancel_delay_sec={self._options.cancel_delay_sec:g}'
        )
        future = self._client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        try:
            handle = future.result()
        except Exception as exc:
            self._emit(f'Goal request error: {exc}')
            self.done = True
            return
        self._emit(
            f'Delivery goal ID: {goal_id_text(handle.goal_id)}; '
            f'accepted={handle.accepted}'
        )
        if not handle.accepted:
            self._emit('Final status: REJECTED; no action result')
            self.done = True
            return
        self._goal_handle = handle
        result_future = handle.get_result_async()
        result_future.add_done_callback(self._on_result)
        # Feedback may have arrived before the send-goal response.
        self._maybe_arm_cancel()

    def _on_feedback(self, feedback_message):
        feedback = feedback_message.feedback
        self._stage = feedback.stage
        self._emit(f'Feedback: stage={feedback.stage} message={feedback.message}')
        self._maybe_arm_cancel()

    def _maybe_arm_cancel(self):
        if (self._goal_handle is None or self._result_seen or
                self._cancel_sent or self._cancel_timer is not None or
                self._stage != self._options.cancel_at):
            return
        if self._options.cancel_delay_sec == 0:
            self._request_cancel()
            return
        self._emit(
            f'Cancel scheduled at {self._stage} after '
            f'{self._options.cancel_delay_sec:g} s'
        )
        self._cancel_timer = self.create_timer(
            self._options.cancel_delay_sec,
            self._on_cancel_timer,
            clock=self._steady_clock,
        )

    def _on_cancel_timer(self):
        timer = self._cancel_timer
        if timer is None:
            return
        self._cancel_timer = None
        self.destroy_timer(timer)
        if self._stage != self._options.cancel_at or self._result_seen:
            self._emit('Cancel skipped: requested stage already ended')
            return
        self._request_cancel()

    def _request_cancel(self):
        if self._goal_handle is None or self._cancel_sent or self._result_seen:
            return
        self._cancel_sent = True
        self._emit(
            f'Cancel requested for delivery goal '
            f'{goal_id_text(self._goal_handle.goal_id)}'
        )
        try:
            future = self._goal_handle.cancel_goal_async()
            future.add_done_callback(self._on_cancel_response)
        except Exception as exc:
            self._emit(f'Cancel request error: {exc}')
            self._cancel_response_seen = True
            self._maybe_finish()

    def _on_cancel_response(self, future):
        self._cancel_response_seen = True
        try:
            response = future.result()
            ids = [goal_id_text(info.goal_id)
                   for info in response.goals_canceling]
            self._emit(
                f'Cancel response: return_code={response.return_code} '
                f'goals_canceling={ids}'
            )
        except Exception as exc:
            self._emit(f'Cancel response error: {exc}')
        self._maybe_finish()

    def _on_result(self, future):
        self._result_seen = True
        if self._cancel_timer is not None:
            self.destroy_timer(self._cancel_timer)
            self._cancel_timer = None
        try:
            response = future.result()
            result = response.result
            status = STATUS_NAMES.get(response.status, str(response.status))
            self._emit(
                f'Final status: {status} ({response.status}); '
                f'result: success={result.success} '
                f'failed_stage={result.failed_stage!r} '
                f'message={result.message!r}'
            )
        except Exception as exc:
            self._emit(f'Final result error: {exc}')
        self._maybe_finish()

    def _maybe_finish(self):
        if self._result_seen and (
                not self._cancel_sent or self._cancel_response_seen):
            self.done = True


def main(args=None):
    options = parse_options(args)
    rclpy.init(args=[])
    node = DeliveryAcceptanceClient(options)
    try:
        node.start()
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.2)
    except KeyboardInterrupt:
        node._emit('Client interrupted; this does not cancel the task goal')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
