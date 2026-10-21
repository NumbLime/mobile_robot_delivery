"""Check the manual client without connecting to a ROS action server."""

import math
from types import SimpleNamespace

import pytest

from delivery_task_manager.acceptance_client import DeliveryAcceptanceClient
from delivery_task_manager.acceptance_client import goal_id_text
from delivery_task_manager.acceptance_client import make_map_pose, parse_options


class FakeFuture:
    def __init__(self, result):
        self._result = result
        self.callback = None

    def add_done_callback(self, callback):
        self.callback = callback

    def result(self):
        return self._result


class FakeGoalHandle:
    def __init__(self, seed):
        self.goal_id = SimpleNamespace(uuid=[seed] * 16)
        self.cancel_calls = 0
        self.cancel_future = FakeFuture(SimpleNamespace(
            return_code=0,
            goals_canceling=[SimpleNamespace(goal_id=self.goal_id)],
        ))

    def cancel_goal_async(self):
        self.cancel_calls += 1
        return self.cancel_future


def bare_client(handle=None, cancel_at='pickup'):
    client = DeliveryAcceptanceClient.__new__(DeliveryAcceptanceClient)
    client._options = SimpleNamespace(
        cancel_at=cancel_at, cancel_delay_sec=0.0,
    )
    client._goal_handle = handle
    client._stage = None
    client._cancel_timer = None
    client._cancel_sent = False
    client._cancel_response_seen = False
    client._result_seen = False
    client.done = False
    client.messages = []
    client._emit = client.messages.append
    return client


def test_parse_options_and_map_poses():
    options = parse_options([
        '--pickup', '0.66', '-1.11',
        '--dropoff', '0.12', '-1.58',
        '--dropoff-yaw', str(math.pi),
        '--cancel-at', 'dropoff',
        '--cancel-delay-sec', '2.0',
    ])
    assert options.pickup == [0.66, -1.11]
    assert options.dropoff == [0.12, -1.58]
    assert options.cancel_at == 'dropoff'
    pose = make_map_pose(*options.dropoff, options.dropoff_yaw)
    assert pose.header.frame_id == 'map'
    assert pose.pose.position.y == -1.58
    assert math.isclose(pose.pose.orientation.z, 1.0)

    with pytest.raises(SystemExit):
        parse_options([
            '--pickup', '0', '0', '--dropoff', '1', '1',
            '--cancel-delay-sec', '-1',
        ])


def test_stage_feedback_before_goal_handle_cancels_only_owned_goal():
    owned = FakeGoalHandle(1)
    other = FakeGoalHandle(2)
    client = bare_client()
    client._on_feedback(SimpleNamespace(
        feedback=SimpleNamespace(stage='pickup', message='Navigating')
    ))
    assert not client._cancel_sent

    client._goal_handle = owned
    client._maybe_arm_cancel()
    assert owned.cancel_calls == 1
    assert other.cancel_calls == 0
    assert goal_id_text(owned.goal_id) in client.messages[-1]
    owned.cancel_future.callback(owned.cancel_future)
    assert client._cancel_response_seen
    assert any('return_code=0' in message for message in client.messages)


def test_other_stage_and_completed_goal_are_not_canceled():
    handle = FakeGoalHandle(3)
    client = bare_client(handle, cancel_at='dropoff')
    client._on_feedback(SimpleNamespace(
        feedback=SimpleNamespace(stage='pickup', message='Navigating')
    ))
    assert handle.cancel_calls == 0
    client._result_seen = True
    client._on_feedback(SimpleNamespace(
        feedback=SimpleNamespace(stage='dropoff', message='Navigating')
    ))
    assert handle.cancel_calls == 0


def test_delayed_cancel_only_fires_while_selected_stage_is_current():
    handle = FakeGoalHandle(5)
    client = bare_client(handle)
    client._options.cancel_delay_sec = 2.0
    client._steady_clock = object()
    client.create_timer = lambda _delay, callback, clock: SimpleNamespace(
        callback=callback
    )
    client.destroy_timer = lambda _timer: None

    client._on_feedback(SimpleNamespace(
        feedback=SimpleNamespace(stage='pickup', message='Navigating')
    ))
    timer = client._cancel_timer
    client._stage = 'dropoff'
    timer.callback()
    assert handle.cancel_calls == 0

    client._stage = 'pickup'
    client._maybe_arm_cancel()
    client._cancel_timer.callback()
    assert handle.cancel_calls == 1


def test_result_status_and_fields_are_printed():
    client = bare_client(FakeGoalHandle(4), cancel_at='none')
    response = SimpleNamespace(
        status=5,
        result=SimpleNamespace(
            success=False, failed_stage='pickup', message='timed out'
        ),
    )
    client._on_result(FakeFuture(response))
    assert client.done
    assert any('Final status: CANCELED (5)' in message
               and "failed_stage='pickup'" in message
               for message in client.messages)
