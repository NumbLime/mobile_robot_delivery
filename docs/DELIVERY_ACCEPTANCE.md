# Delivery cancellation and timeout: manual acceptance

This is an **operator checklist**, not a record of a completed Gazebo/Nav2 run. The completed V0.1 acceptance results and remaining evidence limits are recorded in [PROJECT_STATUS.md](PROJECT_STATUS.md). Use the cases below for repeat runs and retain their actual output.

## Preparation and evidence

1. Check whether Gazebo, Nav2, or the task server is already running; use one instance of each. In a sourced workspace, start `navigation.launch.py` only if it is not running. Set the AMCL initial pose in RViz to the robot's actual map position. Wait until `/navigate_to_pose` is available and localization/TF are stable.
2. Build and source the workspace before using the new client:

   ```bash
   source /opt/ros/humble/setup.bash
   cd ~/mobile_robot_delivery
   colcon build --packages-select delivery_task_interfaces delivery_task_manager
   source install/setup.bash
   ```

3. Save the navigation launch console, task-server launch console, acceptance-client console, and `bt_navigator` ROS log for **each** case. Keep runtime logs outside this repository, for example in `~/mobile_robot_delivery_acceptance_logs/`. Record the chosen poses, yaw, `leg_timeout_sec`, `--cancel-at`, and `--cancel-delay-sec` with each run. For independent Nav2 terminal-state evidence, capture `/navigate_to_pose/_action/status` during the run after checking that topic exists. The status values are `4=SUCCEEDED`, `5=CANCELED`, and `6=ABORTED`. Match the status stream and Nav2 log to the target and run; do not assume client and Nav2 timestamps share a clock until checked.
4. The client prints Unix wall-time timestamps, its **own delivery goal ID**, stage feedback, cancel response (`return_code` and goal IDs transitioning to cancellation), and final delivery action status/result. It calls `cancel_goal_async()` only on the accepted goal handle it received. A zero `return_code` with that ID in `goals_canceling` indicates the delivery cancellation request was accepted; still wait for the final action result.

The client executable is `delivery_acceptance_client` in `delivery_task_manager`. It always sends two `map`-frame poses with `z=0`; yaw defaults to zero radians. `--cancel-at` is `none` (default), `pickup`, or `dropoff`. `--cancel-delay-sec` is a nonnegative steady-clock delay after the selected stage feedback. If feedback precedes the goal-acceptance response, the client waits for its handle before issuing cancellation. Pressing Ctrl+C only interrupts the client and does **not** cancel the action goal.

## 1. Regression: two-stop success

Restart **only the task server** after rebuilding so it uses the new installed code. Leave one Nav2/Gazebo instance running. Use the already accepted reachable pickup and drop-off as an initial choice, provided they remain appropriate for the robot's current pose:

```bash
ros2 launch delivery_task_manager task_manager.launch.py
ros2 run delivery_task_manager delivery_acceptance_client \
  --pickup 0.66 -1.11 --dropoff 0.12 -1.58
```

Run the launch and client in separate terminals. Expect `pickup` then `dropoff` feedback, final `SUCCEEDED`, `success=True`, `failed_stage=''`, and two successful Nav2 legs in order. If either pose is no longer reachable from the current localized pose, choose two reachable free-space map poses instead and record the change. This case checks that the new code preserved the prior success path; it does not establish any cancellation or timeout result.

## 2. Cancel during pickup

Use the normal task-server timeout (`120.0` seconds). Choose a reachable pickup far enough from the **current** robot pose for feedback to arrive while the robot is still on the pickup leg. Choose any reachable drop-off that would be obvious in the logs if wrongly sent. For example, after confirming these poses remain suitable:

```bash
ros2 run delivery_task_manager delivery_acceptance_client \
  --pickup 0.66 -1.11 --dropoff 0.12 -1.58 \
  --cancel-at pickup --cancel-delay-sec 2.0
```

Expect pickup feedback, a cancel request/response for the printed delivery goal ID, then delivery `CANCELED` with `success=False` and `failed_stage='pickup'`. Confirm the current Nav2 goal reaches a terminal state before the delivery result, and that there is no drop-off feedback, task-server `Navigating to dropoff.` line, or second Nav2 goal. If pickup finishes before the delayed cancel fires, use a farther **reachable** pickup or shorten the delay; do not count a late cancel as a pickup-cancel pass.

## 3. Cancel during drop-off

Choose a pickup that the robot can reach quickly and a reachable drop-off that takes long enough to cancel after `dropoff` feedback. Keep the normal task-server timeout. Substitute the selected coordinates below:

```bash
ros2 run delivery_task_manager delivery_acceptance_client \
  --pickup PICKUP_X PICKUP_Y --dropoff DROPOFF_X DROPOFF_Y \
  --cancel-at dropoff --cancel-delay-sec 2.0
```

Expect pickup to succeed before the drop-off feedback, then a cancel response for this client's goal ID, delivery `CANCELED`, `success=False`, and `failed_stage='dropoff'`. Confirm the second Nav2 goal reaches a terminal state before the delivery result. If pickup does not finish before the timeout or drop-off finishes before the cancel, move pickup closer to the current robot pose, move drop-off farther within reachable free space, or shorten the cancel delay. Restart and record each changed case rather than treating an unintended stage as accepted.

## 4. Per-leg timeout

Stop the previous **task-server** instance, then launch just one new task server with a shorter timeout; do not restart an already running Gazebo/Nav2 stack:

```bash
ros2 launch delivery_task_manager task_manager.launch.py leg_timeout_sec:=5.0
```

- **Pickup timeout:** Pick a reachable pickup whose route normally takes longer than 5 seconds, and any reachable drop-off. Run the client without `--cancel-at`. Expect only `pickup` feedback, delivery `ABORTED`, `success=False`, `failed_stage='pickup'`, and `timed out` in the message. Confirm the pickup Nav2 goal reached a terminal state before delivery returned; no drop-off goal should appear.
- **Drop-off timeout:** Start from a known localized robot pose. Choose a reachable pickup that normally finishes comfortably within 5 seconds, then a reachable drop-off whose route takes longer than 5 seconds. Expect `pickup` then `dropoff` feedback, delivery `ABORTED`, `success=False`, `failed_stage='dropoff'`, and `timed out` in the message. Confirm the second Nav2 goal is terminal before delivery returns.

If 5 seconds is too short for the first leg or Nav2 goal acceptance, increase `leg_timeout_sec` and choose a longer route for the leg being timed. If a leg reaches its goal or Nav2 aborts for another reason before the deadline, decrease the timeout or choose another reachable route. The same timeout applies independently to both legs; the drop-off timeout case needs the pickup leg to finish before that limit. If Nav2 never acknowledges acceptance or never returns a terminal result, the delivery action may remain pending; record that behavior rather than claiming timeout acceptance passed.

## Evidence boundaries

For each case, keep the client output and task-server/Nav2 logs showing the order of feedback, cancellation or timeout request, Nav2 terminal result, and outer delivery result. The delivery action reaching `CANCELED` or `ABORTED` is **not** evidence that the chassis has stopped. To make a stopped-state claim, separately observe the actual velocity command/controller state after the Nav2 goal ends. These cases do not test retries.
