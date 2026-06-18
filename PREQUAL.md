# RoboSub Pre-Qualification Preparation — Marv AUV

Guide for the optional [RoboSub pre-qualification maneuver](https://robonation.gitbook.io/robosub-resources/section-3-autonomy-challenge/3.4-competition-sequence-of-events). Success skips on-site qualification and advances you directly to semi-finals.

**Submission deadline:** June 24, 2026 · **Submit video:** [robosub.org/pre-qual](https://robosub.org/pre-qual)

---

## What you must do (autonomous)

| Step | Requirement |
|------|-------------|
| 1 | Submerge; start **3 m behind** the gate |
| 2 | Pass **through** the horizontal gate |
| 3 | **Circle** the vertical marker **10 m** beyond the gate |
| 4 | Pass **back through** the gate |
| 5 | Everything stays submerged; **one continuous unedited video** |

---

## Pool course layout

Build to [handbook dimensions](https://robonation.gitbook.io/robosub-resources/section-3-autonomy-challenge/3.4-competition-sequence-of-events):

```
        [Marker — floor to surface, 10 m ahead]
                    |
                    |  10 m
                    |
    ----==== GATE (2 m wide, 1 m depth) ====----
                    |
                    |  3 m
                    |
              [START — submerged]
```

| Element | Spec |
|---------|------|
| Gate | 2 m (6.6 ft) horizontal opening, **1 m below surface** |
| Marker | Vertical pole, **10 m** past gate, touches floor + breaks surface |
| Start | **3 m behind** gate, fully submerged |
| Video | Single take, full run visible, no cuts |

Can't build full course? Email RoboNation for alternate instructions (per handbook).

---

## How Marv maps to the maneuver

| Pre-qual phase | Marv mission | Notes |
|----------------|--------------|-------|
| Submerge & hold | `wait_submerged` | Depth hold at `target_depth_m:=1.0` |
| Align to gate | `traverse_gate` | YOLO `black_gate` (all-black gate) |
| Pass through gate | `pass_gate` | Ping range + forward surge |
| Transit to marker | `transit_forward` | ~10 m dead reckoning |
| Circle marker | `circle_marker` | YOLO `yellow_pole` |
| Turn for return | `turn_around` | ~180° using `/sensors/pose` yaw |
| Re-align & pass gate | `traverse_gate` + `pass_gate` | Same as outbound |
| Stop | `hold` | Zero cmd_vel |

Mission graph: `marv_bringup/config/plans/prequal_plan.yaml`

Tuning: `marv_bringup/config/marv.yaml` → `behaviors:` section

**Vision:** OpenCV `prequal_cv` mode (default in `prequal_bringup`) — tune `config/prequal_cv.yaml`. See **[VISION_PREQUAL.md](VISION_PREQUAL.md)**.

---

## Launch commands

### Bench (safe — no thrusters)

```bash
source ~/marv_ws/install/setup.bash
ros2 launch marv_bringup prequal_bringup.launch.py enable_control:=false
ros2 topic echo /mission_planner/status
```

### Pool / video attempt

```bash
# 1. Verify MAVROS + pose
ros2 topic echo /mavros/state --once          # connected: true
ros2 topic echo /sensors/pose --once

# 2. Arm only when ready in water (manual or your arm script)
# 3. Full pre-qual stack
ros2 launch marv_bringup prequal_bringup.launch.py \
  enable_control:=true \
  command_backend:=mavros_rc \
  target_depth_m:=1.0
```

### Unity HITL practice (no pool)

```bash
ros2 launch marv_bringup prequal_bringup.launch.py \
  use_sim:=true enable_control:=true command_backend:=mavros_rc
```

---

## Pre-run checklist

### Hardware
- [ ] ARK FPV USB connected (`ls /dev/ttyACM0`)
- [ ] Jetson in `dialout` group
- [ ] All tethers/cables submerged with vehicle
- [ ] Thrusters spin correct direction (bench test first)
- [ ] Depth sensor / barometer calibrated in QGC
- [ ] Battery fully charged; leak check done

### Software
- [ ] `colcon build` + `source install/setup.bash`
- [ ] `numpy<2` installed (`pip3 show numpy`)
- [ ] exploreHD USB detected (`~/marv_ws/scripts/check_explorehd.sh`)
- [ ] Front camera sees gate at pool depth (1280×720 MJPEG on `/dev/video0`)
- [ ] `ros2 topic echo f_cam/detections` shows `black_gate:...` / `yellow_pole:...`
- [ ] `/sensors/pose` updating (required for transit + turn)
- [ ] `enable_control:=false` verified on bench before pool

### Pool / course
- [ ] Gate at 1 m depth, 2 m opening
- [ ] Marker 10 m beyond gate
- [ ] Start position 3 m behind gate, submerged
- [ ] Camera not blinded by sun/reflections
- [ ] Video camera rolling **before** submerge (single continuous take)

### Video submission
- [ ] Full autonomous run, no human joystick input
- [ ] Gate pass → circle → return gate pass all visible
- [ ] No surface breach
- [ ] Upload to [robosub.org/pre-qual](https://robosub.org/pre-qual) before **June 24, 2026**

---

## Tuning guide

Edit `src/marv_bringup/config/marv.yaml`:

| Parameter | What to adjust |
|-----------|----------------|
| `traverse_gate.conf_min` | Raise if false detections; lower if gate missed |
| `traverse_gate.aligned_frames_required` | More = stricter alignment before surge |
| `pass_gate.duration_s` | Increase if gate is wide / sub is slow |
| `transit_forward.target_distance_m` | Match pool marker distance (default 10 m) |
| `circle_marker.orbit_duration_s` | Full orbit time; tune in pool |
| `circle_marker.marker_classes` | Use `[yellow_pole]` for yellow pole marker |
| `control.target_depth_m` | Gate depth (1.0 m per spec) |

After edits:

```bash
cd ~/marv_ws && colcon build --packages-select marv_bringup marv_control
```

---

## Known gaps & mitigations

| Gap | Impact | Mitigation |
|-----|--------|------------|
| No DVL | Transit uses MAVROS odom drift | Tune `transit_forward.target_distance_m` in pool |
| Ping not installed | Gate pass falls back to timed surge | Install `ping_sonar_ros`; verify `/sensors/range_forward` |
| Marker not in YOLO set | `circle_marker` may not see marker | Train marker class or tune timed orbit |
| `pos_est` is MAVROS odom | Turn/transit accuracy varies | Practice turns in pool; log pose |
| Down camera unused | No bottom marker view | Front cam only for pre-qual |

---

## Debugging during practice

```bash
ros2 topic echo /mission_planner/status
ros2 param get /master_control_node active_behavior
ros2 topic echo /f_cam/detections
ros2 topic echo /sensors/pose
ros2 topic echo /cmd_vel
```

---

## Related files

| File | Purpose |
|------|---------|
| `config/plans/prequal_plan.yaml` | Full pre-qual mission graph |
| `config/marv.yaml` | Vehicle + behavior tuning |
| `launch/prequal_bringup.launch.py` | One-command pre-qual stack |
| [INSTRUCTIONS.md](INSTRUCTIONS.md) | Bench + MAVROS procedures |
