"""Check delivery ordering, cancellation, and timeouts without Nav2."""

import asyncio
import math
from threading import Event, Lock
from types import SimpleNamespace

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from rclpy.action import CancelResponse

from delivery_task_manager.delivery_task_server import DeliveryTaskServer
from delivery_task_manager.delivery_task_server import validate_map_pose
from delivery_task_manager.sequence import DeliveryStatus, NavigationOutcome
from delivery_task_manager.sequence import NavigationStatus, run_delivery


def make_pose():
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.orientation.w = 1.0
    return pose


async def until(predicate):
    for _ in range(1000):
        if predicate():
            return
        await asyncio.sleep(0.001)
    raise AssertionError('condition did not become true')


class FakeNavHandle:
    def __init__(self, accepted=True):
        self.accepted = accepted
        self.result_future = asyncio.get_running_loop().create_future()
        self.cancel_calls = 0

    def get_result_async(self):
        return self.result_future

    def cancel_goal_async(self):
        self.cancel_calls += 1
        response = asyncio.get_running_loop().create_future()
        response.set_result(SimpleNamespace())
        return response

    def finish(self, status):
        self.result_future.set_result(SimpleNamespace(status=status))


class FakeNavClient:
    def __init__(self, auto_replies=()):
        self.auto_replies = list(auto_replies)
        self.sent = []

    def server_is_ready(self):
        return True

    def send_goal_async(self, goal):
        future = asyncio.get_running_loop().create_future()
        self.sent.append((goal, future))
        if self.auto_replies:
            future.set_result(self.auto_replies.pop(0))
        return future


class FakeLogger:
    def info(self, _message):
        pass

    def error(self, _message):
        pass


class FakeTaskNode:
    _navigate = DeliveryTaskServer._navigate
    _wait_until_settled = DeliveryTaskServer._wait_until_settled
    _wait_for_cancel_state = DeliveryTaskServer._wait_for_cancel_state
    _execute_delivery = DeliveryTaskServer._execute_delivery
    _result = staticmethod(DeliveryTaskServer._result)

    def __init__(self, client, timeout=1.0):
        self._nav_client = client
        self._leg_timeout_sec = timeout
        self._cancel_event = Event()
        self._goal_lock = Lock()
        self._busy = True

    async def _wait_step(self):
        await asyncio.sleep(0.001)

    def get_clock(self):
        stamp = PoseStamped().header.stamp
        stamp.sec = 42
        return SimpleNamespace(now=lambda: SimpleNamespace(to_msg=lambda: stamp))

    def get_logger(self):
        return FakeLogger()

    def _accept_cancel(self, goal):
        response = DeliveryTaskServer._accept_cancel(self, goal)
        if response == CancelResponse.ACCEPT:
            goal.cancel_requested = True
        return response


class FakeTaskGoal:
    def __init__(self):
        self.request = SimpleNamespace(
            pickup_pose=make_pose(), dropoff_pose=make_pose()
        )
        self.feedback = []
        self.state = None
        self.cancel_requested = False

    @property
    def is_active(self):
        return self.state is None

    @property
    def is_cancel_requested(self):
        return self.cancel_requested

    def publish_feedback(self, feedback):
        self.feedback.append(feedback.stage)

    def succeed(self):
        self.state = 'succeeded'

    def abort(self):
        self.state = 'aborted'

    def canceled(self):
        self.state = 'canceled'


def test_dropoff_waits_for_pickup_result():
    async def scenario():
        finish_pickup = asyncio.Event()
        visited = []
        stages = []

        async def navigate(stage, _pose):
            visited.append(stage)
            if stage == 'pickup':
                await finish_pickup.wait()
            return NavigationOutcome(NavigationStatus.SUCCEEDED)

        task = asyncio.create_task(run_delivery(
            'pickup pose', 'dropoff pose', navigate, stages.append
        ))
        await until(lambda: visited == ['pickup'])
        assert stages == ['pickup']
        finish_pickup.set()
        result = await task
        assert result.status is DeliveryStatus.SUCCEEDED
        assert result.failed_stage == ''
        assert result.message == 'Pickup and drop-off reached.'
        assert visited == ['pickup', 'dropoff']
        assert stages == ['pickup', 'dropoff']

    asyncio.run(scenario())


def test_pickup_failure_skips_dropoff():
    async def scenario():
        visited = []
        stages = []

        async def navigate(stage, _pose):
            visited.append(stage)
            return NavigationOutcome(NavigationStatus.FAILED, 'pickup blocked')

        result = await run_delivery(
            'pickup pose', 'dropoff pose', navigate, stages.append
        )
        assert result.status is DeliveryStatus.FAILED
        assert result.failed_stage == 'pickup'
        assert result.message == 'pickup blocked'
        assert visited == ['pickup']
        assert stages == ['pickup']

    asyncio.run(scenario())


