import pickle
from pathlib import Path
import threading
import face_recognition
from config import DATASET, CACHE

enc_lock = threading.Lock()
known_encs = []
known_names = []

def build_encodings():
    encs, names = [], []
    for person_dir in DATASET.iterdir():
        if not person_dir.is_dir(): continue
        person = person_dir.name
        for img_path in person_dir.glob("*"):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}: continue
            try:
                img = face_recognition.load_image_file(str(img_path))
                e = face_recognition.face_encodings(img)
                if e:
                    encs.append(e[0])
                    names.append(person)
            except Exception as ex:
                print("[ENC] failed to load", img_path, ex)
    return encs, names

def load_encodings(use_cache=True):
    global known_encs, known_names
    with enc_lock:
        if use_cache and Path(CACHE).exists():
            try:
                with open(CACHE, "rb") as f:
                    data = pickle.load(f)
                known_encs = data.get("encodings", [])
                known_names = data.get("names", [])
                if known_encs and known_names:
                    print("[ENC] loaded from cache")
                    return
            except Exception:
                print("[ENC] cache invalid, rebuilding")
        known_encs, known_names = build_encodings()
        try:
            with open(CACHE, "wb") as f:
                pickle.dump({"encodings": known_encs, "names": known_names}, f)
        except:
            pass
        print("[ENC] ready:", len(known_names))

def rebuild_async(cb=None):
    def worker():
        load_encodings()
        if cb:
            try:
                cb()
            except:
                pass
    threading.Thread(target=worker, daemon=True).start()

# load at import
load_encodings()
