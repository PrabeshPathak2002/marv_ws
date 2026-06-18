# Marv AUV — Operating Instructions

Step-by-step guide for building, connecting the ARK FPV flight controller, verifying MAVROS, and running the pose → control → actuation loop.

For architecture and package overview, see [README.md](README.md).

---

## 1. One-time setup

### 1.1 Build the workspace

```bash
cd ~/marv_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

Add to `~/.bashrc` (optional):

```bash
source /opt/ros/humble/setup.bash
source ~/marv_ws/install/setup.bash
```

### 1.2 USB permissions (ARK FPV on Jetson)

Your Linux user must be in the `dialout` group:

```bash
groups | grep dialout
# If missing:
sudo usermod -aG dialout $USER
# Log out and back in
```

### 1.3 Install MAVROS (if not already installed)

```bash
sudo apt install ros-humble-mavros ros-humble-mavros-extras
```

---

## 2. Hardware connection

| Item | Detail |
|------|--------|
| Flight controller | ARK FPV running **ArduSub** |
| Link to Jetson | **USB** cable |
| Typical device | `/dev/ttyACM0` (sometimes also `ttyACM1`) |
| MAVROS URL | `serial:///dev/ttyACM0:115200` |

**Verify USB:**

```bash
lsusb | grep -i ark
ls -l /dev/ttyACM*
```

Expected: `Generic ARK_FPV` and `crw-rw---- ... ttyACM0`.

---

## 3. Software architecture (what runs where)

```
ARK FPV (USB/MAVLink)
        ↓
     MAVROS
        ↓
  sensor_io (read)  →  pos_est (fuse)  →  /sensors/pose
                                              ↓
                                    master_control_node
                                              ↓
                                          /cmd_vel
                                              ↓
                                      ardusub_node
                                              ↓
                           MAVROS RC override or setpoint_velocity
```

| Module | Package | Job |
|--------|---------|-----|
| `sensor_io` | marv_ardusub | Subscribe to MAVROS IMU + odometry |
| `pos_est` | marv_ardusub | Publish `/sensors/pose`, `/sensors/velocity` only |
| `master_control_node` | marv_control | Mission logic + depth-hold `cmd_vel` |
| `mavros_actuation` | marv_ardusub | Send `cmd_vel` to the flight controller |

---

## 4. Procedure A — Verify MAVROS only

Use this when the ARK FPV is plugged in and you want to confirm the link before starting Marv.

**Terminal 1 — start MAVROS:**

```bash
source ~/marv_ws/install/setup.bash
ros2 launch marv_bringup mavros.launch.py
# Or manually:
# ros2 run mavros mavros_node --ros-args -p fcu_url:=serial:///dev/ttyACM0:115200
```

**Terminal 2 — check topics:**

```bash
source ~/marv_ws/install/setup.bash
ros2 topic echo /mavros/state --once
ros2 topic echo /mavros/imu/data --once
```

**Healthy signs:**

| Check | Good value |
|-------|------------|
| `connected` | `true` |
| `mode` | e.g. `MANUAL` (normal on bench) |
| `armed` | `false` on bench |
| IMU `linear_acceleration` | ~9.8 m/s² on one axis (gravity) |

If `connected: false`, check USB cable, port (`ttyACM0` vs `ttyACM1`), and baud rate in QGroundControl.

---

## 5. Procedure B — Position estimate (no motion commands)

Starts MAVROS + `ardusub_node` + `master_control` with **control disabled**.

```bash
source ~/marv_ws/install/setup.bash
ros2 launch marv_bringup marv_bringup.launch.py \
  use_vision:=false \
  enable_control:=false \
  command_backend:=log_only
```

**Verify in another terminal:**

```bash
ros2 topic echo /sensors/pose --once
ros2 topic echo /sensors/velocity --once
ros2 topic echo /cmd_vel
```

- `/sensors/pose` orientation should track the IMU (not all zeros).
- `/cmd_vel` should be all zeros.

**If position is always (0,0,0):**

```bash
ros2 topic echo /mavros/local_position/odom --once
```

