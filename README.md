# Marv AUV — ROS 2 Workspace

Modular [ROS 2 Humble](https://docs.ros.org/en/humble/) workspace for the **Marv** autonomous underwater vehicle (AUV). The stack is split into vision, high-level control, and ArduSub hardware interface packages so each subsystem can be developed and tested independently.

## Prerequisites

- Ubuntu 22.04 (or compatible) with **ROS 2 Humble** installed
- `colcon` and common ROS build tools:

```bash
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions
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
└── README.md
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
- **Library:** `marv_vision/lib/` — camera pipelines, coordinates, VSLAM, string formatting, YOLO inference
- **Weights:** `marv_vision/weights/front_model.pt`, `down_model.pt` (placeholders; replace with trained models)

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
| `cmd_vel` | `geometry_msgs/Twist` | `master_control_node` | `ardusub_node` |
| `/sensors/pose` | `geometry_msgs/PoseWithCovarianceStamped` | **`pos_est`** | — |
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
