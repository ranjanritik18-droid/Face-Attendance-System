import threading
import time
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

from config import PANDAS_OK
from face_encodings import load_encodings, rebuild_async
from enroll import enroll_worker
from camera import start_recognition
from exporter import export_file
from db import create_session, list_sessions, get_session, fetch_recent

# state
active_session = {"id": None, "name": None}
stop_event = threading.Event()

# create root
root = tk.Tk()
root.title("Modular Face Attendance")

def start_btn():
    if stop_event.is_set():
        messagebox.showinfo("Info", "Camera already running")
        return
    # ensure encodings loaded
    load_encodings()
    stop_event.set()
    threading.Thread(target=lambda: start_recognition(lambda: active_session, stop_event), daemon=True).start()
    messagebox.showinfo("Started", f"Camera started.\nSession: {active_session.get('name')}")

def stop_btn():
    if not stop_event.is_set():
        messagebox.showinfo("Info", "Camera not active")
        return
    stop_event.clear()
    time.sleep(0.2)
    messagebox.showinfo("Stopped", "Camera stopped")

def add_btn():
    name = simpledialog.askstring("Enroll", "Enter full name:", parent=root)
    if not name: return
    threading.Thread(target=lambda: enroll_worker(name, lambda msg: root.after(0, lambda: messagebox.showinfo("Enroll", msg)) ),
                     daemon=True).start()

def create_session_btn():
    name = simpledialog.askstring("Session", "Enter session name:", parent=root)
    if not name: return
    sid = create_session(name)
    messagebox.showinfo("Session Created", f"Created session ID {sid}")

def pick_session_btn():
    rows = list_sessions()
    if not rows:
        if messagebox.askyesno("No Sessions", "Create one now?"): create_session_btn()
        return
    s = "\n".join(f"{r[0]}: {r[1]}" for r in rows)
    sel = simpledialog.askstring("Select Session", "Enter ID:\n" + s, parent=root)
    if not sel: return
    try:
        sid = int(sel.split(":")[0])
    except:
        try: sid = int(sel)
        except: messagebox.showerror("Error", "Invalid selection"); return
    row = get_session(sid)
    if not row: messagebox.showerror("Error", "Session not found"); return
    active_session["id"], active_session["name"] = row[0], row[1]
    messagebox.showinfo("Session Active", f"{row[1]} (ID {row[0]})")

def view_btn():
    rows = fetch_recent()
    if not rows:
        messagebox.showinfo("Attendance", "No records.")
        return
    txt = "\n".join(f"{p} | {d} | {s} | {t}" for (p,d,s,t) in rows)
    if len(txt) > 15000: txt = txt[:15000] + "\n...(truncated)..."
    messagebox.showinfo("Recent Attendance", txt)

def export_btn():
    start = simpledialog.askstring("Export", "Start date (YYYY-MM-DD) or empty:", parent=root)
    end = simpledialog.askstring("Export", "End date (YYYY-MM-DD) or empty:", parent=root)
    default = "attendance.xlsx" if PANDAS_OK else "attendance.csv"
    types = [("Excel", "*.xlsx"), ("CSV", "*.csv")] if PANDAS_OK else [("CSV", "*.csv")]
    path = filedialog.asksaveasfilename(title="Save export", initialfile=default, filetypes=types, defaultextension=default.split(".")[-1])
    if not path: return
    ok, err = export_file(path, start or None, end or None)
    if ok:
        if err: messagebox.showinfo("Exported", f"Done.\nNote: {err}")
        else: messagebox.showinfo("Exported", f"Saved to:\n{path}")
    else:
        messagebox.showerror("Error", err)

def exit_btn():
    stop_event.clear()
    try: root.destroy()
    except: pass

tk.Button(root, text="Start Attendance", width=30, command=start_btn).pack(pady=6)
tk.Button(root, text="Stop Attendance", width=30, command=stop_btn).pack(pady=6)
tk.Button(root, text="Add New User", width=30, command=add_btn).pack(pady=6)
tk.Button(root, text="Create Session", width=30, command=create_session_btn).pack(pady=6)
tk.Button(root, text="Start Session (Choose)", width=30, command=pick_session_btn).pack(pady=6)
tk.Button(root, text="View Attendance", width=30, command=view_btn).pack(pady=6)
tk.Button(root, text="Export Attendance", width=30, command=export_btn).pack(pady=6)
tk.Button(root, text="Exit", width=30, command=exit_btn).pack(pady=6)

if __name__ == "__main__":
    root.mainloop()