Without GPS/DVL, ArduSub may only provide good **attitude** until position sources are configured. Depth-hold still uses the `z` component when odometry is available.

---

## 6. Procedure C — Control loop on the bench (no thruster output)

Enables depth-hold logic but only **logs** commands (`command_backend:=log_only`).

```bash
ros2 launch marv_bringup marv_bringup.launch.py \
  use_vision:=false \
  enable_control:=true \
  command_backend:=log_only \
  target_depth_m:=1.0
```

**Watch commands:**

```bash
ros2 topic echo /cmd_vel
```

You should see `linear.z` (heave) change when depth error changes. Thrusters do **not** move in `log_only` mode.

**If MAVROS is already running** (Procedure A in another terminal):

```bash
ros2 launch marv_bringup marv_bringup.launch.py \
  use_mavros:=false \
  use_vision:=false \
  enable_control:=true \
  command_backend:=log_only
```

---

## 7. Procedure D — Live actuation (in water only)

**Safety checklist before proceeding:**

- [ ] Vehicle in water, props clear
- [ ] QGroundControl connected; you can disarm instantly
- [ ] Understand current flight mode (`MANUAL`, `ALT_HOLD`, etc.)
- [ ] Start with small `target_depth_m` and low `depth_kp`
- [ ] Spotter / operator ready

**Launch with RC override backend** (matches ArduSub + QGC setups):

```bash
ros2 launch marv_bringup marv_bringup.launch.py \
  use_vision:=false \
  enable_control:=true \
  command_backend:=mavros_rc \
  target_depth_m:=1.0
```

**Alternative — velocity setpoints** (may require `GUIDED` or compatible mode):

```bash
ros2 launch marv_bringup marv_bringup.launch.py \
  use_vision:=false \
  enable_control:=true \
  command_backend:=setpoint_velocity
```

Monitor logs on `ardusub_node` for lines like:

```text
cmd_vel -> MAVROS (mavros_rc): surge=0.00 sway=0.00 heave=0.12 yaw=0.00
```

---

## 8. Launch parameters reference

| Argument | Default | Description |
|----------|---------|-------------|
| `use_mavros` | `true` | Start MAVROS node |
| `fcu_url` | `serial:///dev/ttyACM0:115200` | ARK FPV USB serial URL |
| `use_ardusub` | `true` | Start `ardusub_node` |
| `use_control` | `true` | Start `master_control_node` |
| `use_vision` | `true` | Start camera nodes |
| `enable_control` | `false` | Publish depth-hold `cmd_vel` |
| `command_backend` | `log_only` | `log_only`, `mavros_rc`, `setpoint_velocity`, `disabled` |
| `target_depth_m` | `1.0` | Depth setpoint (NED z, meters positive down) |

### Subsystem launches

```bash
ros2 launch marv_bringup mavros.launch.py
ros2 launch marv_bringup ardusub.launch.py command_backend:=log_only
ros2 launch marv_bringup control.launch.py enable_control:=true
ros2 launch marv_bringup vision.launch.py
```

---

## 9. Troubleshooting

| Problem | Things to try |
|---------|----------------|
| No `/dev/ttyACM0` | Replug USB; try `ttyACM1`; check `lsusb` |
| `connected: false` | Wrong port/baud; close QGC serial hogging the port |
| No `/sensors/pose` | Is `ardusub_node` running? Is MAVROS up? |
| `/cmd_vel` always zero | Set `enable_control:=true` |
| Commands logged but no motion | Set `command_backend:=mavros_rc`; arm vehicle; check mode |
| Heave wrong direction | Set `heave_pwm_invert:=true` on `ardusub_node` |
| Position always zero | Expected without GPS/DVL; check `/mavros/local_position/odom` |

**List active nodes and topics:**

```bash
ros2 node list
ros2 topic list | grep -E 'mavros|sensors|cmd_vel'
```

**Kill a stuck stack:**

```bash
# Ctrl+C in the launch terminal, or:
pkill -f "ros2 launch marv_bringup"
```

---

## 10. Recommended progression

