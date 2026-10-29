# Project status

## Current stage: V0.2 temporary-obstacle delivery delivered; V0.1 delivered

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
- Global costmap: the current V0.2 configuration uses the static `/map` layer, `/scan` obstacle layer, and inflation layer (`0.55 m` radius); the earlier V0.1 configuration had only static and inflation layers.
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

## V0.2 量化进度基线（2026-10-21 冻结）

**本阶段终点：**临时障碍进入两站配送路线后，代价地图识别、路径调整、无碰撞送达，并有演示与文档备份。沿用现有 Gazebo Classic、静态地图、Nav2 和配送任务流程；本阶段只验证这一临时障碍场景。V0.1 已完成的 **100/100** 保留在上方，V0.2 独立从 **0/100** 起算。**分数表示阶段交付进度，不代表 ROS 知识掌握百分比。**

| 项目 | 分值 | 已得分 | 状态 | 验收依据 / 待取得证据 |
| --- | ---: | ---: | --- | --- |
| C1 当前配置和证据核对 | 10 | 10 | 已完成，文件与既有证据核对 | 已核对源码、安装链接、地图、机器人外廓、代价地图、`/scan`、速度链和 B6 旧风险；结论见下方。运行中的实际参数与话题仍须复查。 |
| C2 临时障碍和两站路线候选 | 10 | 10 | 已完成路线核实；障碍后运行仍待验收 | 2026-10-26 的 `/compute_path_to_pose` 路径文件显示起终点及 `SUCCEEDED`；Gazebo 模型位姿与 TF 配对换算箱体坐标，原路径穿过箱体外廓，静态几何检查存在两侧候选绕行空间；详见下方。未生成箱体，也未验证实际避障。 |
| C3 临时障碍进入场景 | 10 | 10 | 已完成，2026-10-26 单次配送运行验收 | `C3_delivery_recheck_2026-10-26/run_001/`：同一配送 goal 的 `pickup` 反馈后、`dropoff` 反馈前生成箱体；记录位置与时间，bag 中仅见该配送 goal 和顺序执行的两段 Nav2 goal。首次删除响应成功。配送送达段最终失败，不计入 C6。 |
| C4 激光与代价地图识别 | 10 | 10 | 已完成，2026-10-26 run_001 离线核对 | 同期 `/scan` 命中点按 TF 转入 `odom`，对应局部 costmap 栅格生成前后 `0→100`、周边出现递减代价；删除后对应区域及周边清为 `0`。**该次旧运行**的全局 costmap 仅有静态层和膨胀层；详见仓库外 C4 离线报告。 |
| C5 路径调整 | 20 | 20 | 已完成固定对照与单次配送运行核对 | `planning_run_002` 的同起终点对照证明箱体进入全局地图后路径南绕；`delivery_run_001/C5_B_OFFLINE_ANALYSIS.md` 核对同一配送 UUID 下生成、运动中 `/scan` 视角变化、全局/局部代价更新及后续南侧 `/plan`。运行 BT 约 1 Hz 周期规划，支持箱体相关的全局路径选择与持续重算；不能声称每次扫描都造成路线切换或雷达已看全箱体。 |
| C6 两站无碰撞送达 | 10 | 10 | 已完成 2026-10-28 单次运行与独立离线验收 | `C6_2026-10-28/run_001/C6_RUN_001_OFFLINE_ANALYSIS.md`：同一配送及两段 Nav2 目标成功；13,179 组箱体存在时的 Gazebo 真值中，带 padding 的旋转机器人外廓至实际箱体碰撞盒最小约 0.200 m；约 1 kHz 的箱体接触记录覆盖经过时段，261,844 条均无接触对。结果后运动单独核对，不宣称 action 返回瞬间静止或所有未来运行都无碰撞。 |
| C7 结果与风险交叉核对 | 10 | 10 | 已完成，2026-10-28 同轮原始 bag 交叉核对 | C6 `run_001/` 同一 bag：箱体 world 真值、送达 `/plan` 的南侧路线、机器人 Gazebo 轨迹、两段 action 终态及删除时序相符；另记录删除后全局 costmap 原箱体区域仍有高代价的风险。B6 旧超时 odom 偏航仍未解，详见下方 C7 记录。 |
| C8 演示 | 10 | 10 | 已完成，2026-10-28 同轮真实画面与成片核对 | 仓库外 `C8_2026-10-28/run_001/`：92.170 秒原片完整保留；110.200 秒成片的片头/片尾显著标明编辑说明，真实录屏可见箱体出现、RViz 激光/代价/路径、机器人运动及客户端 pickup→dropoff→SUCCEEDED。同期 bag 核对 `/scan`、全局地图标记、南侧 `/plan` 和同一配送终态；见 `C8_DEMO_VALIDATION.md`。 |
| C9 文档收尾与备份 | 10 | 10 | 已完成，2026-10-29 文档与仓库备份 | README、状态文档及现有验收/排障文档与实现和证据边界核对一致；仓库内 V0.2 配置与文档提交推送到现有 `origin/master`。仓库外 bag、录像、分析报告及临时 world 不在 GitHub 备份内。 |
| **合计** | **100** | **100** | **C1～C9 完成** | V0.2 本阶段交付完成；未解风险保留供后续排查，不把阶段进度当作 ROS 知识掌握比例。 |

| 固定状态字段 | 当前记录 |
| --- | --- |
| 本阶段终点 | V0.2 临时障碍进入两站配送路线后，代价地图识别、路径调整、无碰撞送达，并有演示与文档备份。 |
| 阶段进度 | **100/100**；C1～C9 已完成，V0.1 的 **100/100** 结论不变。**100 分只表示 V0.2 阶段交付完成，不代表 ROS 知识掌握 100%，也不表示所有风险已修复。** |
| 今日计划与进度 | **2026-10-29 本次已得/计划 10/10**：只完成 C9 文档、交付核对与 GitHub 备份；2026-10-28 的 C6～C8 已得 30/30 是此前记录，不重复计分。今日完成后停止，不进入新阶段。 |
| 本次完成项及证据 | README 与本状态文档核对当前全局 `/scan` 障碍层、0.55 m 膨胀和 C5～C8 的运行/离线结论；验收指南与排障文档仍对应各自既有范围。仓库内保留 ROS 包、launch、配置、地图及文档并备份到现有 `origin/master`；仓库外 C5 固定路径与动态配送 bag/报告、C6 同轮真值与接触 bag/报告、C8 **92.170 秒原片**与 **110.200 秒成片**仅作为本机证据索引，均**未纳入 GitHub 备份**。本轮只做文件、配置、构建与 Git 核对，没有新增 Gazebo 运行或操作者目视证据；既有实测与离线证据详见 C5～C8 各节。 |
| 未解风险和后续清单 | B6 旧超时 bag 的约 **0.15 rad** 持续同向 odom 偏航来源未查明；C6 删除箱体后全局 costmap 原箱体区域高代价持续至 bag 结束，清除原因和最终消退时间未确认。后续分别补录 Gazebo 真值/轮反馈/控制器命令接收，以及复核障碍层清除与静态层叠加；按新任务另行安排。不得把 action 返回视为立即停车，也不能假定 `/scan` 看见完整箱体。 |
| 预计剩余学习次数及完成时间 | V0.2 于 **2026-10-29** 完成本阶段交付，计分项剩余 **0 次**；未解风险属于后续独立任务，暂无承诺完成时间。 |

