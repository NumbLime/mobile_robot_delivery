# Project status

## Current stage: V0.1 two-stop delivery demonstration delivered

The workspace contains the robot description, Gazebo Classic world, mapping and static-map localization launch files. `navigation.launch.py` and its configuration run the Nav2 single-goal stack using Humble's planner, controller, behavior, BT navigator, velocity smoother, and lifecycle manager nodes. The user has confirmed that single-goal navigation runtime acceptance is complete.

The navigation bringup reuses the existing Gazebo, robot spawn, controller spawners, map server, AMCL, and RViz flow. Navigation is requested only after the robot spawn and both controllers have completed successfully. The map and AMCL are started once, and SLAM is disabled in this mode.

The first delivery task increment accepts a pickup pose and a drop-off pose, then uses Nav2 to visit them in order. The user confirmed a successful two-stop run in Gazebo/Nav2; the client output and corresponding ROS logs are recorded below. The updated task node's success path, pickup/drop-off cancellation, and pickup/drop-off timeout were accepted in Gazebo/Nav2 on 2026-10-20. B6 now has independent stopped-state evidence for the prescribed success, cancellation, and timeout scenarios; an earlier timeout run's sustained odom yaw remains unexplained and is documented below.

## V0.1 量化进度基线（2026-10-19 冻结）

**本阶段终点：室内两站配送演示版 V0.1。** 在现有 Gazebo 场景展示两站配送成功流程；取得取货段与送达段分别取消、分别超时的运行证据；独立记录任务结束后的停车证据；完成简短演示、文档收尾和本增量备份。下表是本阶段唯一的进度计分表，静态测试分与仿真运行验收分分别记录。**分数表示阶段交付进度，不代表 ROS 知识掌握百分比。**

| 项目 | 分值 | 已得分 | 状态 | 验收依据 / 待取得证据 |
| --- | ---: | ---: | --- | --- |
| A1 机器人仿真与基本控制 | 10 | 10 | 已完成，运行验证 | 现有 Gazebo 仿真和键盘控制运行证据；见下方定位与遥控记录。 |
| A2 建图、地图保存、AMCL 定位与 RViz 地图 QoS 修复 | 10 | 10 | 已完成，运行验证 | `maps/delivery_world.yaml`、`maps/delivery_world.pgm` 及建图、定位、地图显示的既有运行证据；见下方验收记录。 |
| A3 Nav2 单点导航 | 10 | 10 | 已完成，运行验证 | 三个独立目标成功；运动期间已核对 `velocity_smoother → /diff_drive_controller/cmd_vel_unstamped → diff_drive_controller`。 |
| A4 原版两站配送成功路径 | 15 | 15 | 已完成，运行验证 | 客户端依次收到 `pickup`、`dropoff`、`SUCCEEDED`；下方 Nav2 日志证明取货段成功后才启动送达段。 |
| A5 取消与单段超时的实现、构建和单元测试 | 10 | 10 | 已完成，仅代码与静态测试 | 现有取消/超时实现、构建及单元测试记录；本项得分本身不作为运行证据，运行验收另见 B2～B5。 |
| A6 独立验收客户端与操作指南 | 5 | 5 | 已完成，仅工具静态检查 | `delivery_acceptance_client` 入口、`--help`、客户端测试及 [操作指南](DELIVERY_ACCEPTANCE.md)；当前包测试汇总为 23 通过、1 跳过、0 失败。 |
| A7 故障经验与证据边界文档 | 5 | 5 | 已完成，文档核对 | [导航排查记录](NAVIGATION_TROUBLESHOOTING.md)、[配送验收指南](DELIVERY_ACCEPTANCE.md)及本文件中的静态/运行证据边界。 |
| B1 重启更新后的任务节点，成功路径回归 | 5 | 5 | 已完成，2026-10-20 运行验收 | 新节点依次反馈 `pickup`、`dropoff`，两段 Nav2 目标成功，配送最终 `SUCCEEDED`、`success=True`；日志见下方。 |
| B2 取货段取消 | 5 | 5 | 已完成，2026-10-20 运行验收 | 取货反馈后取消；Nav2 取货目标先结束，配送 `CANCELED`、`failed_stage='pickup'`；无送达目标；日志见下方。 |
| B3 送达段取消 | 5 | 5 | 已完成，2026-10-20 运行验收 | 取货目标成功后在送达段取消；Nav2 送达目标先结束，配送 `CANCELED`、`failed_stage='dropoff'`；日志见下方。 |
| B4 取货段超时 | 5 | 5 | 已完成，2026-10-20 运行验收 | `leg_timeout_sec=5.0`；仅 `pickup` 反馈，Nav2 取货目标先取消，配送 `ABORTED`、`failed_stage='pickup'`、消息含 `timed out`；无送达目标。 |
| B5 送达段超时 | 5 | 5 | 已完成，2026-10-20 运行验收 | `leg_timeout_sec=10.0`；近起点的取货目标成功后进入 `dropoff`，Nav2 送达目标先取消，配送 `ABORTED`、`failed_stage='dropoff'`、消息含 `timed out`。 |
| B6 终态后停车证据 | 5 | 5 | 已完成，本阶段场景的独立运行证据 | 成功、取消报告及两次取货超时复现均记录先运动、后经短暂制动进入持续小幅位姿变化；证据路径与旧异常限制见下方。得分不代表所有超时运行保证停稳或旧异常已修复。 |
| B7 约 1～2 分钟的两站配送演示 | 3 | 3 | 已完成，2026-10-21 演示核对 | 仓库外客户端日志与原片显示 `pickup`、`dropoff` 和最终 `SUCCEEDED`、`success=True`；63.210 秒成片保留原片完整顺序，说明片头片尾标明非原始录屏。 |
| B8 按实际验收收尾文档并备份本增量 | 2 | 2 | 已完成，2026-10-21 文档与仓库备份 | README、状态文档、验收指南与实际接口、节点和客户端一致；本阶段仓库内项目文件提交并推送到现有 `origin/master`，仓库外运行证据未纳入。 |
| **合计** | **100** | **100** | **A 项 65 分；B1～B8 已得 35 分** | V0.1 阶段交付完成；旧超时偏航风险留待后续。 |