1. **Procedure A** — MAVROS link OK  
2. **Procedure B** — `/sensors/pose` publishing  
3. **Procedure C** — `/cmd_vel` responds on bench (`log_only`)  
4. **Procedure D** — in-water test with `mavros_rc`  
5. Next: cameras / `traverse_gate` / simulation (see README)

---

## 11. Front camera vision model

Runtime files (in repo, installed with `marv_vision`):

| File | Purpose |
|------|---------|
| `src/marv_vision/marv_vision/weights/front_model.pt` | YOLO weights |
| `src/marv_vision/marv_vision/weights/front_model_data.yaml` | Class names (`nc: 14`) |

Training image folders referenced in the yaml (`../train/images`, etc.) stay **outside** the repo.

**Requires:** `pip install 'numpy<2' ultralytics` (NumPy 2.x breaks ROS `cv_bridge` on Humble).

### Unity simulation (HITL)

Vision nodes support hardware vs Unity sim via `use_sim`:

| Mode | `use_sim` | Input |
|------|-----------|--------|
| Hardware (default) | `false` | OpenCV `VideoCapture` (`camera_index` 0 / 1) |
| Unity HITL | `true` | `/unity/f_cam/image_raw`, `/unity/d_cam/image_raw` |

```bash
ros2 launch marv_bringup marv_bringup.launch.py use_sim:=true
# Or per-node:
ros2 run marv_vision f_cam_node --ros-args -p use_sim:=true
```

Detection output on `f_cam/detections` / `d_cam/detections` is unchanged.

### Unity HITL bridge (`unity_hil_bridge`)

Middleware between Unity (ROS-TCP-Endpoint) and ArduSub (MAVROS):

| Direction | Topics |
|-----------|--------|
| Unity → ArduSub | `/unity/imu` + `/unity/pose` → `/mavros/hil/sensor` |
| ArduSub → Unity | `/mavros/rc/out` → `/unity/thruster_forces` |

```bash
# With MAVROS + bridge (typical Unity HITL session)
ros2 launch marv_bringup marv_bringup.launch.py \
  use_sim:=true use_unity_hil_bridge:=true use_mavros:=true

# Bridge only
ros2 launch marv_bringup unity_hil_bridge.launch.py

### Full Unity simulation (`sim_bringup.launch.py`)

One launch file for the entire Unity HITL stack (isolated from bench defaults):

```bash
ros2 launch marv_bringup sim_bringup.launch.py
```

Starts: ROS-TCP-Endpoint (port 10000) → MAVROS → `unity_hil_bridge` →
`f_cam_node` / `d_cam_node` (`use_sim:=true`) → `master_control_node`.

`ardusub_node` is included by default (`use_pos_est_stack:=true`) for
`/sensors/pose` and `cmd_vel` → MAVROS. It does **not** publish HIL data.

```bash
# Enable control once sim is verified
ros2 launch marv_bringup sim_bringup.launch.py enable_control:=true

# Without ardusub (vision + HIL only)
ros2 launch marv_bringup sim_bringup.launch.py use_pos_est_stack:=false
```

`ros_tcp_endpoint` is installed at `~/marv_ws/src/ros_tcp_endpoint` (branch `main-ros2`).
```

Thruster PWM channels default to indices `[2, 3, 4, 5]` (ArduSub thr/yaw/fwd/lat), published as normalized `[-1, 1]` forces.

```bash
source ~/marv_ws/install/setup.bash
python3 -c "from marv_vision.lib.model_config import load_front_model_config; print(load_front_model_config())"
```

---

## 12. Related files

| File | Purpose |
|------|---------|
| [README.md](README.md) | Workspace overview, topics, build |
| [LICENSE](LICENSE) | MIT license |
| `src/marv_bringup/launch/` | Launch files |
| `src/marv_ardusub/marv_ardusub/lib/sensor_io.py` | MAVROS sensor input |
| `src/marv_ardusub/marv_ardusub/lib/pos_est.py` | Position estimate |
| `src/marv_control/marv_control/master_control_node.py` | Control node |
| `src/marv_ardusub/marv_ardusub/lib/mavros_actuation.py` | MAVROS output |