### C1：当前配置和既有证据（文件核对）

- `maps/delivery_world.yaml` 指向 `delivery_world.pgm`，分辨率 `0.05 m/格`，原点 `(-2.93, -2.95, 0)`；PGM 为 `117×118` 格。`delivery_room.world` 的房间墙中心约在 `x/y=±3 m`，中隔墙在 `y=0` 留 `x=-0.6～0.6 m` 的 1.2 m 缺口；现有南侧障碍位于 `(-1.5,-1.2)`，另有北侧两处固定障碍。安装目录中的 navigation、控制器、地图和 world 文件均为指向当前源码/地图的符号链接，内容哈希一致；这只确认当前磁盘文件，不代替运行参数查询。
- Xacro 车体长 `0.40 m`、宽 `0.30 m`，轮距 `0.34 m`、轮宽 `0.04 m`，轮外缘约宽 `0.38 m`；Nav2 全局与局部代价地图均设置 `0.40×0.38 m` 四角 footprint、`0.02 m` padding、`0.05 m` 分辨率、`0.40 m` 膨胀半径。**C1 核实时**全局地图在 `map` 坐标系使用 `/map` 静态层和膨胀层，没有激光障碍层；局部地图在 `odom` 坐标系使用 `/scan` 的 `LaserScan` marking/clearing 障碍层与膨胀层，窗口 `3×3 m`，障碍标记范围至 `2.5 m`。Xacro 激光 frame 为 `laser_link`，Gazebo 射线插件输出 `scan`。
- `navigation.launch.py` 使用静态地图定位和 `use_sim_time=true`；控制器/行为节点的速度经 `/cmd_vel_nav → velocity_smoother → /diff_drive_controller/cmd_vel_unstamped → diff_drive_controller`。控制器设置 `use_stamped_vel=false`、`open_loop=false`、位置反馈、`cmd_vel_timeout=0.5 s`；smoother 为 `OPEN_LOOP`，`velocity_timeout=0.6 s`。V0.1 运行证据曾确认速度话题发布者与订阅者及运动中的非零 Twist，但本次未查询运行端点。
- **C1 核实时待核实：**实际加载参数、TF 与地图对齐、障碍是否被 `/scan` 看到、局部代价地图变化、全局规划或局部轨迹如何调整，以及是否无碰撞。静态全局层不会直接把新出现的障碍写入 `/map`；如需证明全局重规划，后续须先确认并按实际需要配置动态障碍来源。C3/C4 后续补齐激光与局部地图证据，C5 后续补了全局障碍层并在无运动规划中验证其识别与路径变化；单次配送实际机制及无碰撞仍待验。B6 最初超时 bag 在结果后 T+12 秒起累计约 `0.15 rad` 的持续同向 odom 偏航，缺少 Gazebo 模型与轮反馈，来源仍未查明；两次未复现不是修复，action 终态也不表示立即停车。

### C2：临时障碍候选（无障碍路线已核实，动态避障待验）

- 候选取货点 `map (1.4,-1.0)`、送达点 `map (-0.2,-1.8)`；临时箱体候选中心仍为 **Gazebo world `(0.6,-1.4)`**，水平尺寸 `0.35×0.35 m`、高 `0.50 m`，底面落地（中心 `z=0.25 m`）。**C2 核实时**箱体尚未生成；高度覆盖名义约 `0.20 m` 的激光安装高度，但是否实际被扫描到留给 C4。两目标的 map 坐标直线中点恰好也写作 `(0.6,-1.4)`，只是数字相同，**不能据此认为它与箱体 world 中心重合**。
- **规划路径文件与点提取：**`~/mobile_robot_delivery_acceptance_logs/C2_2026-10-26/baseline_path.log` 保存了 `/compute_path_to_pose` 的 goal、完整 `map` 路径和结果，无另造截图。请求明确设置 `use_start=true`、起点 `map (1.4,-1.0)`、终点 `map (-0.2,-1.8)`；goal ID `7a0a757133fc4b0fbdd5473c5139efaa`，最终 `SUCCEEDED`。从结果的 `path.poses[].pose.position` 提取 **72 点**，首点 `(1.4200,-1.0000)`（地图栅格量化后与请求起点相差 `0.020 m`）、末点 `(-0.2000,-1.8000)`；逐段欧氏长度之和约 `1.820 m`。该 action 只计算路径，不是实际行驶或配送验收。
- **world→map 换算：**当前 ROS 话题清单无 `/gazebo/model_states`，Gazebo ROS 服务清单有 `/get_model_list` 但无模型位姿查询服务；改用 Gazebo Classic 的只读 `gz model -m delivery_robot -p`，与近时刻 `map→base_footprint` TF 配对。按平面刚体关系 `p_map = R(θ) p_world + t`，由同一机器人位姿求 `θ = yaw_map - yaw_world`、`t = p_map - R(θ)p_world`。一组原始配对为 world 机器人 `(-0.123119,0.007909,0.077680 rad)`、map 机器人 `(-0.105867,-0.030536,-0.038547 rad)`；8 组配对的 `t_x=0.0155～0.0160 m`、`t_y=-0.0528～-0.0526 m`、`θ=-0.1168～-0.1160 rad`（约 `-6.7°`）。据此 world `(0.6,-1.4)` 映到 **map 约 `(0.449,-1.513)`**，箱体在 map 中也旋转约 `-0.116 rad`。配对期间 Gazebo 模型平面位置仅缓慢变化约 `0.6 mm`，TF 的平面位置变化约 `0.1 mm`；Gazebo 命令无消息时间戳，TF 更新时间也有间隔，因此这是运行中的近时刻对齐估计，不是发布的 `world→map` TF。实际放置前仍须重新核对。
- **阻断与绕行的几何检查：**对 72 个路径点计算 `d_i=‖p_i-(0.449,-1.513)‖`，最小点距 **`0.0667 m`**（第 45 点，按 1 起编号，约 `(0.4199,-1.4530)`）；再投影到每个相邻点线段，最小线段距同为 **`0.0667 m`**。把该最近投影点逆旋转到箱体局部坐标约 `(-0.038,0.055) m`，两个绝对值均小于箱体半边长 `0.175 m`，说明**原路径中心线穿过候选箱体平面外廓**；机器人 `0.40×0.38 m` footprint 与 `0.02 m` padding 只会增加碰撞范围。为检查旁路，将保存的 `0.05 m` PGM 中占用或未知栅格视为不可通行，机器人带 padding 的半对角线约 `0.304 m`；取更保守的 `0.40 m` 膨胀半径作为禁行距离（**不与 `0.304 m` 相加**），静态栅格中心距离再留约 `0.035 m` 半格对角线，对旋转后的箱体矩形也按 `0.40 m` 排除。8 邻接、禁止斜穿障碍角的静态栅格搜索仍找到两侧候选通路：北侧经约 `(0.111,-0.881)` 长约 `2.44 m`，南侧经约 `(0.772,-2.115)` 长约 `2.50 m`；两点到最近静态占用/未知栅格中心约 `0.97/0.75 m`，到箱体外廓约 `0.475/0.442 m`。这些是**保守几何连通性**数值，不是 Nav2 已规划的绕障路径；实际 footprint 随朝向变化，膨胀层是代价而非绝对禁行，map/world 配对及定位会有误差。
- **运行边界与放置时机：**先保存无临时障碍的两段路径；以后另一次两站配送运行中，在 `pickup` 阶段、机器人尚未前往 `dropoff` 时加入箱体，使其落在已核实的送达段原路径上。**C2 核实时**没有生成箱体或发送配送/速度命令；当时全局代价地图只有静态层与膨胀层，局部代价地图才使用 `/scan`。箱体出现后是否被激光/代价地图识别、Nav2 是否调整全局路径或局部轨迹、两站能否无碰撞送达，都须在 C3～C7 分别取得运行证据。不能把此次无障碍规划成功和几何绕行空间写成动态避障已通过。

