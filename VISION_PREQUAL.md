# Pre-Qual Vision — Black Gate + Yellow Pole

**Default approach: OpenCV** (`vision_profile:=prequal_cv`) — no training required.  
Optional: YOLO (`vision_profile:=prequal`) — see [§ YOLO fallback](#yolo-fallback-optional) below.

| Class | Object | Detector | Used by |
|-------|--------|----------|---------|
| `black_gate` | All-black horizontal gate | Dark wide region in frame | `traverse_gate`, `pass_gate` |
| `yellow_pole` | Yellow vertical marker | HSV color mask | `circle_marker` |

Tune HSV in: `src/marv_bringup/config/prequal_cv.yaml`

---

## OpenCV mode (recommended)

### Run

```bash
source ~/marv_ws/install/setup.bash

# Bench / pool — OpenCV pre-qual vision (exploreHD USB)
ros2 run marv_vision f_cam_node --ros-args \
  -p vision_profile:=prequal_cv \
  -p conf_threshold:=0.30 \
  -p camera_device:=/dev/video0 \
  -p image_width:=1280 \
  -p image_height:=720

ros2 topic echo /f_cam/detections
# black_gate:0.65,x:0.50,y:0.55;yellow_pole:0.82,x:0.48,y:0.40

# Full pre-qual stack (prequal_bringup uses prequal_cv by default)
ros2 launch marv_bringup prequal_bringup.launch.py enable_control:=false
```

### Pool tuning (`prequal_cv.yaml`)

| Parameter | What it does |
|-----------|----------------|
| `yellow_h_low` / `yellow_h_high` | HSV hue range for pole (OpenCV H: 0–180) |
| `yellow_s_min` / `yellow_v_min` | Ignore washed-out pixels |
| `yellow_min_height_frac` | Pole must be tall in frame |
| `gate_v_max` | Max brightness for “black” gate pixels |
| `gate_min_width_frac` | Gate must span ≥20% of image width |
| `gate_roi_top_frac` | Ignore top of frame (surface glare) |
| `min_confidence` | Detection threshold |

**Black gate hard to see?** Add white corner tape on the gate, or lower `gate_v_max` slightly. Rely on **Ping** for pass-through timing.

**Camera:** Front sensor is the **Blue Robotics exploreHD** USB camera. Verify with `~/marv_ws/scripts/check_explorehd.sh`. Tune at **1 m depth** — underwater color/exposure differs from bench.

**Yellow false positives?** Raise `yellow_s_min` or `yellow_min_height_frac`.

After editing:

```bash
cd ~/marv_ws && colcon build --packages-select marv_bringup marv_vision
```

### Implementation

`marv_vision/lib/prequal_cv.py` — HSV pole + dark-region gate → same `f_cam/detections` string format as YOLO.

---

## Build the practice props

Match [RoboSub pre-qual dimensions](https://robonation.gitbook.io/robosub-resources/section-3-autonomy-challenge/3.4-competition-sequence-of-events):

- **Gate:** 2 m opening, 1 m depth, all black PVC
- **Pole:** Floor to surface, saturated yellow, 10 m past gate

---

## YOLO fallback (optional)

Use if OpenCV is unreliable in your pool (heavy glare, murky water). Train a 2-class model:

Config: `src/marv_vision/marv_vision/weights/prequal_model_data.yaml`  
Weights: `prequal_model.pt`  
Launch: `vision_profile:=prequal`

```bash
./scripts/train_prequal_yolo.sh
```

---

## Legacy YOLO training guide

<details>
<summary>Full YOLO dataset + training steps (click to expand)</summary>

Train a **2-class YOLO model** for RoboSub pre-qualification:

Minimum useful split: **250 train / 50 val / 50 test**

### What to capture

| Scenario | Images |
|----------|--------|
| Approaching gate from 3 m–0.5 m | 80+ |
| Gate centered / off-center / partial | 40+ |
| After gate — pole at 5 m–15 m | 80+ |
| Orbiting pole (circle maneuver angles) | 60+ |
| Return approach to gate | 40+ |
| Negative (no gate, no pole, walls only) | 50+ |

### Capture from the sub (best)

```bash
source ~/marv_ws/install/setup.bash
ros2 run marv_vision f_cam_node --ros-args -p conf_threshold:=0.99
# Images won't detect much — use another node or:
# Record bag and extract frames, or use rqt_image_view + screenshots
```

**Simpler:** Handheld Jetson + front USB camera at **1 m depth** in the pool, walk the course.

### Folder layout for training

```
~/marv_prequal_dataset/
├── train/images/
├── train/labels/
├── valid/images/
├── valid/labels/
└── test/images/
    test/labels/
```

---

## 3. Label in Roboflow (recommended)

1. Create project at [roboflow.com](https://roboflow.com) — **Object Detection**
2. Classes: exactly `black_gate`, `yellow_pole`
3. Draw **tight bounding boxes**:
   - `black_gate` → entire gate opening (both sides + top bar if visible)
   - `yellow_pole` → full pole from waterline to bottom of frame
4. Augmentations (moderate):
   - Brightness / exposure ±15%
   - Blur (underwater haze)
   - **Avoid** heavy mosaic/mixup early — gate geometry matters
5. Export → **YOLOv8** format → download into `~/marv_prequal_dataset/`

Update paths in `prequal_model_data.yaml` if your dataset lives elsewhere.

---

## 4. Train on the Jetson

```bash
pip3 install 'numpy<2' ultralytics

cd ~/marv_ws/src/marv_vision/marv_vision/weights

yolo detect train \
  data=prequal_model_data.yaml \
  model=yolov8n.pt \
  imgsz=640 \
  epochs=100 \
  batch=8 \
  patience=20 \
  project=prequal_runs \
  name=v1
```

When training finishes:

```bash
cp prequal_runs/v1/weights/best.pt prequal_model.pt
cd ~/marv_ws && colcon build --packages-select marv_vision
```

**Jetson too slow?** Train on a PC with GPU, copy `best.pt` to the Jetson as `prequal_model.pt`.

---

## 5. Validate before pool autonomy

```bash
source ~/marv_ws/install/setup.bash

# Live camera + prequal model
ros2 run marv_vision f_cam_node --ros-args \
  -p vision_profile:=prequal \
  -p conf_threshold:=0.30

# Expect strings like:
# black_gate:0.85,x:0.52,y:0.48
# yellow_pole:0.78,x:0.61,y:0.40
ros2 topic echo /f_cam/detections
```

| Check | Pass criteria |
|-------|----------------|
| Gate at 3 m | `black_gate` stable, conf > 0.5 |
| Gate centered | `x` near 0.5 (±0.1) |
| Pole at 10 m | `yellow_pole` detected |
| False positives | No detections on empty wall |

Tune `conf_threshold` (0.25–0.45) and `marv.yaml` `conf_min` values.

---

## 6. Run with pre-qual stack

```bash
ros2 launch marv_bringup prequal_bringup.launch.py \
  vision_profile:=prequal \
  use_ping_driver:=true \
  enable_control:=true \
  command_backend:=mavros_rc
```

(`prequal_bringup` already sets `vision_profile:=prequal` and disables down cam.)

Behavior class names in `marv_bringup/config/marv.yaml`:

```yaml
traverse_gate:
  gate_classes: [black_gate, gate]
circle_marker:
  marker_classes: [yellow_pole]
```

---

## 7. Unity HITL (optional)

Place black gate + yellow pole meshes in Unity with colors matching pool props.  
Publish to `/unity/f_cam/image_raw` and train/validate with `use_sim:=true`.

---

## 8. Troubleshooting

| Problem | Fix |
|---------|-----|
| Gate not detected | More gate images; lower `conf_min`; add corner tape for contrast |
| Pole confused with lane line | More negatives; label only the pole class |
| Detections jump left/right | Raise `aligned_frames_required` in `marv.yaml` |
| `prequal_model.pt not found` warning | Train and copy `best.pt` (falls back to `front_model.pt` until then) |
| Slow inference | Use `yolov8n.pt` base; reduce `imgsz` to 416 |

</details>

---

## Related

- [PREQUAL.md](PREQUAL.md) — full maneuver + pool checklist  
- [INSTRUCTIONS.md](INSTRUCTIONS.md) — camera + MAVROS setup  
- `config/plans/prequal_plan.yaml` — mission sequence
