#!/usr/bin/env bash
# Marv AUV tmux layout (inspired by Inspiration Robotics tmuxSetup.bash).
# Usage: ./scripts/tmux_marv.bash [bench|sim|competition]

set -euo pipefail

MODE="${1:-bench}"
WS="${HOME}/marv_ws"

if [[ ! -d "${WS}/install" ]]; then
  echo "Workspace not built. Run: cd ${WS} && colcon build"
  exit 1
fi

SETUP="source /opt/ros/humble/setup.bash && source ${WS}/install/setup.bash"

tmux new-session -d -s marv -n stack "${SETUP} && ros2 launch marv_bringup marv_bringup.launch.py"

case "${MODE}" in
  sim)
    tmux kill-session -t marv 2>/dev/null || true
    tmux new-session -d -s marv -n sim \
      "${SETUP} && ros2 launch marv_bringup sim_bringup.launch.py"
  ;;
  competition)
    tmux kill-session -t marv 2>/dev/null || true
    tmux new-session -d -s marv -n competition \
      "${SETUP} && ros2 launch marv_bringup competition_bringup.launch.py enable_control:=true"
  ;;
esac

tmux new-window -t marv -n monitor \
  "${SETUP} && ros2 topic echo /mission_planner/status"
tmux new-window -t marv -n topics \
  "${SETUP} && ros2 topic list"
tmux new-window -t marv -n shell \
  "${SETUP} && bash"

tmux select-window -t marv:stack 2>/dev/null || tmux select-window -t marv:0
tmux attach -t marv