### C3：首次箱体证据核对（2026-10-26，旧试验未通过）

- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C3_2026-10-26/` 保存 `temporary_box.sdf`、生成/位姿/删除日志、三帧扫描及本轮填写的 `run_notes.txt`。SDF 定义 `c3_temporary_box`、`static=true`，visual 与 collision 均为 `0.35×0.35×0.50 m`。`spawn.log` 报告生成成功；之后的 `box_world_pose.log` 记录 world `(0.6,-1.4,0.25)`、yaw 约 0。机器人生成前后 world 平面位置只差约 `0.0064 m`、yaw 差约 `0.0076 rad`，生成后机器人中心到箱体外廓约 `1.305 m`；用户报告 Gazebo 画面中二者可见且分离。
- 三份 `laser_link` 扫描的 `angle_min=-3.141590 rad`、`angle_increment=0.017502 rad`。按生成后的机器人位姿、激光固定关节与箱体四角推算，箱体覆盖约第 **105～122** 束，中心方向约 `-1.165 rad`（第 113 束），朝机器人一侧的预测量程约 `1.335 m`。已展开的第 105～121 束在生成前约 `3.036～3.431 m`、生成后约 `1.305～1.622 m`、较晚第三帧约 `3.068～3.504 m`；第 113 束依次为 `3.190、1.342、3.239 m`。集中变化的方向和距离与箱体相符，用户亦报告 RViz 回波出现及后来消失。三帧各只有前 128 束被 `ros2 topic echo` 文本展开，且扫描间隔较长、缺少第三帧同期机器人位姿；原有墙体和其他变化不能完全排除，不能从任意单束差值推断因果。
- 用户补充：首次将 `/delete_entity` 调用的输出经 `tee` 保存，紧接着执行单帧 `/scan` 采集时终端卡住；在 Gazebo 看见实体已消失后中断，再将两条命令分开重跑。重跑的 `tee` 与扫描输出重定向会覆盖原文件。现存 `delete.log` 的请求名称是 `c3_temporary_box`，响应 **`success=False`、`Entity [c3_temporary_box] does not exist`**，属于**实体已消失后的重试**；不能拿它反证首次删除成功，也不能改写为首次 `success=True`。第三帧及用户画面支持箱体后来不见和对应回波消失，但首次服务响应与精确移除时刻未保留。本目录没有同期配送目标/阶段/终态记录；用户说明本次未发送导航或配送目标，但缺少目标日志本身不能独立证明没有发送。冻结的 C3 验收条件要求在单次配送中加入障碍并留存不干扰其他目标的证据，**该次旧试验**无法满足，当时保持 **C3 0/10、V0.2 20/100**；后续补验结论见下。

### C3：单次配送中加入箱体（2026-10-26，10/10）

- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C3_delivery_recheck_2026-10-26/run_001/` 的 `client.log`、`spawn_gate.log`、`bag/`、模型/扫描/删除日志，以及新整理的 `run_notes.txt`、`C3_RUN_001_OFFLINE_REVIEW.md` 构成本轮证据。bag 接收 Unix 时间 **1793012726.753～1793013207.872**，录制 481.118 秒，包含配送 feedback/status、Nav2 status、`/clock`、`/scan`、`/tf`、odom、局部 costmap 与路径。bag 只见配送 UUID `3afe560e-69ae-431c-9150-6fcaaf83d912`；其 status 先为 EXECUTING(2)，最终 ABORTED(6)。Nav2 status 只见顺序执行的取货成功和送达失败两 UUID；用户报告只发送这一单，未另点 Nav2 Goal 或发速度命令。bag 无法证明录制窗口外绝无其他目标。
- 客户端于 Unix **1793012825.715** 收到该 UUID 的 `pickup` 反馈；`spawn_gate.log` 于 **2826.347** 以同一 UUID 发出唯一 `SPAWN_REQUEST`，**2826.463** 收到 `success=True`，**2827.192** 读到箱体 world `(0.6,-1.4,0.25)`；客户端直到 **2839.824** 才收到 `dropoff` 反馈，最终于 **3011.495** 返回 `ABORTED (6)`、`success=False`、`failed_stage='dropoff'`、`Nav2 goal finished with status 6`。生成时配送尚在执行，机器人 world `(-0.032084,0.004858)`、至箱体外廓 **1.312 m**；本轮 world/map 对齐估计箱体 map `(0.572488,-1.437611)`、至 C2 基线路径 **0.058 m**。用户现场观察机器人尚未经过箱体区域、二者分离。上述 Unix 时间与脚本记录的 `/clock` 仿真时间、扫描 header 时间分开解释，详见离线报告。
- 模型表生成前无箱体、生成后及删除前有箱体；首次 `/delete_entity` 于 Unix **3130.785～3131.751** 返回 `success=True`、命令退出码 0，无重试日志，删除后模型表无箱体。删除前后的首次 `/get_model_list` 查询曾卡住并中断，现存模型表文件是重查结果，不能混同首次删除响应。bag 扫描在生成后符合箱体方向和约 1.3 m 量程，删除附近对应方向束由约 **0.299 m** 转为约 **2.277 m**；用户亦报告 Gazebo 箱体与 RViz 对应回波出现又消失。出现与删除的精确物理时刻分别由服务响应、后续模型/扫描夹定；未录 `/gazebo/model_states`。`cancel_goal.log` 仅有无效占位 UUID 的参数解析错误，不是有效取消请求。
- **计分边界：**本轮只证明 C3 的单次配送生成时机、位置和目标隔离；送达 Nav2 目标失败，配送不是 `CANCELED` 或 `timed out`，更不是无碰撞送达成功。C4 的局部代价地图识别、C5 的路径调整、C6 的无碰撞送达及停车仍须独立验收；用户观察未见碰撞不能替代 Gazebo/轨迹证据。旧 B6 偏航风险未解决。

### C4：激光与局部代价地图离线核对（2026-10-26，10/10）

- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C3_delivery_recheck_2026-10-26/run_001/C4_RUN_001_OFFLINE_ANALYSIS.md` 记录从同一份 bag 用 `rosbag2_py` 离线反序列化的窗口、时间对齐、TF、滚动地图 origin、栅格索引和原始值。有效窗口含生成前 13 帧扫描/4 张局部地图、生成后箱体存在时 33 帧扫描/10 张地图、删除前 28 帧扫描/8 张地图、删除后 70 帧扫描/21 张地图；`/clock` 同期持续推进。`/scan` 为 `laser_link`，局部地图为 `odom`、60×60 格、约 0.05 m/格。bag 的静态 TF 显示激光相对底盘无平面偏置；扫描附近的 `odom→base_footprint` TF 与扫描 stamp 差约 0.007 s（生成）和 0.003 s（删除）。
- 生成后扫描 Unix **1793012826.693630** 的第 115 束为 `-1.128872 rad`、`1.307288 m`，变换后命中点 `odom (0.391481,-1.258065)`；生成前地图 Unix **2826.187682** 的 origin `(-1.50,-1.45)`，该点索引 (37,3) 值 **0**，生成后首张地图 **2826.562458** 同索引为 **100**。同一张生成后地图中，沿箱体外侧相邻区域值从 **99** 递减到 **74、55**；滚动 origin 在下一时刻改变时，重新换算该点索引而非沿用 (37,3)。删除前扫描 Unix **3130.718446** 的第 180 束约 `0.299384 m`，命中点 `odom (0.585314,-1.251029)`；删除前地图 origin `(-0.65,-2.90)`、索引 (24,32) 为 **100**，删除后该束为 **2.277 m**，对应地图格及周边膨胀代价清为 **0**。结合 C3 的模型位姿、首次删除响应和模型列表，支持箱体被激光及局部 costmap 识别并在移除后清除。
- **run_001 当时** `navigation.yaml` 的局部 costmap 为 `/scan` 障碍层加膨胀层，全局 costmap 为静态层加膨胀层，没有全局动态激光障碍层；本 bag 未录全局地图或运行时全局参数，不能由 C4 推断全局 costmap 已识别箱体。送达段第一条明确控制错误在 Unix **1793012854.605606**：`No valid trajectories out of 314!`，随后 `Controller patience exceeded`、清图及多次 spin/backup/wait 恢复；后期重复 `Failed to make progress`，最终 BT navigator 于 **3011.467568** 报 `Goal failed`，客户端于 **3011.495** 返回配送 `ABORTED`。spin 的 `Collision Ahead` 为恢复行为的碰撞预测，非实际碰撞证明。日志未给出轨迹全部被拒的具体原因，故障排查不加 C5 分，也不把配送 ABORTED 解释成碰撞或单段超时。

### C5：全局障碍层与实测准备（2026-10-26，仍为 0/20）

- 冻结条件仍为同起终点的障碍前后路径比较、将变化归因于箱体，并记录局部避障或全局重规划机制。run_001 的 `/plan` 共有 159 条有效 `map` 路径，取货段生成前 1 条、生成后 13 条，送达段 145 条；首条送达路径 Unix **1793012839.828** 从约 `(1.27,-0.90)` 到 `(-0.2,-1.8)`、约 1.734 m，末条 **3010.648** 从约 `(0.92,-1.30)` 到相同终点、约 1.240 m。按 C3 生成时估计的箱体 map 中心 `(0.572488,-1.437611)` 逐段投影，首条距中心约 0.120 m，送达段最小距离范围约 0.004～0.120 m，说明旧全局路径反复靠近**名义**箱体区域。移动起点和 AMCL map/world 对齐变化、缺 `/global_costmap/costmap`，使这些旧路径不能构成同起终点的因果对照；控制器 `No valid trajectories` 也不能代替规划证据。
- 源码 `navigation.yaml` 的 `global_costmap.global_costmap.ros__parameters.plugins` 现为 `[static_layer, obstacle_layer, inflation_layer]`；新层与已运行验证的局部 `ObstacleLayer` 使用同样的 `/scan`、`LaserScan`、marking/clearing、障碍高度及量程。`map` frame、footprint/padding、2 Hz 更新、1 Hz 发布、静态地图和 Navfn planner 参数未改。`navigation.launch.py` 默认参数指向安装的本文件，`mapping.launch.py` 传给 planner_server；src/install 为同一符号链接目标且 SHA256 一致。`colcon build --packages-select delivery_robot_bringup --symlink-install` 通过，YAML 层级/插件名、`--show-args`、本机默认 BT XML 解析与 `git diff --check` 静态检查通过。**这些是当时的静态检查；后来的全局障碍层无运动运行证据见 C5-A 两轮对照，不能视为配送运动验收。**
- 本机安装的默认 NavigateToPose BT XML 包含 1 Hz `RateController → ComputePathToPose → FollowPath`；本项目任务节点只设置 Nav2 goal pose，YAML 未另指定 BT，run_001 `/plan` 大约每 1.03 秒更新，支持已有周期规划。现阶段无需修改 BT；单次配送时仍须核查运行参数和新 bag。仓库外 `~/mobile_robot_delivery_acceptance_logs/C5_2026-10-26/C5_PREPARATION_AND_RUN_PLAN.md` 分开设计 `planning_run_001` 的**无运动、同一 map 起终点**规划对照与以后 `delivery_run_001` 的单次配送录制，并要求核对全局地图箱体栅格、路径最小距离/长度/几何差异。原计划先做前者，现已核对见下；B 仍待另行安排。

### C5-A：固定起终点箱体前后规划对照（旧配置及 2026-10-27 新配置均有无运动证据，C5 仍 0/20）

- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C5_2026-10-26/planning_run_001/C5_A_OFFLINE_ANALYSIS.md` 列出全部原始文件、缺口、Unix/bag/仿真时间关系、TF 与 world→map 换算、全局地图栅格及逐段路径几何。bag 覆盖两次规划、生成、首次删除及删除后窗口，含 `/clock` 4,561、`/scan` 4,561、`/tf` 54,782、全局 costmap 305、`/plan` 2 和规划 action status 4 条。运行时全局插件为 `[static_layer, obstacle_layer, inflation_layer]`，`/scan` 参数确认为 `/scan`，planner 为 active、action server 1 个。`spawn.log` 报成功、实体 world `(0.6,-1.4,0.25)`；首次删除响应 `success=True`、退出码 0，删除后模型表无箱体，没有重试文件。
- 两份请求打印内容相同：`use_start=true`、`planner_id=''`，map 起点 `(1.4,-1.0)`、终点 `(-0.2,-1.8)`；均 `SUCCEEDED` 且退出码 0。返回首点均为 `(1.42,-1.0)`，距请求起点约 0.020 m；末点均为 `(-0.2,-1.8)`。第一条 72 点、1.820225 m，第二条 88 点、2.224220 m，增加约 0.404 m。按本轮近时刻 Gazebo 机器人 world 位姿及 map/odom TF，箱体中心约为 map `(0.54,-1.42)`、平面旋转约 -0.03 rad；逐段计算旧路径到旋转箱体外廓为 **0、穿越**，新路径最小外廓距离约 **0.21890 m**、改走南侧；x=0.6 m 处路线 y 约由 -1.357 改为 -1.974 m。首点栅格偏差、位姿快照非严格同步及约厘米级估计限制见报告。
- bag 扫描第 113 束约由 3.202 m 变 1.342 m，删除后恢复约 3.238 m；扫描命中点经同期 TF 为 map `(0.472363,-1.247854)`、全局地图栅格 (68,34)，其值在生成前/后/删除后为 **0→100→0**。箱体近侧另一格 (69,33) 同为 0→100→0，中心估计格 (69,30) 为 0→99→0，周边有膨胀代价。箱体附近 403 个变化格在删除后回到初始值；全图其他区域也有扫描变化，不能称全图只有箱体变化。旧路径在后地图的加密采样命中致命/高代价格，新路径的加密采样未命中正代价值。两次规划间 map→odom 数值恒定、odom 最大平面位移约 0.00932 m，world 两快照差约 0.01285 m，远小于路径在箱体处约 0.617 m 的横向差异。模型列表仅增加/删除该箱体；综合证据足以支持 A 的箱体归因，但没有连续 Gazebo 模型状态，不能据此证明实际车体避障或无碰撞。
- **计分边界：**A 的全局地图标记、固定路径几何变化及归因已通过；冻结 C5 仍要求 B 的单次配送实际局部避障或全局重规划机制。未执行 B，C5 暂维持 **0/20**、V0.2 **40/100**、2026-10-26 已验收交付分值 **25/25**；C6 无碰撞送达也未通过。

