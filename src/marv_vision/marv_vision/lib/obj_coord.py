"""Object coordinate calculation from detections."""


def calculate_obj_coord(detection, image_width=640, image_height=480, camera_params=None):
    """Compute normalized image position and horizontal bearing from bbox."""
    xyxy = detection.get('xyxy')
    if not xyxy or len(xyxy) != 4:
        return None

    x1, y1, x2, y2 = xyxy
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    width = max(float(image_width), 1.0)
    height = max(float(image_height), 1.0)

    norm_x = cx / width
    norm_y = cy / height
    bearing_x = (cx - width / 2.0) / (width / 2.0)

    return {
        'norm_x': norm_x,
        'norm_y': norm_y,
        'bearing_x': max(-1.0, min(1.0, bearing_x)),
        'bbox_area': max(0.0, (x2 - x1) * (y2 - y1)),
    }