| 固定状态字段 | 当前记录 |
| --- | --- |
| 本阶段终点 | V0.1 两站配送演示版。 |
| 阶段进度 | **100/100**；A1～A7 共 65 分，B1～B8 共 35 分；V0.1 阶段交付完成。**100 分是本阶段交付进度，不代表 ROS 知识掌握百分比。** |
| 今日进度 | **2026-10-21：10/10 个新增交付分值**，B6 5 分、B7 3 分、B8 2 分；2026-10-20 的 B1～B5 为此前累计 25/25 分。**今日到此停止，不自动追加任务。** |
| 本次完成项及证据 | B7 客户端 `pickup`、`dropoff` 反馈和最终 `SUCCEEDED (4)`、`success=True` 与原片一致；63.210 秒成片完整保留原片，并用明确标识的说明片头片尾呈现真实信息。B8 核对 README、状态文档、验收指南与本阶段接口、任务节点、客户端、测试及安装入口；将仓库内文件备份到现有 GitHub 远端。原片、日志、bag、离线报告和成片都在仓库外，**不属于本次 GitHub 备份**；本次没有新增仿真运行或构建。 |
| 阻塞项和下次第一步 | V0.1 计分项无剩余；最初超时 bag 的约 0.15 rad 持续同向 odom 偏航仍是未解决的复现风险，后续若复现须结合 Gazebo 模型姿态、轮反馈和控制器命令接收排查。本轮完成后停止，不开始下一阶段开发。 |
| 预计剩余学习次数及完成时间 | V0.1 已于 **2026-10-21** 完成交付；后续异常排查属于单独安排，不纳入本阶段剩余次数。 |

**V0.1 范围边界：**本阶段不加入重试、任务队列、装卸操作、新界面、回充、专项绕障/重规划、自定义插件比较或实机部署。取货失败中止已有单元测试覆盖；独立仿真故障注入留到后续阶段，**不计入 V0.1 验收**。

**后续更新规则：**每次开始按用户提供的可用时间安排少量任务；未说明时按约 60 分钟。开始时写明今日计划分值与停止条件，完成后不自动追加任务，并在结束时更新上方同一张固定状态表。排错只有形成具体结论或记录才算有效产出；原任务未通过验收时，该项不得加分。若需调整 V0.1 范围，先说明原因及分值、时间影响，等待用户确认。