### C5-A：0.55 m 全局膨胀半径重测（2026-10-27，B 仍暂停）

- 用户现场完成仓库外 `~/mobile_robot_delivery_acceptance_logs/C5_2026-10-26/planning_run_002/`；本轮只离线核对原始日志与 rosbag2，完整方法和数值见 `C5_A_055_OFFLINE_ANALYSIS.md`。运行时全局半径 **0.55 m**、局部 **0.40 m**，插件顺序为静态层、`/scan` 障碍层、膨胀层。bag 覆盖两次 `/compute_path_to_pose`、生成、首次删除及清除；两次同一 map 起终点请求均成功。无箱体路径 **72 点、1.820225 m**；有箱体路径 **95 点、2.543311 m**，在 x=0.6 m 处由 y≈-1.357 m 改为 y≈-2.139 m。箱体 world `(0.6,-1.4,0.25)`；首次删除响应 `success=True`、退出码 0，之后模型列表无箱体。`models_after_spawn.log` 缺失，但生成响应、world 位姿和删除前模型列表支持箱体曾存在。
- 用户指出激光只能看到箱体部分边界。bag 中可见箱体近侧第 105～121 束回波；将实际 SDF 外廓按近时 world/map 配对投到地图，箱体内部 48 个栅格中心仅 5 个为致命值 100，其余为膨胀高代价，**不能**把全局图的致命标记当完整碰撞盒。新路径到真实外廓的中心线最小距离约 **0.344～0.347 m**；以带 padding 的 `0.44×0.42 m` footprint 外接圆半径约 **0.304 m** 作任意朝向保守核算，模型余量仅 **0.040～0.043 m**。沿计划折线切线及连续转角的条件性扫掠最小净空约 0.129 m，但路径姿态全部为零 yaw，不能作为未来车体朝向。静态占用格到新路径最近约 0.613 m，不是本轮最紧约束。两次规划期间 odom 平面变化约 0.014 m，不能写为绝对静止；world/map 的非同步配对、定位、感测与实际跟踪误差缺可靠界限。
- **当时结论：**新配置确实使固定规划路径进一步南绕，生成/删除与 `/scan`、全局地图变化时序一致；但只观测可见表面且保守模型余量约 4 cm，尚不足以证明车体实际可安全通过。旧、新 A 都不能替代单次配送中的路径/局部避障机制和 C6 无碰撞到达。当时保持 **C5 0/20、V0.2 40/100**，未进入 C5-B；后续前置门槛修订见下。

### C5：完整箱体与静态障碍的只读通道核对（2026-10-27，不计分）

- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C5_2026-10-26/C5_FULL_BOX_CORRIDOR_READONLY.md` 及同目录 `c5_corridor_readonly.py` 保留输入、算法和输出。保存地图的 859 个占用格和 528 个未知格均按完整方格视为障碍；使用本轮两组非同步 world→map 估计的**完整** `0.35×0.35 m` 箱体，并用带 padding footprint 的 `0.304 m` 任意朝向外接圆作保守搜索。南侧、北侧各找到额外圆包络净空下界约 **0.10 m** 和 **0.20 m** 的离线候选路径；0.10 m 情形的候选长度约 2.487/2.413 m，在 x=0.6 m 处分别经过 y≈-2.075/-0.825 m。它们不是 Navfn 运行路径，位姿配对差异也不是误差界限；当时 0.55 m Navfn 路径的保守余量仍只有约 4 cm。**几何上有通道，不等于现有规划器、定位与控制能安全走通。**该次只读核对未执行 B，C5 保持 0/20、V0.2 40/100；后续前置门槛修订见下。

### C5：已知完整箱体外廓的隔离 Navfn 诊断（2026-10-27，不计分）

- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C5_2026-10-26/full_box_diagnostic_001/C5_FULL_BOX_INPUT_DIAGNOSTIC.md` 和同目录原始地图、脚本、日志记录了无 Gazebo/RViz/控制器的规划对照。由 `planning_run_002` 箱体周边新增的 12 个致命格重建可见表面输入；完整盒输入保留它们并根据 SDF 外廓补上 52 格。两者保留相同静态地图、Navfn A*、全局膨胀半径 0.55 m、footprint、map 起点 `(1.4,-1.0)` 与终点 `(-0.2,-1.8)`；只发送 `/compute_path_to_pose`，不发送运动目标。
- 有效的可见表面诊断路径与 `planning_run_002` 现场结果 **95 点逐点一致**、长 2.543311 m、走南侧；在独立 ROS 域中核实地图确实加载的完整盒诊断路径为 **109 点、2.742386 m**、改走北侧。相同估计的真实箱体外廓下，中心线最小距离约 **0.347/0.538 m**，减 0.304 m 任意朝向外接圆后的条件性余量约 **0.043/0.234 m**；至静态占用/未知格的余量下界分别约 **0.307/0.279 m**。首次完整盒尝试有旧 planner 残留，日志已明确排除，只有独立域 `_verified` 文件参与比较；所有本轮进程最后已清理。
- **结论边界：**在隔离的同一 Navfn 配置中，补齐已知外廓足以改变规划；冻结的可见表面输入不是现场 `/scan` 完整重放，预知 SDF 轮廓不是机器人独立感知，新的北侧路线没有在正式实时栈或配送中运行，定位与跟踪误差仍未界定。该次诊断未执行 C5-B，保持 **C5 0/20、V0.2 40/100**；后续前置门槛修订见下。

### C5-B：动态感知试验的运行前条件修订（2026-10-27，当时尚未运行）

