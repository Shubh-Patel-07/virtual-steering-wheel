# 🎮 Virtual Steering Wheel — MediaPipe + Python

Control any car game using your hands as a steering wheel — no hardware needed. Just your webcam.

---

## How It Works

Hold both fists toward the camera like you're gripping a steering wheel. Tilt your hands to steer.

```
Both hands level  →  Straight (no key pressed)
Tilt LEFT         →  ← LEFT arrow key
Tilt RIGHT        →  → RIGHT arrow key
Remove hands      →  All keys released instantly
```

---

## Requirements

- Python 3.9+
- Webcam

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run

```bash
python3 steering_wheel.py
```

Press **Q** in the camera window to quit.

---

## macOS Setup ⚠️

On macOS, grant camera permission to Terminal (or your Python launcher) before running:

1. Go to **System Settings → Privacy & Security → Camera**
2. Enable access for **Terminal** (or your Python launcher)
3. Run the script again

---

## Windows Setup

The script works on Windows with **one small change**. Open `steering_wheel.py` and find this line:

```python
backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
```

This line already auto-detects your OS — **no manual change needed**. On Windows it will automatically use `cv2.CAP_ANY` (DirectShow/MSMF).

**Steps for Windows:**

1. Install Python from https://python.org

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python steering_wheel.py
   ```

4. If the camera doesn't open, try changing `CAMERA_INDEX` at the top of `steering_wheel.py`:
   ```python
   CAMERA_INDEX = 0   # primary webcam; try 1 or 2 for external cameras
   ```

> **Note for Windows:** You may see a Windows Security prompt asking if Python can access your camera — click **Allow**.

---

## Config (top of `steering_wheel.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `CAMERA_INDEX` | `0` | `0` = built-in webcam, `1` = external USB camera |
| `DEAD_ZONE_DEG` | `12` | Degrees of tilt to ignore at center (prevents jitter) |
| `FLIP_CAMERA` | `True` | Mirror the feed (selfie view). Set `False` for some external cameras |
| `GRACE_FRAMES` | `8` | Frames to wait before releasing keys when hands disappear |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `[ERROR] Cannot open camera` | Check `CAMERA_INDEX` — try `0`, `1`, `2` |
| Steering is reversed | Toggle `FLIP_CAMERA = False` in config |
| Keys stuck after removing hands | Hands must be fully out of frame for ~8 frames |
| Low FPS / laggy | Lower camera resolution in the script or close other apps |

---

## Works With Any Game That Uses Arrow Keys

- Google Chrome Dinosaur game
- Trackmania
- TORCS
- Hill Climb Racing (browser)
- Any browser/PC racing game using arrow keys