## Navigation interfaces

- Saved map: `maps/delivery_world.yaml` with image `maps/delivery_world.pgm`; 117 × 118 cells at 0.05 m/cell.
- Laser scan: `/scan`, frame `laser_link`.
- Localization TF: AMCL publishes `map -> odom`.
- Odometry TF: `diff_drive_controller` publishes `odom -> base_footprint`.
- Navigation base frame: `base_footprint`.
- Controller input: `/diff_drive_controller/cmd_vel_unstamped` (`use_stamped_vel: false`).
- Velocity path: Nav2 controller and behavior outputs feed the velocity smoother; its output is remapped to the differential-drive controller input.
- Global costmap: static `/map` layer and inflation layer.
- Local costmap: `/scan` obstacle layer and inflation layer.
- Footprint: 0.40 m by 0.38 m rectangle, including the wheel lateral extent, with 0.02 m padding.
- All navigation and localization nodes use simulation time.

## Delivery task interfaces

- Task action: `/delivery_task`, type `delivery_task_interfaces/action/DeliveryTask`.
- Goal: `pickup_pose` and `dropoff_pose` are `geometry_msgs/PoseStamped` in the `map` frame. The task server refreshes each goal timestamp when sending it to Nav2.
- Feedback: `stage` is `pickup` or `dropoff` when that navigation leg begins, with a short `message`.
- Result: `success`, `failed_stage`, and `message`. A failure at pickup prevents the drop-off goal from being sent; an invalid input reports `validation`.
- Nav2 client: one `/navigate_to_pose` goal (type `nav2_msgs/action/NavigateToPose`) at a time. The next goal is sent only after the previous goal returns `STATUS_SUCCEEDED`.
- The task server accepts one delivery request at a time. It accepts cancellation of the active `/delivery_task` goal. If Nav2 has not answered goal acceptance yet, the task waits for that answer; if Nav2 accepts, it requests cancellation of that goal and waits for its terminal result. Cancellation between legs prevents sending the next goal. The delivery action then ends as `CANCELED`, with `success: false`; `failed_stage` names the active leg, or is empty if no leg was active.
- `leg_timeout_sec` is a positive, finite per-leg timeout, default `120.0` seconds. It uses a steady clock and includes waiting for Nav2 goal acceptance and result. On timeout, the task requests cancellation of an accepted Nav2 goal and waits for its terminal result before returning delivery action `ABORTED`, `success: false`, `failed_stage: pickup` or `dropoff`, and a message containing `timed out`. If Nav2 never answers acceptance or never returns a terminal result, the delivery action remains pending rather than claiming that Nav2 has stopped.
- Nav2 goal rejection, Nav2 terminal failure, timeout, user cancellation, and internal errors have separate internal outcomes and messages. Rejection/failure/timeout abort the delivery action with the affected stage; an internal error aborts with `failed_stage: internal`. Retry is not implemented. The separate `task_manager.launch.py` sets `use_sim_time: true` and starts only this task node; the timeout clock is deliberately steady time.

## Build and launch

```bash
source /opt/ros/humble/setup.bash
cd ~/mobile_robot_delivery
colcon build --packages-up-to delivery_robot_bringup
source install/setup.bash
ros2 launch delivery_robot_bringup navigation.launch.py
```

Optional arguments include `map:=/absolute/path/to/map.yaml`, `x:=...`, `y:=...`, `z:=...`, `yaw:=...`, `gui:=false`, and `rviz:=false`.

The existing modes remain available:

```bash
ros2 launch delivery_robot_bringup mapping.launch.py
ros2 launch delivery_robot_bringup localization.launch.py
```

Build the new task packages and start the task server in a separate terminal after navigation and AMCL are ready:

```bash
colcon build --packages-up-to delivery_task_manager
source install/setup.bash
ros2 launch delivery_task_manager task_manager.launch.py
```

The task launch does not start Gazebo, Nav2, AMCL, or RViz a second time. Use `leg_timeout_sec:=30.0` to override the default per-leg timeout when launching the task node. The previously accepted success run used `map`-frame pickup `(0.66, -1.11)` and drop-off `(0.12, -1.58)` with feedback enabled; both poses had the unit quaternion `(0, 0, 0, 1)`. The following example reproduces those supplied coordinates and orientation with `z: 0.0`.

