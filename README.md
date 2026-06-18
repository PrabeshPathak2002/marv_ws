# Marv AUV — ROS 2 Workspace

Modular [ROS 2 Humble](https://docs.ros.org/en/humble/) workspace for the **Marv** autonomous underwater vehicle (AUV). The stack is split into vision, high-level control, and ArduSub hardware interface packages so each subsystem can be developed and tested independently.

**Operating guide:** [INSTRUCTIONS.md](INSTRUCTIONS.md) — bench + MAVROS procedures · [PREQUAL.md](PREQUAL.md) — RoboSub pre-qualification prep

## Prerequisites

- Ubuntu 22.04 (or compatible) with **ROS 2 Humble** installed
- `colcon` and common ROS build tools:

```bash
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions
pip3 install 'numpy<2'   # cv_bridge on Humble is built against NumPy 1.x
```

Source ROS before building or running:

```bash
source /opt/ros/humble/setup.bash
```

## Workspace layout

```
marv_ws/
├── src/
│   ├── marv_vision/     # Front & down cameras, YOLO inference, VSLAM helpers
│   ├── marv_control/    # Master control & mission behaviors
│   ├── marv_ardusub/    # Depth hold, ESC PWM, position estimation
│   └── marv_bringup/    # Launch files
├── build/
├── install/
├── log/
├── README.md
└── INSTRUCTIONS.md
```

A previous workspace may live at `~/ros2_ws_archive` if you migrated from an older `ros2_ws`.

## Packages

| Package | Nodes | Role |
|---------|--------|------|
| **marv_vision** | `f_cam_node`, `d_cam_node` | Camera processing, object detection, detection strings |
| **marv_control** | `master_control_node` | Mission logic: path, gates, gripper, torpedo, return home |
| **marv_ardusub** | `ardusub_node` | Vehicle I/O: thruster PWM, depth hold; **`pos_est` for where-the-sub-is** |
| **marv_bringup** | — | Launch files to start the full stack |

### marv_vision

- **Nodes:** `f_cam_node`, `d_cam_node`
- **Front camera:** Blue Robotics **exploreHD** USB (V4L2 `/dev/video0`, MJPEG 1280×720) — see [INSTRUCTIONS.md](INSTRUCTIONS.md) §4.2
- **Library:** `marv_vision/lib/` — camera pipelines, coordinates, VSLAM, string formatting, YOLO inference
- **Weights:** `front_model.pt` (14-class YOLO) · Pre-qual uses **OpenCV** (`vision_profile:=prequal_cv`) — [VISION_PREQUAL.md](VISION_PREQUAL.md)
- **Down camera:** `down_model.pt` still a placeholder until trained

### marv_control

- **Node:** `master_control_node`
- **Library:** `marv_control/lib/` — `avoid_obstacles`, `detect_path`, `return_home`, `traverse_gate`, `open_grip`, `close_grip`, `deploy_torpedo`

### marv_ardusub

- **Node:** `ardusub_node`
- **Library:** `marv_ardusub/lib/`
  - **`pos_est`** — critical path: fuse inputs → publish `/sensors/pose` and `/sensors/velocity` only
  - **`sensor_io`** — read raw hardware / MAVLink inputs; optional raw-topic publishing later
  - `maintain_depth`, `calculate_esc_pwm` — actuation helpers

Keep `pos_est` focused on **where the sub is and how it moves**. Do not add battery, camera, or raw IMU publishing there — use separate nodes or `sensor_io` when needed.

## Hardware (ARK FPV + Jetson)

The **ARK FPV** flight controller connects to the Jetson over **USB** (shows up as a serial device, typically `/dev/ttyACM0`). Your user must be in the `dialout` group to access it.

```
Jetson (marv_ws)  --USB-->  ARK FPV (ArduSub)  --PWM-->  thrusters / servos
                MAVROS (MAVLink serial)
                sensor_io  -->  pos_est  -->  /sensors/pose
```

**Check the link:**

```bash
lsusb | grep -i ark          # expect: Generic ARK_FPV
ls -l /dev/ttyACM*           # often ttyACM0 (+ sometimes ttyACM1)
```

**Typical MAVROS serial URL** (confirm baud in QGroundControl / ArduSub params):

```bash
ros2 run mavros mavros_node --ros-args -p fcu_url:=serial:///dev/ttyACM0:115200
```

`ardusub_node` → `sensor_io` subscribes to `/mavros/imu/data` and `/mavros/local_position/odom`, then `pos_est` publishes `/sensors/pose`.

**Healthy MAVROS (what you should see):**

- `/mavros/state`: `connected: true`, mode e.g. `MANUAL`
- `/mavros/imu/data`: non-zero orientation and linear_acceleration (~9.8 m/s² on one axis)

```bash
# Terminal 1 — MAVROS + Marv stack (or run mavros separately)
ros2 launch marv_bringup marv_bringup.launch.py

# Terminal 2 — verify pos_est output
ros2 topic echo /sensors/pose --once
```

## Control loop (pose → cmd_vel → MAVROS)

```
/sensors/pose  →  master_control_node  →  /cmd_vel  →  ardusub_node  →  MAVROS
```

Defaults are bench-safe (`enable_control:=false`, `command_backend:=log_only`). Full step-by-step procedures (MAVROS check, bench test, in-water actuation) are in **[INSTRUCTIONS.md](INSTRUCTIONS.md)**.

## Build

From the workspace root:

```bash
cd ~/marv_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

Use plain `colcon build` (not `--symlink-install`) if your setuptools version does not support editable installs.

Build a single package:

```bash
colcon build --packages-select marv_vision
```

## Run

After sourcing `install/setup.bash`, start the full stack with one command:

```bash
ros2 launch marv_bringup marv_bringup.launch.py
```

### Launch options

```bash
# Full stack (default)
ros2 launch marv_bringup marv_bringup.launch.py

# Subsystems only
ros2 launch marv_bringup ardusub.launch.py
ros2 launch marv_bringup control.launch.py
ros2 launch marv_bringup vision.launch.py

# Partial stack
ros2 launch marv_bringup marv_bringup.launch.py use_vision:=false
ros2 launch marv_bringup marv_bringup.launch.py use_front_cam:=true use_down_cam:=false

# Unity simulation (HITL — isolated from bench defaults)
ros2 launch marv_bringup sim_bringup.launch.py

# Pre-qualification (RoboSub)
ros2 launch marv_bringup prequal_bringup.launch.py enable_control:=true command_backend:=mavros_rc
```

See **[PREQUAL.md](PREQUAL.md)** for course layout, checklist, and tuning.

### Mission planner

Inspired by [Inspiration Robotics robosub_2026](https://github.com/InspirationRobotics/robosub_2026): mission classes with `step`/`cleanup`, YAML mission graphs, and per-vehicle config.

| Path | Purpose |
|------|---------|
| `marv_control/missions/` | Mission class library (`traverse_gate`, `detect_path`, …) |
| `marv_bringup/config/marv.yaml` | Vehicle + behavior tuning |
| `marv_bringup/config/plans/*.yaml` | Mission sequence graphs |
| `scripts/tmux_marv.bash` | tmux layout for bench / sim / competition |

```bash
# Planner only (master_control in planner_mode)
ros2 launch marv_bringup mission_planner.launch.py enable_control:=true

# Custom plan
ros2 launch marv_bringup competition_bringup.launch.py \
  plan_file:=$(ros2 pkg prefix marv_bringup)/share/marv_bringup/config/plans/bench_plan.yaml
```

### Individual nodes (manual)

```bash
ros2 run marv_ardusub ardusub_node
ros2 run marv_control master_control_node
ros2 run marv_vision f_cam_node
ros2 run marv_vision d_cam_node
```

## Topics (initial wiring)

| Topic | Type | Publisher | Subscriber |
|-------|------|-----------|------------|
| `f_cam/detections` | `std_msgs/String` | `f_cam_node` | `master_control_node` |
| `d_cam/detections` | `std_msgs/String` | `d_cam_node` | — |
| `cmd_vel` | `geometry_msgs/Twist` | `master_control_node` | `ardusub_node` → MAVROS |
| `/sensors/pose` | `geometry_msgs/PoseWithCovarianceStamped` | **`pos_est`** | `master_control_node` |
| `/sensors/range_forward` | `sensor_msgs/Range` | `ardusub_node` | `master_control_node` |
| `/sensors/velocity` | `geometry_msgs/TwistWithCovarianceStamped` | **`pos_est`** | — |

Raw sensors (IMU, pressure, cameras, battery) are **not** in `pos_est`. Add them via `sensor_io` or dedicated driver nodes when needed.

Behavior modules and vision pipelines are **stubs** until you add real sensor drivers, models, and ArduSub MAVLink/MAVROS integration.

## Development

- **Imports:** Each package exposes its `lib/` API via `lib/__init__.py` for use in node files.
- **Entry points:** Console scripts are declared in each package’s `setup.py`.
- **Tests:** Standard ament linters under each package’s `test/` directory.

```bash
# Example: run package tests after build
colcon test --packages-select marv_vision
colcon test-result --verbose
```


## License

This project is licensed under the [MIT License](LICENSE).
