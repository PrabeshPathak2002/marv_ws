"""Serialize and parse detection strings for ROS topics."""


def format_detection_string(detections):
    """Format detections as: class:conf,x:0.42,y:0.55;..."""
    if not detections:
        return ''
    parts = []
    for det in detections:
        name = det.get('class_name', '?')
        conf = det.get('confidence', 0.0)
        part = f'{name}:{conf:.2f}'
        coord = det.get('coord')
        if coord:
            part += f',x:{coord["norm_x"]:.3f},y:{coord["norm_y"]:.3f}'
        parts.append(part)
    return ';'.join(parts)


def parse_detection_string(data):
    """Parse detection string back into a list of dicts."""
    if not data:
        return []
    detections = []
    for entry in data.split(';'):
        entry = entry.strip()
        if not entry:
            continue
        det = {}
        fields = entry.split(',')
        head = fields[0].split(':')
        if len(head) != 2:
            continue
        det['class_name'] = head[0]
        try:
            det['confidence'] = float(head[1])
        except ValueError:
            continue
        for field in fields[1:]:
            if ':' not in field:
                continue
            key, value = field.split(':', 1)
            try:
                det[key] = float(value)
            except ValueError:
                pass
        detections.append(det)
    return detections