```bash
ros2 action send_goal --feedback \
  /delivery_task delivery_task_interfaces/action/DeliveryTask \
  '{pickup_pose: {header: {frame_id: map}, pose: {position: {x: 0.66, y: -1.11, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}, dropoff_pose: {header: {frame_id: map}, pose: {position: {x: 0.12, y: -1.58, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}'
```

## Validation status

### Runtime acceptance passed

- Mapping and map saving are complete. The saved files are `maps/delivery_world.yaml` and `maps/delivery_world.pgm` (117 × 118 cells, 0.05 m/cell).
- Static-map localization has been run and verified: after setting AMCL's initial pose, localization worked and keyboard teleoperation moved the robot as expected.
- RViz initially did not receive the static map because the Map display subscription used Volatile durability. After setting that display to Reliable + Transient Local, the map was received and displayed.
- After localization initialization, Nav2 lifecycle nodes entered `active`, the `/navigate_to_pose` action server was available, and the `map` to `base_footprint` TF stayed stable.
- Three independent NavigateToPose goals each reported “Reached the goal!” and “Goal succeeded”:
  - `(-0.02, -0.01) → (0.66, -1.11)`
  - `(0.63, -0.98) → (0.12, -1.58)`
  - `(0.23, -1.53) → (-0.39, 1.48)`
