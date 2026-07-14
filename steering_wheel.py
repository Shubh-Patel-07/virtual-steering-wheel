import cv2
import mediapipe as mp
import numpy as np
import math
import time
import platform
from pynput.keyboard import Key, Controller

CAMERA_INDEX       = 0
DEAD_ZONE_DEG      = 12
RELEASE_ZONE_DEG   = 6
SOFT_ZONE_DEG      = 25
FLIP_CAMERA        = True
SHOW_ANGLE         = True
MIN_DETECTION_CONF = 0.7
MIN_TRACKING_CONF  = 0.5
GRACE_FRAMES       = 8

CLR_WHEEL   = (80, 200, 255)
CLR_LEFT    = (60, 120, 255)
CLR_RIGHT   = (50, 220, 140)
CLR_NEUTRAL = (200, 200, 200)
CLR_TEXT    = (255, 255, 255)
CLR_ACCENT  = (0, 180, 255)
CLR_HAND_L  = (255, 130, 60)
CLR_HAND_R  = (60, 230, 130)

keyboard   = Controller()
mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class SteeringController:
    def __init__(self):
        self.keys_held     = {Key.left: False, Key.right: False, Key.up: False}
        self.angle_history = []
        self.HISTORY_LEN   = 1

    def _press(self, key):
        if not self.keys_held[key]:
            keyboard.press(key)
            self.keys_held[key] = True

    def _release(self, key):
        if self.keys_held[key]:
            keyboard.release(key)
            self.keys_held[key] = False

    def release_all(self):
        for key in list(self.keys_held.keys()):
            try:
                keyboard.release(key)
            except Exception:
                pass
            self.keys_held[key] = False
        self.angle_history.clear()

    def smooth_angle(self, raw_angle: float) -> float:
        self.angle_history.append(raw_angle)
        if len(self.angle_history) > self.HISTORY_LEN:
            self.angle_history.pop(0)
        return float(np.mean(self.angle_history))

    def update(self, left_wrist, right_wrist):
        dx = right_wrist[0] - left_wrist[0]
        dy = right_wrist[1] - left_wrist[1]

        raw_angle_rad = math.atan2(dy, dx)
        raw_angle_deg = math.degrees(raw_angle_rad)
        angle = self.smooth_angle(raw_angle_deg)

        direction = "STRAIGHT"
        if angle < -DEAD_ZONE_DEG:
            direction = "LEFT"
        elif angle > DEAD_ZONE_DEG:
            direction = "RIGHT"
        elif self.keys_held[Key.left] and angle > -RELEASE_ZONE_DEG:
            direction = "STRAIGHT"
        elif self.keys_held[Key.right] and angle < RELEASE_ZONE_DEG:
            direction = "STRAIGHT"

        strength = 0.0
        if direction == "LEFT":
            strength = min(1.0, (abs(angle) - DEAD_ZONE_DEG) / (SOFT_ZONE_DEG - DEAD_ZONE_DEG))
            self._press(Key.left)
            self._release(Key.right)
        elif direction == "RIGHT":
            strength = min(1.0, (abs(angle) - DEAD_ZONE_DEG) / (SOFT_ZONE_DEG - DEAD_ZONE_DEG))
            self._press(Key.right)
            self._release(Key.left)
        else:
            self._release(Key.left)
            self._release(Key.right)

        return angle, direction, strength


def draw_steering_wheel(frame, center, angle_deg, direction, strength):
    h, w = frame.shape[:2]
    radius = int(min(w, h) * 0.10)
    cx, cy = center

    color = CLR_NEUTRAL
    if direction == "LEFT":
        color = CLR_LEFT
    elif direction == "RIGHT":
        color = CLR_RIGHT

    cv2.circle(frame, (cx + 3, cy + 3), radius, (0, 0, 0), 4)
    cv2.circle(frame, (cx, cy), radius, color, 3)

    for sa in [0, 120, 240]:
        rad = math.radians(sa - angle_deg)
        x1 = int(cx + radius * 0.4 * math.cos(rad))
        y1 = int(cy - radius * 0.4 * math.sin(rad))
        x2 = int(cx + radius * 0.95 * math.cos(rad))
        y2 = int(cy - radius * 0.95 * math.sin(rad))
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)

    cv2.circle(frame, (cx, cy), 6, color, -1)

    if direction != "STRAIGHT":
        start_a = -30 if direction == "RIGHT" else 150
        end_a   =  30 if direction == "RIGHT" else 210
        cv2.ellipse(frame, (cx, cy), (radius, radius), 0, start_a, end_a, color, 5)


