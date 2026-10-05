import time
import cv2
import numpy as np
import face_recognition
from datetime import datetime
from config import CAM_IDX, FRAME_SCALE, MATCH_TOL, REQUIRED
from face_encodings import enc_lock, known_encs, known_names
from db import record_attendance_db
from pathlib import Path
from config import SNAP

# minimal state holder (could be improved)
_capture = None
_running = False
_last_marked = {}  # person -> datetime

def record_attendance(person, crop=None, session_id=None, cooldown=40):
    now = datetime.now()
    ts = now.isoformat(timespec="seconds")
    d = now.date().isoformat()

    last = _last_marked.get(person)
    if last and (now - last).total_seconds() < cooldown and last.date() == now.date():
        return False

    ok = record_attendance_db(person, ts, d, session_id)
    if ok:
        _last_marked[person] = now
        if crop is not None:
            fname = f"{person}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(str(Path(SNAP) / fname), crop)
    return ok

def start_recognition(active_session_getter, stop_event):
    """active_session_getter: callable returning current session dict {'id':..., 'name':...}
       stop_event: threading.Event set() means run; clear to stop"""
    global _capture, _running
    cap = cv2.VideoCapture(CAM_IDX)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")
    _capture = cap
    _running = True
    scale = int(1 / FRAME_SCALE)
    counters = {}

    try:
        while stop_event.is_set():
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.03)
                continue

            small = cv2.resize(frame, (0,0), fx=FRAME_SCALE, fy=FRAME_SCALE)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            locs = face_recognition.face_locations(rgb)
            encs = face_recognition.face_encodings(rgb, locs)

            # decay counters
            for k in list(counters.keys()):
                counters[k] -= 0.15
                if counters[k] <= 0: counters.pop(k)

            for enc, loc in zip(encs, locs):
                with enc_lock:
                    if not known_encs: continue
                    dists = face_recognition.face_distance(known_encs, enc)
                idx = int(np.argmin(dists))
                dist = float(dists[idx])
                if dist <= MATCH_TOL:
                    person = known_names[idx]
                    counters[person] = counters.get(person, 0) + 1
                    if counters[person] >= REQUIRED:
                        t, r, b, l = loc
                        t *= scale; r *= scale; b *= scale; l *= scale
                        crop = frame[int(t):int(b), int(l):int(r)]
                        record_attendance(person, crop, active_session_getter().get("id"))
                        counters[person] = 0

            # preview drawing (optional)
            for enc, loc in zip(encs, locs):
                with enc_lock:
                    dists = face_recognition.face_distance(known_encs, enc) if known_encs else []
                if len(dists) == 0:
                    label="Unknown"; color=(0,0,255)
                else:
                    idx = int(np.argmin(dists))
                    if float(dists[idx]) <= MATCH_TOL:
                        label = known_names[idx]; color=(0,255,0)
                    else:
                        label="Unknown"; color=(0,0,255)
                t, r, b, l = loc
                t *= scale; r *= scale; b *= scale; l *= scale
                cv2.rectangle(frame, (l,t), (r,b), color, 2)
                cv2.rectangle(frame, (l, b-20), (r, b), color, -1)
                cv2.putText(frame, label, (l+5, b-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

            cv2.putText(frame, f"Session: {active_session_getter().get('name') or 'None'}",
                        (10,25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

            cv2.imshow("Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        try: cap.release()
        except: pass
        try: cv2.destroyAllWindows()
        except: pass
        _capture = None
        _running = False