- `ros2 topic info /diff_drive_controller/cmd_vel_unstamped --verbose` showed `velocity_smoother` as publisher and `diff_drive_controller` as subscriber. The Reliable publisher and Best Effort subscriber matched successfully; `ros2 topic echo` received non-zero `Twist` messages during motion. This is motion evidence, not a separate check of the stopped state.
- Two-stop delivery in Gazebo/Nav2 succeeded. For the `/delivery_task` goal above, the user-provided `ros2 action send_goal --feedback` output showed `Goal accepted`, then feedback stages `pickup` and `dropoff`, then `success: true`, `failed_stage: ''`, `message: Pickup and drop-off reached.`, and `Goal finished with status: SUCCEEDED`.
- The local ROS log `~/.ros/log/bt_navigator_20335_1791887692620.log` records pickup navigation starting at `1791888193.339` toward `(0.66, -1.11)` and succeeding at `1791888208.499`; drop-off navigation starts at `1791888208.503` toward `(0.12, -1.58)` and succeeds at `1791888236.623`. `~/.ros/log/python3_20577_1791887808291.log` records the task server's `Navigating to pickup.` at `1791888193.336` and `Navigating to dropoff.` at `1791888208.501`. These records establish that drop-off started only after pickup succeeded in this run.
- On 2026-10-20, B1 passed with the updated task node. `~/mobile_robot_delivery_acceptance_logs/B1_2026-10-20/client.log` records goal `f372b99c-cc36-46d1-8d7f-f628da58b145`, `pickup` then `dropoff` feedback, and final `SUCCEEDED (4)`, `success=True`. The navigation console records the first `Goal succeeded` at `1792481372.943` and the second at `1792481427.802`. During the second leg, Nav2 reported `Failed to make progress`, cleared costmaps, resumed control, and eventually succeeded. This was Nav2 recovery within the navigation leg, not a task-level retry.
- B2 passed in `~/mobile_robot_delivery_acceptance_logs/B2_2026-10-20/`: client goal `a7d78581-c24d-495a-a714-d1db92bb8ce3` received `pickup` feedback, then cancellation was accepted with `return_code=0` for that goal ID. The navigation console records `Goal canceled` at `1792482284.398`; the client records final `CANCELED (5)`, `success=False`, `failed_stage='pickup'` at `1792482284.402`. The task and client logs contain no `dropoff` stage, and the navigation log ends with the pickup cancellation; no drop-off goal was sent in this run.
- B3 passed in `~/mobile_robot_delivery_acceptance_logs/B3_2026-10-20/` (`client.log`, `task_server_console.log`, `navigation_console.log`, `run_notes.txt`). Initial pose was `(0, 0, 0)`; pickup `(0.0, -0.49)`, drop-off `(-0.39, 1.48)`, `leg_timeout_sec=120.0`, `cancel_at=dropoff`, `cancel_delay_sec=2.0`. Client goal `e13a7674-7c30-4ac6-bdae-10fad7d94f9e`: Nav2 pickup `Goal succeeded` at `1792482934.940`; client received `dropoff` feedback at `1792482934.965`; cancel response `return_code=0` at `1792482936.968`; Nav2 reported `Goal canceled` at `1792482936.989`; delivery returned `CANCELED (5)`, `success=False`, `failed_stage='dropoff'` at `1792482936.994`.
- B4 passed in `~/mobile_robot_delivery_acceptance_logs/B4_2026-10-20/` (`client.log`, `task_server_console.log`, `navigation_console.log`, `run_notes.txt`). With `leg_timeout_sec=5.0`, pickup `(0.66, -1.11)` and drop-off `(0.12, -1.58)`, the client received only `pickup` feedback. Nav2 reported pickup `Goal canceled` at `1792486264.875`; delivery returned `ABORTED (6)`, `success=False`, `failed_stage='pickup'`, message containing `timed out` at `1792486264.880`. The task/client logs have no `dropoff` stage, and the navigation log records only the canceled pickup goal; no drop-off goal was sent in this run.
- B5 passed in `~/mobile_robot_delivery_acceptance_logs/B5_2026-10-20/` (`client.log`, `task_server_console.log`, `navigation_console.log`, `run_notes.txt`, `pose_before_goal.log`). Before sending, `tf2_echo` showed `map → base_footprint` near `(-0.002, -0.014, -0.020 rad)`. Pickup `(0, 0)` was therefore near the starting pose; drop-off was `(-0.39, 1.48)` and `leg_timeout_sec=10.0`. Nav2 pickup `Goal succeeded` at `1792486875.123`; the client then received `dropoff` feedback. Nav2 reported drop-off `Goal canceled` at `1792486885.230`; delivery returned `ABORTED (6)`, `success=False`, `failed_stage='dropoff'`, message containing `timed out` at `1792486885.234`.
- B6 independent stopped-state evidence is recorded outside the repository under `~/mobile_robot_delivery_acceptance_logs/`. The success report `B6_2026-10-21/success/B6_SUCCESS_OFFLINE_ANALYSIS.md` and cancellation report `B6_2026-10-21/cancel/B6_CANCEL_OFFLINE_ANALYSIS.md` use client results, action status, `/clock`, velocity commands and odom to show motion followed by small velocities and pose changes from about T+2 to T+12 seconds. The first timeout reproduction `B6_timeout_repro/B6_TIMEOUT_REPRO_OFFLINE_ANALYSIS.md` and second timeout reproduction `B6_timeout_repro_2/B6_TIMEOUT_REPRO_2_OFFLINE_ANALYSIS.md` additionally compare Gazebo `delivery_robot` model pose/twist and wheel joints with odom through T+46.976 and T+59.496 seconds, respectively. In the second reproduction, model yaw changes at T+12～22, +22～32, and +32～end are only `+0.000745`, `+0.000462`, and `+0.000261 rad`; corresponding odom changes are `+0.000532`, `+0.000367`, and `-0.000098 rad`. Both reproductions provide positive evidence of settling after the short post-result motion period.
- **B6 evidence limit and unresolved risk:** action return does not mean immediate stopping: the second timeout reproduction still shows about `0.079 m` model displacement during T～T+2 seconds. A zero Twist was recorded as **published** at about T+0.880 seconds, but this alone does not prove that the controller received it. The original timeout report `B6_2026-10-21/timeout/B6_TIMEOUT_OFFLINE_ANALYSIS.md` found about **0.15 rad** of sustained same-direction odom yaw after T+12 seconds. That bag lacks Gazebo model pose and wheel feedback, so the source of the yaw cannot be determined. Keep this as an unresolved reproduction risk for later investigation. B6's 5 points mean the V0.1 prescribed scenarios have independent positive stopped-state evidence; they do **not** mean every timeout run is guaranteed to stop or that the old anomaly was fixed.
- B7 evidence is outside the repository in `~/mobile_robot_delivery_acceptance_logs/B7_2026-10-21/`: `client.log`, `B7_two_stop_delivery_demo_2026-10-21.webm` (original recording), and `B7_two_stop_delivery_demo_final_2026-10-21.webm` (63.210-second final cut). The client goal `f028f760-e61d-4dd8-aa18-5748ab7766b1` reports `pickup` then `dropoff` feedback, followed by `SUCCEEDED (4)` and `success=True`. The final cut adds about 12 seconds each of introductory and closing text marked as non-original footage; the original 39.209-second recording remains complete, in order, and at its original playback speed. The recording shows the Gazebo/RViz run and client output; it is a demonstration of this successful run, not new evidence that the old timeout anomaly was resolved. These logs, bags, reports and videos are **not in the GitHub backup**, which covers only repository files.
- B7 核对完成时，阶段先达到 **98/100**，2026-10-21 今日进度先达到 **8/10**；随后 B8 文档与仓库备份完成，固定状态表更新为 100/100 和 10/10。