def draw_hud(frame, angle, direction, strength, both_hands_visible, fps):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 130), (w, h), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    bar_w = int(w * 0.5)
    bar_h = 14
    bar_x = (w - bar_w) // 2
    bar_y = h - 90
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 60), -1)

    mid = bar_x + bar_w // 2
    cv2.rectangle(frame, (mid - 2, bar_y - 4), (mid + 2, bar_y + bar_h + 4), (180, 180, 180), -1)

    fill_len = int((bar_w // 2) * strength)
    if direction == "LEFT" and fill_len > 0:
        cv2.rectangle(frame, (mid - fill_len, bar_y), (mid, bar_y + bar_h), CLR_LEFT, -1)
    elif direction == "RIGHT" and fill_len > 0:
        cv2.rectangle(frame, (mid, bar_y), (mid + fill_len, bar_y + bar_h), CLR_RIGHT, -1)

    font      = cv2.FONT_HERSHEY_SIMPLEX
    dir_color = CLR_LEFT if direction == "LEFT" else (CLR_RIGHT if direction == "RIGHT" else CLR_NEUTRAL)
    cv2.putText(frame, "  <- LEFT",  (bar_x, bar_y - 10),           font, 0.45, CLR_LEFT,  1)
    cv2.putText(frame, "RIGHT ->",   (bar_x + bar_w - 80, bar_y - 10), font, 0.45, CLR_RIGHT, 1)
    cv2.putText(frame, direction,    (mid - 30, bar_y + bar_h + 28), font, 0.8,  dir_color, 2)

    if SHOW_ANGLE:
        cv2.putText(frame, f"{angle:+.1f} deg", (bar_x, h - 20), font, 0.55, CLR_TEXT, 1)

    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 90, 30), font, 0.55, CLR_ACCENT, 1)

    status       = "BOTH HANDS DETECTED" if both_hands_visible else "SHOW BOTH HANDS"
    status_color = (60, 220, 60) if both_hands_visible else (0, 80, 255)
    cv2.putText(frame, status, (10, 30), font, 0.55, status_color, 1)

    draw_steering_wheel(frame, (w - 80, h - 80), angle, direction, strength)


def draw_hand_connection(frame, lw, rw):
    lx, ly = lw
    rx, ry = rw
    cv2.line(frame, (lx, ly), (rx, ry), (30, 100, 200), 8)
    cv2.line(frame, (lx, ly), (rx, ry), CLR_ACCENT, 2)
    cv2.circle(frame, (lx, ly), 10, CLR_HAND_L, -1)
    cv2.circle(frame, (rx, ry), 10, CLR_HAND_R, -1)
    cv2.circle(frame, (lx, ly), 13, CLR_HAND_L, 2)
    cv2.circle(frame, (rx, ry), 13, CLR_HAND_R, 2)
    mx = (lx + rx) // 2
    my = (ly + ry) // 2
    cv2.circle(frame, (mx, my), 7, CLR_WHEEL, -1)


def main():
    backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_INDEX, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        print("  -> On macOS: System Settings > Privacy & Security > Camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    controller = SteeringController()

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=0,
        min_detection_confidence=MIN_DETECTION_CONF,
        min_tracking_confidence=MIN_TRACKING_CONF,
    )

    conn_style     = mp_drawing.DrawingSpec(color=(80, 80, 100), thickness=1)
    landmark_style = mp_drawing.DrawingSpec(color=(200, 200, 255), thickness=1, circle_radius=2)

    prev_time    = time.time()
    angle        = 0.0
    direction    = "STRAIGHT"
    strength     = 0.0
    lost_frames  = 0

    print("=" * 50)
    print("  Virtual Steering Wheel  |  Press Q to quit")
    print("=" * 50)

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            if FLIP_CAMERA:
                frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            both_visible = False

            if results.multi_hand_landmarks and results.multi_handedness:
                hand_data = {}

                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    label = handedness.classification[0].label

                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS, landmark_style, conn_style)

                    wrist = hand_landmarks.landmark[0]
                    wx    = int(wrist.x * w)
                    wy    = int(wrist.y * h)
                    hand_data[label] = (wrist.x, wrist.y, wx, wy)

                if "Left" in hand_data and "Right" in hand_data:
                    both_visible = True
                    lost_frames  = 0
                    lx_n, ly_n, lx_px, ly_px = hand_data["Left"]
                    rx_n, ry_n, rx_px, ry_px = hand_data["Right"]

                    draw_hand_connection(frame, (lx_px, ly_px), (rx_px, ry_px))
                    angle, direction, strength = controller.update((lx_n, ly_n), (rx_n, ry_n))
                else:
                    lost_frames += 1
                    if lost_frames >= GRACE_FRAMES:
                        controller.release_all()
                        angle, direction, strength = 0.0, "STRAIGHT", 0.0
            else:
                lost_frames += 1
                if lost_frames >= GRACE_FRAMES:
                    controller.release_all()
                    angle, direction, strength = 0.0, "STRAIGHT", 0.0

            now       = time.time()
            fps       = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            draw_hud(frame, angle, direction, strength, both_visible, fps)
            cv2.imshow("Virtual Steering Wheel", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q'), 27):
                break

    finally:
        controller.release_all()
        hands.close()
        cap.release()
        cv2.destroyAllWindows()
        print("\n[INFO] Stopped. All keys released.")


if __name__ == "__main__":
    main()
