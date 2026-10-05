import time
import cv2
from datetime import datetime
from pathlib import Path
from config import DATASET, CAM_IDX, FRAME_SCALE, CAPTURE_COUNT, CAPTURE_DELAY
from face_encodings import enc_lock, rebuild_async, CACHE

def enroll_worker(name, notify_callback=None):
    safe = name.strip().replace("/", "_").replace("\\", "_")
    if not safe:
        if notify_callback: notify_callback("Invalid name")
        return

    if not enc_lock.acquire(timeout=2):
        if notify_callback: notify_callback("Camera busy")
        return

    folder = Path(DATASET) / safe
    folder.mkdir(parents=True, exist_ok=True)
    saved = 0
    last = 0

    try:
        cap = cv2.VideoCapture(CAM_IDX)
        if not cap.isOpened():
            if notify_callback: notify_callback("Cannot open camera")
            return

        if notify_callback: notify_callback(f"Enrollment for {safe}. Press Q to cancel.")

        while saved < CAPTURE_COUNT:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05); continue

            small = cv2.resize(frame, (0,0), fx=FRAME_SCALE, fy=FRAME_SCALE)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locs = cv2.face.detectMultiScale if False else []  # placeholder: use face_recognition in real code

            preview = frame.copy()
            cv2.putText(preview, f"Captured: {saved}/{CAPTURE_COUNT}", (10,25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

            # use face_recognition to detect faces here for real saving
            import face_recognition
            locs = face_recognition.face_locations(rgb)

            if locs and time.time() - last >= CAPTURE_DELAY:
                filename = f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(str(folder / filename), frame)
                saved += 1; last = time.time()

            cv2.imshow("Enrollment", preview)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if saved > 0:
            try: Path(CACHE).unlink()
            except: pass
            rebuild_async(lambda: notify_callback("Enrollment completed.") if notify_callback else None)
        else:
            if notify_callback: notify_callback("Cancelled: no photos saved.")
    finally:
        try: cap.release()
        except: pass
        try: cv2.destroyAllWindows()
        except: pass
        enc_lock.release()