- 用户指出：机器人静止时，单台激光只观测新增箱体的部分表面；要求**在运动前**从该视角证明完整 SDF 轮廓及全程误差余量，会把 C5 本应观察的“运动中获得新视角、代价地图更新、规划/局部轨迹调整”排除掉。运动可能增加可见表面，**不保证最终看全箱体**；C5 验收应针对实际观测与响应，不把“补全整盒地图”写成必然结果。此前“约 4 cm 余量不足则不许进入 B”是额外的保守试验门槛，**不是冻结的 C5 计分条件**。现移除该硬性门槛，不改变 C5 20 分、V0.2 总分或“单次配送中记录实际局部避障或全局重规划机制”的原文要求。约 4 cm 仍是需重点监护的风险，不是安全证明。
- **运行前必须核实的可执行条件：**只有一套导航仿真和一个任务节点；AMCL/TF、Nav2 生命周期、`/scan` 与全局/局部动态障碍层、规划 action 与控制器状态正常；足够的单段超时；已有客户端能按**本次配送 UUID**请求取消。录制同一配送和 Nav2 goal 的 feedback/status、`/clock`、`/scan`、`/tf`、两张 costmap、`/plan`、局部轨迹、odom、速度命令，以及 Gazebo 真实模型位姿或接触来源（接口须先现场核实，不能假设存在 `/gazebo/model_states`）。明确现场观察者和仿真暂停/停止手段；取消是异步请求，不能把收到取消响应等同于立即停车。
- **分阶段执行和停止：**先在同一单配送中按已核实的时机生成原箱体，确认机器人尚未经过该区域、未重叠，并开始记录新视角的回波与地图/路径时间序列。接近箱体时持续查看真实模型与路径；若 TF/地图失效、路径仍指向已观测障碍、局部控制反复无有效轨迹，或存在迫近碰撞的迹象，提前取消该配送 UUID；必要时按预先核实的方法暂停仿真并留存证据，**不为追求成功强行继续**。若试验中止，仍可根据足够的时序证据独立判断 C5 机制是否出现；不得把中止写成 C6 成功。
- **验收边界：**C5-B 要从同一配送 UUID 证明“机器人位置/扫描视角变化 → `/scan` 命中变化 → 全局或局部 costmap 在同期正确坐标系更新 → `/plan` 的后续路线或局部控制轨迹对该障碍作出可归因调整”；移动起点自然引起的点数/长度变化不算重规划证明，须与固定对照 A、实时栅格及路径空间关系一起分析。C5 可记录机制，即使配送最终失败；C6 仍需两站实际成功及 Gazebo/轨迹无碰撞证据，另查终态后停车。已知 SDF 外廓仅用于离线真值/碰撞核对，**不得**在宣称“仅凭 `/scan` 感知”的试验中偷偷作为规划输入。**本条为运行前记录**；当时未执行 B，分数为 C5 0/20、V0.2 40/100，之后验收见下。

### C5-B：单次配送动态路径机制验收（2026-10-27，C5 20/20）

- 本轮仓库外 `~/mobile_robot_delivery_acceptance_logs/C5_2026-10-26/delivery_run_001/` 的原始 `client.log`、`spawn_gate.log`、节点日志、bag、首次删除响应及离线报告 `C5_B_OFFLINE_ANALYSIS.md` 相互核对。bag 为 Unix **1793102294.054～1793102462.973**、50,691 条；配送 goal UUID `6ee931bb-0f72-44e0-9298-605655deb017` 于 **2332.017** 收到 pickup 反馈，**2332.653～2332.759** 对同一 UUID 请求并成功生成箱体 world `(0.6,-1.4,0.25)`，当时机器人 world `(-0.009848,0.003188)`、距外廓约 1.303 m；**2347.407** 才收到 dropoff 反馈。bag 只见该配送目标和顺序两段 Nav2 目标，二者 UUID 与配送 UUID 不同，均 SUCCEEDED；配送于 **2372.637** 返回 SUCCEEDED。首次删除 `success=True`、退出码 0；目录缺删除后模型列表，但全局地图对应区域清为 0、操作者目视箱体消失。
- `/scan` 随车体运动在箱体邻域出现不同方向和距离的命中；以同期 TF/odom 投影并按每张地图 frame、origin、resolution 计算，箱体附近全局格 `(70,30)` 从 **0→99/100**，删除后回到 **0**；局部滚动地图相应区域也从 0 变为高代价并于删除后清除。`/plan` 约每 1.03 s 发布，本机运行 BT 参数含周期 ComputePathToPose。生成前的首条取货路径目标不同，不能直接与送达路径比较；**送达首条路径**在箱体加入且地图更新后于 Unix **2347.412** 发布，从约 `(1.32,-0.95)` 到 `(-0.2,-1.8)`，在 x=0.6 处 y≈**-2.163**，后续路径持续南绕。固定起终点 C5-A 的有箱体路径 y≈**-2.139**，无箱体路径 y≈**-1.357**。结合箱体生成、扫描/地图变化与固定对照，支持**全局规划使用动态障碍图层选择南侧路线，并在配送中周期重算**；没有证据表明每次新扫描都令路径拓扑切换，也不能仅凭点数变化归因。
- 冻结 C5 的 A 同起终点障碍前后路径对照和 B 单次配送实际机制均有证据，记 **C5 20/20、V0.2 60/100**。本次未测试暂停/恢复；没有取消请求。bag 缺连续 Gazebo 模型姿态与接触/碰撞话题，操作者“从南侧经过、未见擦碰”是现场观察，**不能给 C6 无碰撞送达计分**。配送结果时 odom 仍有非零角速度，不能称立即停车；B6 旧偏航风险保持未解决。完整方法、数值、文件缺口及人工观察边界见仓库外报告和 `run_notes.txt`。

### C6：独立无碰撞验收的接口与操作单准备（2026-10-28，运行前记录）

- 只读核对确认：B6 临时 world 的导航日志曾显示 `gazebo_ros_state` 发布 `/gazebo/model_states` 和 `/gazebo/link_states`，B6 bag 中前者为 `gazebo_msgs/msg/ModelStates`，约 20 Hz；**当前正式 world 不含该插件，本次尚未运行新 world**。本机存在 `libgazebo_ros_state.so`、`libgazebo_ros_bumper.so` 与 `gazebo_msgs/msg/ContactsState`，安装的 bumper 示例把接触传感器挂在已有 collision 上。正式箱体 SDF 不含接触传感器，不能预设新接触话题已存在。
- 仓库外 `~/mobile_robot_delivery_acceptance_logs/C6_2026-10-28/` 保存 `C6_RUN_PLAN.md`、`delivery_room_with_state.world`、`temporary_box_with_contact.sdf`。副本分别只加 50 Hz 状态发布插件、挂在原箱体 collision 的接触传感器及 ROS 插件；XML/差异静态核对通过，原 world physics/模型和箱体 model/static/collision/visual 未变。指定配送 UUID 取消脚本的 `CancelGoal.Request` 16 字节赋值与读回静态检查通过，**未调用取消服务**。导航 `world` launch 参数静态可解析，操作单 shell 命令组经 `bash -n` 检查通过。上述不是 Gazebo 插件运行验收。
- 操作单规定只运行一单：先检旧实例、建全新 `run_001/`、启动一套导航与一个任务节点、设置 AMCL、现场核对状态/接触话题和 GUI 暂停、先录 bag，再以 pickup 反馈触发原尺寸/位置箱体，记录两段 action、Gazebo 真值、接触、TF/扫描/地图/路径/odom/速度；发生危险按真实 UUID 取消或暂停；结果后继续录至少 40 秒仿真时间，再独立记录首次删除。生成后若接触话题或 recorder 订阅缺失，应及早取消，不把缺数据解释为无碰撞。
- 冻结 C6 要求两站顺序成功并有独立真实无碰撞证据。50 Hz 离散 ModelStates **单独不能排除采样间瞬时接触**；接触消息也需核对从箱体生成到机器人经过的连续覆盖、collision 对和时间戳，不能把没有采到消息当作零接触。**本条是运行前状态**：当时现场执行与离线判断尚未发生，C6 为 0/10、V0.2 为 60/100；后续验收结果见下。旧超时 odom 偏航风险仍未解。