### Build and static checks

- `navigation.launch.py`, `navigation.yaml`, and `navigation.rviz` are implemented. `delivery_robot_bringup` built successfully with `colcon build --packages-select delivery_robot_bringup`.
- Python syntax and flake8 checks passed for the launch files; YAML/RViz and package XML parsing passed; Xacro expanded successfully; and `--show-args` succeeded for the mapping, localization, and navigation launch entries. Static assertions confirmed the configured frames, topics, command remaps, costmap layers, and map display QoS.
- `delivery_task_interfaces` and `delivery_task_manager` built successfully. The cancellation/timeout increment passed 16 task behavior tests covering ordered success, stage failures, validation and internal errors, Nav2 rejection/failure, timeout and cancellation in both stages, cancellation before Nav2 acceptance, cancellation while changing stages, and waiting for the outer action's `CANCELING` state. The package test suite reported 18 passed and one copyright check skipped, including flake8 and pep257.
- `task_manager.launch.py --show-args` resolved the installed `leg_timeout_sec` argument with default `120.0`. These checks did not start Gazebo/RViz or send an action goal or velocity command.
- A separate `delivery_acceptance_client` executable and [manual acceptance guide](DELIVERY_ACCEPTANCE.md) are prepared for operator-run success, cancellation, and timeout checks. The client sends two `map` poses, prints its delivery goal ID, stage feedback, cancellation response, and final action status/result; cancellation uses that client's accepted goal handle. Its five isolated client tests cover input/pose handling, cancellation on the held goal handle, feedback before goal acceptance, delayed stage cancellation, and result display. The client has now been exercised against Gazebo/Nav2 for B1～B5.
- With the acceptance-client tests added, the current package suite reports 23 passed, one skipped, and zero failures. The installed package exposes both `delivery_task_server` and `delivery_acceptance_client`; `delivery_acceptance_client --help` was checked without sending a goal.

### Acceptance boundary

The single-goal Nav2 run, the original successful two-stop delivery run, and the updated task node's B1～B5 success/cancellation/timeout runs are accepted. B6 has independent positive stopped-state evidence for success, cancellation, and the two timeout reproductions, subject to the unresolved original timeout anomaly above. Runtime pickup-failure abort remains unverified but is outside V0.1 and belongs to a later stage. Task-level retry is not implemented; the B1 Nav2 recovery is not evidence of such a retry. Delivery action termination and the controller's “Stopping the robot” log alone do not establish a stopped chassis; the B6 conclusion comes from separate odom, model and wheel observations. Navigation obstacle avoidance and replanning comparisons, and any custom planner comparison, remain later work.

## Navigation troubleshooting

See [Navigation troubleshooting notes](NAVIGATION_TROUBLESHOOTING.md) for checks covering map delivery/QoS, AMCL initialization and TF, Nav2 lifecycle/action availability, costmap parameters, velocity command QoS, and startup laser-message filters.

## V0.1 closure and later follow-up

The V0.1 repository baseline is backed up on `origin/master`. Runtime logs, bags, offline analyses and the original/final B7 videos remain outside this repository and are not included in that GitHub backup. This stage's 100 points represent delivery progress, not the percentage of ROS knowledge mastered.

If the original timeout bag's sustained odom yaw reproduces, retain Gazebo model pose, wheel feedback and controller command reception evidence to determine its source. Do not treat the two normal timeout reproductions as a root-cause fix or assume that an action terminal state means immediate stopping.

Pickup-failure fault injection, retry handling, navigation obstacle avoidance/replanning scenarios, and custom planner comparisons remain outside V0.1.
