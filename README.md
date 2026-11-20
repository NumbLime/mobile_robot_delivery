# Indoor Delivery AMR

ROS 2 Humble 与 Gazebo Classic 中的室内差速配送机器人项目。

## Packages

- `delivery_robot_description`: 差速底盘、激光雷达和 Gazebo 控制接口。
- `delivery_robot_bringup`: 仿真、建图、静态地图定位和 Nav2 导航启动配置。
- `delivery_task_interfaces`: 取货点与送达点任务的 ROS action 接口。
- `delivery_task_manager`: 顺序调用 Nav2 的取货、送达任务节点；两站成功、分段取消和超时已在 Gazebo/Nav2 中运行验收，独立停车证据及限制见项目状态文档。

项目展示入口：[系统架构图](docs/SYSTEM_ARCHITECTURE.md)、[限定场景测试报告](docs/TEST_REPORT.md)、[个人贡献与限制说明](docs/CONTRIBUTION_AND_LIMITS.md)。三份文档区分现行配置、既有运行证据和贡献归属。

## Build

```bash
source /opt/ros/humble/setup.bash
cd ~/mobile_robot_delivery
colcon build
source install/setup.bash
```

## Bringup modes

Build a map:

```bash
ros2 launch delivery_robot_bringup mapping.launch.py
```

Localize on the saved map:

```bash
ros2 launch delivery_robot_bringup localization.launch.py
```

Start the robot with static-map localization and Nav2 single-goal navigation:

```bash
ros2 launch delivery_robot_bringup navigation.launch.py
```

The navigation RViz profile provides an initial-pose tool and a Nav2 goal tool. Set the AMCL initial pose before sending a goal. The default saved map is `maps/delivery_world.yaml`; the map, spawn pose, Gazebo GUI, and RViz can be overridden through launch arguments. Keyboard teleoperation remains a separate terminal workflow.

Once navigation and AMCL are ready, start the delivery task server in another terminal:

```bash
ros2 launch delivery_task_manager task_manager.launch.py
```

This launch starts only the task server. Its `leg_timeout_sec` argument defaults to `120.0` seconds per navigation leg; for example, `ros2 launch delivery_task_manager task_manager.launch.py leg_timeout_sec:=30.0`. The timeout uses a steady clock, requests Nav2 goal cancellation, and waits for Nav2 to finish before the delivery action returns. See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for result semantics, validation status, and manual checks.

For operator-run success, cancellation, and timeout checks, use the separate `delivery_acceptance_client` executable and follow [docs/DELIVERY_ACCEPTANCE.md](docs/DELIVERY_ACCEPTANCE.md). The client is a test tool; it does not start Gazebo/Nav2 or change the task server's navigation logic.

## 演示视频

- [V0.1 两站配送成片](media/B7_two_stop_delivery_demo_final_2026-10-21.webm)：约 63 秒，展示取货与送达顺序。
- [V0.2 临时障碍配送成片](media/C8_temporary_obstacle_two_stop_demo_final.webm)：约 110 秒，展示箱体出现、扫描/代价/路径变化和两站结果。

[视频来源、校验值与限制](media/README.md)说明成片和原片的区别。V0.3 的障碍移除恢复为无运动固定规划对照，仅有[离线图表](docs/V0.3_D7_EVIDENCE_PRESENTATION.md)，没有新增现场录像。

## V0.2 临时障碍演示

当前导航配置在全局 costmap 中依次使用静态层、订阅 `/scan` 的障碍层和膨胀层（半径 `0.55 m`）；局部 costmap 仍使用自己的 `/scan` 障碍层和 `0.40 m` 膨胀半径。V0.2 在固定起终点规划对照中观察到箱体加入后路径南绕；单次配送中又核对了扫描、两张代价地图、全局路径和实际运动时序。独立的一轮 Gazebo 模型姿态与箱体接触记录支持该轮两站无碰撞送达。具体证据和适用边界见 [项目状态](docs/PROJECT_STATUS.md)。

仓库外的 `~/mobile_robot_delivery_acceptance_logs/` 是**本机原始证据索引**，不是 GitHub 可直接打开的链接。其中 C8 原片为 `C8_2026-10-28/run_001/raw_capture.webm`（92.170 秒）；两段展示成片现收录于 [`media/`](media/README.md)。C5/C6 的 bag、离线报告、临时 world、运行日志仍在仓库外，未随本仓库备份。

已知风险仍需后续排查：早期超时运行约 `0.15 rad` 的持续同向 odom 偏航来源未查明；C6 运行删除箱体后，全局 costmap 原箱体区域的高代价持续到 bag 结束。任务 action 返回不表示车体立即静止，单次激光扫描也不代表看见箱体全部边界。

## V0.3 障碍移除与导航恢复

V0.3 在临时箱体的固定起终点规划场景中，已完成两次独立运行的地图标记、绕行、移除和恢复验收；阶段计 **100/100**，不改变 V0.1、V0.2 各 100/100 的历史结论。验收标签为**按已记录操作者操作，无主动清图的自动恢复**，但无法排除其他客户端调用清图服务；历史 C6 残留和早期 odom 偏航仍未解。固定判据、各轮差异、操作方法与原始证据索引见 [V0.3 交付页](docs/V0.3_DELIVERY.md)和[项目状态](docs/PROJECT_STATUS.md)。V0.3 原始 bag、JSONL 与运行日志在仓库外，不随本仓库 GitHub 备份；仓库内保存审计、脚本和离线图表。