### C6：单次两站无碰撞送达验收（2026-10-28）

- 用户按仓库外 `~/mobile_robot_delivery_acceptance_logs/C6_2026-10-28/C6_RUN_PLAN.md` 执行单次实验；`run_001/client.log`、bag 与任务/Nav2 日志确认同一配送 UUID `91b81ad7-b9a7-464f-8c4c-37cd2e5850a9` 依次反馈 pickup、dropoff，两段 Nav2 goal 先后 SUCCEEDED，配送最终 `SUCCEEDED`、`success=True`。箱体 world `(0.6,-1.4,0.25)` 在 pickup 反馈后生成，首次删除响应成功。
- 对箱体存在期间 13,179 组 Gazebo 模型真值，按机器人实际朝向旋转带 `0.02 m` padding 的外廓，至原尺寸箱体碰撞外廓的最小采样净距为 **0.200068 m**；至房间静态碰撞外廓的最小采样净距约 **0.127739 m**。箱体接触传感器在通过时段持续记录 261,844 条消息，全部 `states=[]`。离散真值与接触记录共同支持**本次运行**未碰撞；没有对接触传感器做故意碰撞正控制，不能把结论推广为所有未来运行的保证。
- 结果返回后的头 2 秒，Gazebo 模型仍记录到最大约 **0.16026 rad/s** 角速度和约 **0.02202 rad** 的偏航变化；随后速度衰减，2～40 秒的位置/偏航变化为毫米/毫弧度级，更长时间存在缓慢漂移。不能称 action 返回瞬间静止，也不能把“后续未采到速度命令发布”写成“已发布或收到零速”。B6 旧超时 bag 约 0.15 rad 持续 odom 偏航风险仍未解决。
- 完整时钟对齐、UUID、外廓计算、接触覆盖、结果后运动数值与限制见仓库外 `run_001/C6_RUN_001_OFFLINE_ANALYSIS.md` 和 `run_001/run_notes.txt`。依据本次独立运行证据，**C6 10/10、V0.2 70/100**；今日 C6 清单完成后停止，C7～C9 仍待完成。

### C7：障碍、路径、实际运动及终态的交叉核对（2026-10-28）

- **原始来源与时钟：**本次重新只读解码 `~/mobile_robot_delivery_acceptance_logs/C6_2026-10-28/run_001/bag/`，与同目录 `client.log`、`spawn_gate.log`、`navigation_console.log`、`task_server_console.log`、`delete_first.log`、`models_after_delete.log` 和 C6 离线报告核对；另参照 `C5_2026-10-26/planning_run_002/C5_A_055_OFFLINE_ANALYSIS.md` 的固定对照，以及 `delivery_run_001/C5_B_OFFLINE_ANALYSIS.md` 的前一单动态机制。以下 179315… 数字均为 **Unix bag 接收或客户端墙钟时间**；Path、TF 和 `/clock` 的 423～689 秒为**仿真时间**，两类时间不直接相减。C6 bag 有 `/plan` 45 条、`/gazebo/model_states` 24,285 条、`/tf` 58,256 条、全局 costmap 326 条、`/clock` 4,857 条，以及两种 action status。
- **位置与路线：**配送 UUID `91b81ad7-b9a7-464f-8c4c-37cd2e5850a9` 于 **8985.565** 反馈 pickup；同一 UUID 的箱体请求/成功响应于 **8986.298/8986.403**，模型真值首见于 **8986.417**，world 中固定 `(0.6,-1.4,0.25)`，并非直接作为 map 坐标。取货 Nav2 UUID `57abfdfd-76ac-4754-a17f-9d67d26e01fa` 于 **9001.515** SUCCEEDED，**9001.535** 才反馈 dropoff；送达首条 map `/plan` 于 **9001.540** 发布，起点约 `(1.32,-0.90)`、终点 `(-0.2,-1.8)`、108 点、长约 2.749 m，在 map `x=0.6` 处 `y≈-2.175`，处于箱体南侧。C5 固定起终点无/有箱体对照在该截面分别约 `-1.357/-2.139`，因此 C6 送达路径的南侧形状与已验收的动态全局规划机制一致；不同轮次及起点不能逐点视为同一条路径。
- **实际运动与净距：**C6 Gazebo 模型真值于 **9015.080** 穿过 world `x=0.6`，当时 `y≈-2.252`，确在实际箱体 world `y=-1.4` 南侧；不能把这个 world 数字与 map 路径坐标直接相减。用该时刻附近 `/clock≈453.0 s`，按 **TF 仿真 header 时间**选择 `map→odom`（452.992 s）及 `odom→base_footprint`（452.996 s），配对模型样本后，机器人 map 约 `(0.397,-2.154)`，距接收于 **9014.929** 的近时刻 `/plan` 折线约 **0.004 m**。这是单时刻近同步一致性检查；AMCL 的 `map→odom` 消息接收时带约 1 s 前瞻时间戳，world→map 估计随定位变化，不能由 0.004 m 推得全程跟踪误差上界。C6 真值按实际车体 yaw 和带 padding 外廓复核，箱体最小间距在取货段约 **0.200 m**、送达段约 **0.270 m**；两段都为正，与连续空接触记录及南侧通行相符。Path 姿态均为 0，不代表真实车体朝向。
- **终态与新增风险：**送达 Nav2 UUID `fd41ce39-2b16-40c7-9c23-cd330ec234fc` 于 **9030.899** SUCCEEDED，配送 UUID `91b81ad7-b9a7-464f-8c4c-37cd2e5850a9` 于 **9030.913** 的 bag 状态为 SUCCEEDED，客户端 **9030.915** 收到 `success=True`；两种 action 的 UUID 以任务日志与时序关联，不把它们误认成相同 UUID。首次删除于 **9249.765～9250.626** 响应成功、退出码 0，删除后模型列表无箱体。但全局 costmap `map` frame、origin `(-2.93,-2.95)`、resolution `0.05 m` 的箱体邻域固定格 `(70,30)`（数组索引 `30×117+70`）在生成前 **8985.095** 为 0、生成后 **8986.596** 为 99、删除前 **9249.096** 为 100；模型消失后 **9250.595** 为 99，直到 bag 最后一张 **9273.096** 仍为 99。**实体删除与代价地图完全清除不能画等号**；该残留高代价的具体标记/清除原因及最终消退时间尚未确认，不改写 C4 另一轮的清除结论。
- **判定边界：**障碍真值、南侧规划、真实轨迹、带 padding 外廓和两段终态在本轮相互一致，C7 原定核对条件已满足，计 **10/10**；C6 维持原有 10/10，未重新计分。C7 是证据交叉核对，不是 C8 视频演示，也不是新的避障或碰撞实验。结果后 Gazebo 首 2 秒仍转过约 0.022 rad，不能称即时停车。B6 最初超时 bag 的结果后约 0.15 rad 持续同向 odom 偏航缺模型真值及轮反馈，来源仍未解；本轮成功场景的较小漂移不能当作修复证明。今日完成 C7 后停止，不进入 C8。

