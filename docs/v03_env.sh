# Source this from each operator terminal. It does not start any process.
case $- in *u*) v03_had_nounset=1; set +u ;; *) v03_had_nounset=0 ;; esac
source /opt/ros/humble/setup.bash || { echo 'STOP: ROS 2 环境加载失败'; return 1; }
source "$HOME/mobile_robot_delivery/install/setup.bash" || { echo 'STOP: 项目工作区环境加载失败'; return 1; }
cd "$HOME/mobile_robot_delivery" || { echo 'STOP: 项目目录不存在'; return 1; }
if [ "$v03_had_nounset" -eq 1 ]; then set -u; fi
unset v03_had_nounset
test -n "${V03_TRIAL:-}" && test -d "$V03_TRIAL" || {
  echo 'STOP: 先复制预检输出的 export V03_TRIAL=... 到本终端'; return 1;
}