def test_dropoff_failure_reports_its_stage():
    async def scenario():
        visited = []

        async def navigate(stage, _pose):
            visited.append(stage)
            status = (NavigationStatus.SUCCEEDED if stage == 'pickup'
                      else NavigationStatus.FAILED)
            return NavigationOutcome(status, 'dropoff blocked')

        result = await run_delivery(
            'pickup pose', 'dropoff pose', navigate, lambda _stage: None
        )
        assert result.status is DeliveryStatus.FAILED
        assert result.failed_stage == 'dropoff'
        assert result.message == 'dropoff blocked'
        assert visited == ['pickup', 'dropoff']

    asyncio.run(scenario())


def test_navigation_exception_is_internal():
    async def scenario():
        async def navigate(_stage, _pose):
            raise RuntimeError('action transport failed')

        result = await run_delivery(
            'pickup pose', 'dropoff pose', navigate, lambda _stage: None
        )
        assert result.status is DeliveryStatus.FAILED
        assert result.failed_stage == 'internal'
        assert 'action transport failed' in result.message

    asyncio.run(scenario())


def test_map_pose_validation():
    pose = make_pose()
    assert validate_map_pose(pose, 'pickup') == ''

    pose.header.frame_id = 'odom'
    assert 'map frame' in validate_map_pose(pose, 'pickup')

    pose.header.frame_id = 'map'
    pose.pose.position.x = math.nan
    assert 'non-finite' in validate_map_pose(pose, 'pickup')

    pose.pose.position.x = 0.0
    pose.pose.orientation.w = 0.0
    assert 'unit quaternion' in validate_map_pose(pose, 'pickup')


def test_nav2_adapter_refreshes_stamp_and_checks_success_status():
    async def scenario():
        pose = make_pose()
        pose.header.stamp.sec = 1
        handle = FakeNavHandle()
        handle.finish(GoalStatus.STATUS_SUCCEEDED)
        client = FakeNavClient([handle])
        node = FakeTaskNode(client)
        result = await node._navigate(pose, Event(), 'pickup')
        assert result.status is NavigationStatus.SUCCEEDED
        assert client.sent[0][0].pose.header.stamp.sec == 42
        assert pose.header.stamp.sec == 1

    asyncio.run(scenario())


def test_nav2_rejection_and_failure_are_distinct():
    async def scenario():
        rejected = FakeTaskNode(FakeNavClient([FakeNavHandle(False)]))
        result = await rejected._navigate(make_pose(), Event(), 'pickup')
        assert result.status is NavigationStatus.REJECTED
        assert 'rejected' in result.message

        aborted_handle = FakeNavHandle()
        aborted_handle.finish(GoalStatus.STATUS_ABORTED)
        failed = FakeTaskNode(FakeNavClient([aborted_handle]))
        result = await failed._navigate(make_pose(), Event(), 'pickup')
        assert result.status is NavigationStatus.FAILED
        assert str(GoalStatus.STATUS_ABORTED) in result.message

    asyncio.run(scenario())


def test_task_action_succeeds_after_two_nav2_results():
    async def scenario():
        pickup = FakeNavHandle()
        pickup.finish(GoalStatus.STATUS_SUCCEEDED)
        dropoff = FakeNavHandle()
        dropoff.finish(GoalStatus.STATUS_SUCCEEDED)
        client = FakeNavClient([pickup, dropoff])
        node = FakeTaskNode(client)
        goal = FakeTaskGoal()
        result = await node._execute_delivery(goal)
        assert goal.state == 'succeeded'
        assert result.success
        assert result.failed_stage == ''
        assert result.message == 'Pickup and drop-off reached.'
        assert goal.feedback == ['pickup', 'dropoff']
        assert len(client.sent) == 2

    asyncio.run(scenario())


def test_pickup_timeout_waits_for_nav2_result_and_skips_dropoff():
    async def scenario():
        handle = FakeNavHandle()
        client = FakeNavClient([handle])
        node = FakeTaskNode(client, timeout=0.02)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: handle.cancel_calls == 1)
        assert not task.done()
        assert len(client.sent) == 1
        handle.finish(GoalStatus.STATUS_CANCELED)
        result = await task
        assert goal.state == 'aborted'
        assert not result.success
        assert result.failed_stage == 'pickup'
        assert 'timed out' in result.message
        assert goal.feedback == ['pickup']

    asyncio.run(scenario())


def test_timeout_before_nav2_acceptance_waits_then_cancels():
    async def scenario():
        handle = FakeNavHandle()
        client = FakeNavClient()
        node = FakeTaskNode(client, timeout=0.02)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: len(client.sent) == 1)
        await asyncio.sleep(0.03)
        assert not task.done()
        assert handle.cancel_calls == 0
        client.sent[0][1].set_result(handle)
        await until(lambda: handle.cancel_calls == 1)
        assert not task.done()
        handle.finish(GoalStatus.STATUS_CANCELED)
        result = await task
        assert goal.state == 'aborted'
        assert result.failed_stage == 'pickup'
        assert 'timed out' in result.message
        assert len(client.sent) == 1

    asyncio.run(scenario())