### C8：演示素材盘点与现场录制准备（2026-10-28，当时为 0/10）

- 冻结条件为“演示障碍出现、代价地图识别、路径调整与两站送达，真实画面和说明分开标识”。C5-B 与 C6 的 `client.log`、bag、离线报告能支撑说明文字和结果核对，**不能替代该场景画面**。在两轮证据目录及仓库外既有素材清单中未找到 C5-B/C6 Gazebo/RViz 录像或截图；V0.1 B7 的 63.210 s、1920×1080 成片没有本阶段临时箱体，不用于冒充 C8 原片。
- 新一轮只由用户现场执行：在未占用的 `~/mobile_robot_delivery_acceptance_logs/C8_2026-10-28/run_001/` 保存原始桌面录像、独立客户端/导航/任务/生成日志和同期 bag，保持原箱体、两站目标及现行导航参数；先试录验证画面和文件可播放，再启动单套仿真、设置定位、布置 Gazebo/RViz/终端画面、先录再发一单。若出现重复实例、录制失败、生成门槛不符或迫近碰撞，按本单配送 UUID 取消或暂停并保留证据，不重发凑演示。详细逐终端命令与画面清单在本次对话中交给操作者；本轮助手未执行现场命令。
- 成片应保留原片不变，以明确标识的片头/字幕/片尾说明坐标、`/scan→costmap→/plan` 与最终客户端结果；不得改写终端输出、伪造 Gazebo/RViz 帧或把旧 C6/C7 的离线数值伪装成新一单的现场测量。**本条是运行前记录**：当时缺视频，C8 为 0/10、V0.2 为 80/100；随后用户录制与成片验收见下，不进入 C9。

### C8：新一单演示成片验收（2026-10-28，10/10）

- 新目录 `~/mobile_robot_delivery_acceptance_logs/C8_2026-10-28/run_001/` 的 `raw_capture.webm`、`client.log`、`spawn_gate.log`、bag 与成片 `C8_temporary_obstacle_two_stop_demo_final.webm` 属于同一轮。配送 UUID `8ee43818-2ebc-463a-95ea-217f45b4d468` 于 Unix **1793174021.956** 反馈 pickup，**4022.561～4022.656** 对该目标生成 world `(0.6,-1.4,0.25)` 的原箱体，**4038.311** 反馈 dropoff，**4061.828** 客户端返回 `SUCCEEDED (4)`、`success=True`；bag 两段 Nav2 UUID 顺序成功。录像约 30 秒时无临时箱体、40 秒可见箱体及 RViz 地图变化、50～70 秒有机器人与路径、约 73 秒终端最终结果可读。用户已用播放器确认原片从无箱体到终态连续、Gazebo/RViz/终端清楚。
- 同轮 bag 的 `/scan`、全局 costmap 和 `/plan` 支持片中说明：生成前箱体邻域 map 栅格 `(69,30)` 为 0，生成后为 99，送达首条 map 路径在 `x=0.6` 处 `y≈-2.236`，走箱体南侧。画面呈现可见扫描、代价颜色和路径；具体数值是 bag 离线核对，并非只由 RViz 颜色推断。箱体删除发生在原始录像结束之后，不将删除后的画面冒充已录入视频。
- 原片 SHA-256 和成片 SHA-256 见 `demo_checksums.txt`；原片完整保留，**92.170 秒、1920×1080、15 fps**。成片 **110.200 秒**：8 秒说明片头、原片全部 1383 帧按原顺序和原速、10 秒说明片尾；片头片尾均显著写“编辑说明 · 非原始录屏”。成片经 `gst-discoverer-1.0` 解析、OpenCV 全部 1653 帧解码及关键画面抽查，无异常黑帧或裁切；二次 VP8 编码有轻微画质损失，未修改原终端内容。完整方法与局限见 `C8_DEMO_VALIDATION.md`、`run_notes.txt`。
- 冻结演示的障碍出现、激光/代价、南侧路径及两站结果都有同轮画面与日志/bag 证据，记 **C8 10/10、V0.2 90/100**。本片只陈述该次成功，不代表 action 返回瞬间静止，也不表示 B6 旧超时偏航或 C6 旧代价残留已修复。C9 文档收尾与备份仍为 0/10，另行授权后再做；本轮到此停止。

### C9：文档、交付文件与仓库备份（2026-10-29）

- **文档与配置：**README 已补充 V0.2 的现行全局 `/scan` 障碍层与 0.55 m 膨胀半径，以及 C5 固定路径对照/动态机制、C6 独立无碰撞证据和两项未解风险。原有 `DELIVERY_ACCEPTANCE.md` 是 V0.1 取消/超时的重跑操作指南，`NAVIGATION_TROUBLESHOOTING.md` 是既有故障排查记录；它们不被当作 V0.2 新运行报告。本状态文档 C5～C8 各节区分静态检查、bag 离线分析、Gazebo 实测和操作者目视，保留各轮时间顺序与证据限制。
- **仓库与本机证据边界：**GitHub 备份只包含仓库内 ROS 包源码、launch、配置、地图和文档。C5 `planning_run_002/` 与 `delivery_run_001/` 的 bag/离线报告、C6 `run_001/` 的真值/接触 bag 与报告、C8 `run_001/` 的 **92.170 秒**原片和 **110.200 秒**成片、临时 world/SDF 及运行日志仍位于仓库外 `~/mobile_robot_delivery_acceptance_logs/`，这些路径仅供本机检索，**不是其他 GitHub 访问者可直接打开的仓库链接**。原片和成片分别约 39.6 MB、27.9 MB；冻结 C9 要求说明仓库外证据，并未要求将大型视频/bag 上传 GitHub。
- **验证范围：**本次核对源码与 install 导航 YAML 一致、全局层顺序及 `/scan`、0.55 m 半径、局部 0.40 m 半径；检查 Git 差异、忽略规则、待提交清单和仓库外文件存在性。构建/解析与 Git 检查只验证交付文件，不是新的 Gazebo 验收；C5～C8 的运行和离线结论引用对应原始记录，没有重复计分或重跑实验。
- **遗留事项：**B6 最初超时 bag 的持续 odom 偏航约 0.15 rad 无 Gazebo 真值及轮反馈，原因未知；C6 运行删除箱体后，全局 costmap 高代价仍持续至 bag 结束，最终清除时间未知。后续单独排查；本阶段的 100/100 不表示这两项已修复，也不保证所有超时运行停稳。C6 同轮无碰撞结论只适用于该次记录，C8 视频只展示其本轮成功。雷达只看到了当时可见表面，未证明完整箱体边界被扫描。
