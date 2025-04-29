import cv2
import numpy as np
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Helper utils --------------------------------------------------------------
# ---------------------------------------------------------------------------

def _expand_box(box: list[float], scale: float, max_w: int, max_h: int) -> list[int]:
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    return [
        max(0, int(x1 - scale * bw)),
        max(0, int(y1 - scale * bh)),
        min(max_w, int(x2 + scale * bw)),
        min(max_h, int(y2 + scale * bh)),
    ]


def _hash_color(key: str) -> tuple[int, int, int]:
    np.random.seed(abs(hash(key)) % (2**32))
    return tuple(int(v) for v in np.random.randint(64, 256, 3))  # BGR


def _draw_box(img: np.ndarray, xyxy: tuple[int, int, int, int], color: tuple[int, int, int], label: str, thickness: int = 2):
    x1, y1, x2, y2 = xyxy
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    cv2.putText(img, label, (x1, max(0, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)


def _yolo_detections(model, img: np.ndarray, conf_thresh: float = 0.5) -> list[dict]:
    results = model(img, stream=False, verbose=False)
    dets: list[dict] = []
    for r in results:
        names = r.names
        for b in r.boxes:
            conf = float(b.conf.item())
            if conf < conf_thresh:
                continue
            cls = names[int(b.cls.item())]
            dets.append({
                "class": cls,
                "conf": conf,
                "box": list(map(float, b.xyxy[0].cpu().numpy())),
            })
    return dets


def _is_civilian(police_model, crop: np.ndarray) -> tuple[bool, float]:
    probs = police_model(crop, stream=False, verbose=False)[0].probs.data.cpu().numpy()
    return probs.argmax() == 1, float(probs.max())

# ---------------------------------------------------------------------------
# process_frame_with_yolo  --------------------------------------------------
# ---------------------------------------------------------------------------

def process_frame_with_yolo(
    frame: np.ndarray,
    base_model,
    weapon_model,
    police_model,
    return_detections: bool = False,
    expand: float = 0.3,
):
    if frame is None:
        return (None, []) if return_detections else None

    h, w = frame.shape[:2]
    dark = cv2.convertScaleAbs(frame, alpha=1, beta=-75)
    weapon_detections: list[dict] = []

    persons = [d for d in _yolo_detections(base_model, frame, 0.6) if d["class"] == "person"]

    for p in persons:
        x1, y1, x2, y2 = _expand_box(p["box"], expand, w, h)
        isolated = frame[y1:y2, x1:x2].copy()
        dark[y1:y2, x1:x2] = isolated

        civilian, _ = _is_civilian(police_model, isolated)
        label = "civilian" if civilian else "police"
        color = (0, 255, 0) if civilian else (255, 0, 0)

        if civilian:
            for w_det in _yolo_detections(weapon_model, isolated, 0.6):
                wx1, wy1, wx2, wy2 = [int(w_det["box"][i] + (x1 if i % 2 == 0 else y1)) for i in range(4)]
                w_color = _hash_color(w_det["class"])
                _draw_box(dark, (wx1, wy1, wx2, wy2), w_color, f"{w_det['class']}:{w_det['conf']:.2f}")
                if return_detections:
                    weapon_detections.append({
                        "class_name": w_det["class"],
                        "confidence": round(w_det["conf"], 2),
                        "x1": wx1, "y1": wy1, "x2": wx2, "y2": wy2,
                    })

        _draw_box(dark, (x1, y1, x2, y2), color, f"{label}:{p['conf']:.2f}")

    return (dark, weapon_detections) if return_detections else dark