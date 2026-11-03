#!/usr/bin/env bash
# Read-only checks first; create a fresh evidence directory only after they pass.
set -Eeo pipefail
source /opt/ros/humble/setup.bash || { echo 'STOP: ROS 2 环境加载失败'; exit 1; }
source "$HOME/mobile_robot_delivery/install/setup.bash" || { echo 'STOP: 项目工作区环境加载失败'; exit 1; }
cd "$HOME/mobile_robot_delivery" || { echo 'STOP: 项目目录不存在'; exit 1; }
set -u

for tool in ros2 gz lsof python3 timeout sha256sum rg seq find awk ps tee cmp git sort tr; do
  command -v "$tool" >/dev/null || { echo "STOP: 缺少工具 $tool"; exit 1; }
done
python3 - <<'PY' || { echo 'STOP: ROS Python/SQLite 依赖不可用'; exit 1; }
import sqlite3, rosbag2_py, rclpy, tf2_ros
from nav_msgs.msg import OccupancyGrid
from gazebo_msgs.srv import SpawnEntity, DeleteEntity, GetModelList
print('Python SQLite, rosbag2_py, rclpy, tf2_ros, nav_msgs, gazebo_msgs: PASS')
PY

acceptance_root="$HOME/mobile_robot_delivery_acceptance_logs"
test -d "$acceptance_root" || { echo "STOP: 验收根目录不存在: $acceptance_root"; exit 1; }
test -f "$acceptance_root/C3_delivery_recheck_2026-10-26/temporary_box.sdf" || {
  echo 'STOP: 冻结箱体 SDF 不存在'; exit 1;
}
test -f "$acceptance_root/D3-c_2026-11-02_run_002/plan_sampler.py" || {
  echo 'STOP: 已验收采样器源码不存在'; exit 1;
}
installed_share="$(ros2 pkg prefix delivery_robot_bringup)/share/delivery_robot_bringup"
for relative in launch/navigation.launch.py launch/mapping.launch.py config/navigation.yaml worlds/delivery_room.world; do
  cmp -s "src/delivery_robot_bringup/$relative" "$installed_share/$relative" || {
    echo "STOP: src/install 文件不一致: $relative"; exit 1;
  }
done
expected_sampler_sha='044e8e60924137d65d2c953e7a623e6eca32fffd62f0e48fe66f33a920ce8ce1'
actual_sampler_sha="$(sha256sum "$acceptance_root/D3-c_2026-11-02_run_002/plan_sampler.py" | awk '{print $1}')"
test "$actual_sampler_sha" = "$expected_sampler_sha" || {
  echo "STOP: 采样器 SHA-256 与历史核对值不同: $actual_sampler_sha"; exit 1;
}

printf '%s\n' '=== possible running instances ==='
conflicts="$(ps -eo pid=,comm=,args= | awk '
  $2 ~ /^(gzserver|gzclient|rviz2|planner_server|controller_server|amcl|map_server|rosbag2_recorder)$/ ||
  ($2 != "awk" && $0 ~ /ros2 (bag record|launch)/) ||
  ($0 ~ /delivery_task_server/ && $2 != "awk") { print }
')"
printf '%s\n' "$conflicts"
test -z "$conflicts" || { echo 'STOP: 有遗留仿真、Nav2、任务或 recorder 进程'; exit 1; }
nodes="$(ros2 node list)" || { echo 'STOP: ROS graph 查询失败'; exit 1; }
printf 'ROS nodes:\n%s\n' "$nodes"
test -z "$nodes" || { echo 'STOP: ROS graph 仍有节点'; exit 1; }

printf '%s\n' '=== old bag directory handles ==='
errfile="$(mktemp)"
baglist="$(mktemp)"
trap 'rm -f -- "$errfile" "$baglist"' EXIT
find "$acceptance_root" -type d -name bag -print0 > "$baglist" || {
  echo 'STOP: 旧 bag 目录枚举失败'; exit 1;
}
while IFS= read -r -d '' bagdir; do
  : > "$errfile"
  rc=0
  handles="$(lsof -nP +D "$bagdir" 2> "$errfile")" || rc=$?
  if [ "$rc" -gt 1 ] || [ -s "$errfile" ] || [ -n "$handles" ]; then
    printf 'STOP: 旧 bag 目录占用或检查不确定: %s (lsof rc=%s)\n' "$bagdir" "$rc"
    printf '%s\n' "$handles"
    cat "$errfile"
    exit 1
  fi
done < "$baglist"

day="$(date +%F)"
trial=''
for attempt in $(seq -w 1 999); do
  candidate="$acceptance_root/D5_${day}_recovery_run_${attempt}"
  if [ ! -e "$candidate" ]; then trial="$candidate"; break; fi
done
test -n "$trial" || { echo 'STOP: 无可用尝试编号'; exit 1; }
mkdir -- "$trial" || { echo "STOP: 无法创建新目录 $trial"; exit 1; }
mkdir -- "$trial/bag"
cp -- docs/v03_live_costmap.py docs/v03_validate_plans.py docs/v03_compare_paths.py docs/v03_check_bag.py docs/v03_env.sh docs/v03_preflight.sh "$trial/"
cp -- "$acceptance_root/D3-c_2026-11-02_run_002/plan_sampler.py" "$trial/"
sha256sum "$trial"/*.py "$trial"/v03_env.sh "$trial"/v03_preflight.sh > "$trial/helper_sha256.txt"
printf '%s\n' "$trial" > "$trial/selected_path.txt"
printf 'preflight_date=%s\nsource=%s\n' "$day" "$PWD" > "$trial/preflight_summary.txt"
printf 'ros_distro=%s\nros_domain_id=%s\ninstalled_share=%s\ngit_head=%s\n' \
  "${ROS_DISTRO:-}" "${ROS_DOMAIN_ID:-}" "$installed_share" "$(git rev-parse HEAD)" >> "$trial/preflight_summary.txt"
sha256sum src/delivery_robot_bringup/launch/navigation.launch.py \
  src/delivery_robot_bringup/launch/mapping.launch.py \
  src/delivery_robot_bringup/config/navigation.yaml \
  src/delivery_robot_bringup/worlds/delivery_room.world \
  "$acceptance_root/C3_delivery_recheck_2026-10-26/temporary_box.sdf" > "$trial/runtime_input_sha256.txt"
cat > "$trial/run_notes.txt" <<'EOF'
RViz 2D Pose Estimate（机器人实际位置/朝向、设置时间）：
Gazebo/RViz 现场看到的机器人与箱体关系、扫描回波：
人工暂停、取消、清图或其他干预（若无，写无）：
各终端启动/停止顺序及异常：
EOF
printf '\nPASS: preflight, unique evidence directory created\n'
printf 'Copy this exact line into each new operator terminal:\n'
printf "export V03_TRIAL='%s'\n" "$trial"