def test_dropoff_timeout_waits_for_nav2_result():
    async def scenario():
        pickup = FakeNavHandle()
        pickup.finish(GoalStatus.STATUS_SUCCEEDED)
        dropoff = FakeNavHandle()
        client = FakeNavClient([pickup, dropoff])
        node = FakeTaskNode(client, timeout=0.02)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: dropoff.cancel_calls == 1)
        assert not task.done()
        assert len(client.sent) == 2
        dropoff.finish(GoalStatus.STATUS_CANCELED)
        result = await task
        assert goal.state == 'aborted'
        assert not result.success
        assert result.failed_stage == 'dropoff'
        assert 'timed out' in result.message
        assert goal.feedback == ['pickup', 'dropoff']

    asyncio.run(scenario())


def test_pickup_cancel_forwards_and_waits_for_nav2_result():
    async def scenario():
        handle = FakeNavHandle()
        client = FakeNavClient([handle])
        node = FakeTaskNode(client)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: len(client.sent) == 1)
        assert node._accept_cancel(goal) == CancelResponse.ACCEPT
        await until(lambda: handle.cancel_calls == 1)
        assert not task.done()
        handle.finish(GoalStatus.STATUS_CANCELED)
        result = await task
        assert goal.state == 'canceled'
        assert not result.success
        assert result.failed_stage == 'pickup'
        assert len(client.sent) == 1

    asyncio.run(scenario())


def test_dropoff_cancel_forwards_and_waits_for_nav2_result():
    async def scenario():
        pickup = FakeNavHandle()
        pickup.finish(GoalStatus.STATUS_SUCCEEDED)
        dropoff = FakeNavHandle()
        client = FakeNavClient([pickup, dropoff])
        node = FakeTaskNode(client)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: len(client.sent) == 2)
        assert node._accept_cancel(goal) == CancelResponse.ACCEPT
        await until(lambda: dropoff.cancel_calls == 1)
        assert not task.done()
        dropoff.finish(GoalStatus.STATUS_CANCELED)
        result = await task
        assert goal.state == 'canceled'
        assert result.failed_stage == 'dropoff'
        assert goal.feedback == ['pickup', 'dropoff']

    asyncio.run(scenario())


def test_cancel_before_nav2_acceptance_cancels_later_accepted_goal():
    async def scenario():
        handle = FakeNavHandle()
        client = FakeNavClient()
        node = FakeTaskNode(client)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: len(client.sent) == 1)
        assert node._accept_cancel(goal) == CancelResponse.ACCEPT
        await asyncio.sleep(0.01)
        assert not task.done()
        assert handle.cancel_calls == 0
        client.sent[0][1].set_result(handle)
        await until(lambda: handle.cancel_calls == 1)
        assert not task.done()
        handle.finish(GoalStatus.STATUS_CANCELED)
        result = await task
        assert goal.state == 'canceled'
        assert result.failed_stage == 'pickup'
        assert len(client.sent) == 1

    asyncio.run(scenario())


def test_outer_action_waits_for_canceling_state():
    async def scenario():
        handle = FakeNavHandle()
        client = FakeNavClient([handle])
        node = FakeTaskNode(client)
        goal = FakeTaskGoal()
        task = asyncio.create_task(node._execute_delivery(goal))
        await until(lambda: len(client.sent) == 1)
        # rclpy enters CANCELING after the callback returns; keep it pending.
        response = DeliveryTaskServer._accept_cancel(node, goal)
        assert response == CancelResponse.ACCEPT
        await until(lambda: handle.cancel_calls == 1)
        handle.finish(GoalStatus.STATUS_CANCELED)
        await asyncio.sleep(0.01)
        assert not task.done()
        goal.cancel_requested = True
        result = await task
        assert goal.state == 'canceled'
        assert not result.success

    asyncio.run(scenario())


def test_cancel_during_stage_switch_does_not_send_dropoff():
    async def scenario():
        cancel_event = Event()
        visited = []
        stages = []

        async def navigate(stage, _pose):
            visited.append(stage)
            cancel_event.set()
            return NavigationOutcome(NavigationStatus.SUCCEEDED)

        result = await run_delivery(
            'pickup pose', 'dropoff pose', navigate,
            stages.append, cancel_event.is_set,
        )
        assert result.status is DeliveryStatus.CANCELED
        assert result.failed_stage == ''
        assert visited == ['pickup']
        assert stages == ['pickup']

    asyncio.run(scenario())
