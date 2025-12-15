import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
import numpy as np
import mss
import sounddevice as sd
import soundfile as sf

# --- Globals ---
recording = False
mic_on = True
video_source = "webcam"  # webcam or screen
video_quality = (640, 480)
fps = 20
audio_frames = []

# --- Audio callback ---
def audio_callback(indata, frames, time_info, status):
    if mic_on and recording:
        audio_frames.append(indata.copy())

# --- Recording thread ---
def record():
    global recording, audio_frames
    audio_frames = []

    # Start audio stream
    stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=44100)
    stream.start()

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, fps, video_quality)

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        cap = cv2.VideoCapture(0)

        while recording:
            if video_source == "webcam":
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, video_quality)
            else:  # screen capture
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.resize(frame, video_quality)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            out.write(frame)
            cv2.imshow("Preview", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    stream.stop()

    # Save audio
    if mic_on and audio_frames:
        audio_data = np.concatenate(audio_frames)
        sf.write('audio.wav', audio_data, 44100)

    messagebox.showinfo("Recording", "Recording saved as output.avi and audio.wav")

# --- GUI actions ---
def toggle_record():
    global recording
    if not recording:
        recording = True
        threading.Thread(target=record, daemon=True).start()
        record_btn.config(text="Stop Recording")
    else:
        recording = False
        record_btn.config(text="Start Recording")

def toggle_mic():
    global mic_on
    mic_on = not mic_on
    mic_btn.config(text="🎤 On" if mic_on else "🎤 Off")

def open_settings():
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings")
    settings_win.geometry("250x150")

    tk.Label(settings_win, text="Video Source:").pack()
    source_var = tk.StringVar(value=video_source)
    ttk.Combobox(settings_win, textvariable=source_var, values=["webcam", "screen"]).pack()

    tk.Label(settings_win, text="Resolution:").pack()
    res_var = tk.StringVar(value=f"{video_quality[0]}x{video_quality[1]}")
    ttk.Combobox(settings_win, textvariable=res_var, values=["640x480", "1280x720", "1920x1080"]).pack()

    def save_settings():
        global video_source, video_quality
        video_source = source_var.get()
        w, h = map(int, res_var.get().split("x"))
        video_quality = (w, h)
        settings_win.destroy()

    tk.Button(settings_win, text="Save", command=save_settings).pack(pady=10)

# --- GUI Layout ---
root = tk.Tk()
root.title("Mini OBS")
root.geometry("800x500")

# Left Panel - Scenes
left_frame = tk.Frame(root, width=150, bg="#2e2e2e")
left_frame.pack(side="left", fill="y")
tk.Label(left_frame, text="Scenes", bg="#2e2e2e", fg="white").pack(pady=5)
scenes_list = tk.Listbox(left_frame)
scenes_list.pack(expand=True, fill="both", padx=5, pady=5)
scenes_list.insert(tk.END, "Scene 1")

# Middle Panel - Sources
middle_frame = tk.Frame(root, width=150, bg="#3e3e3e")
middle_frame.pack(side="left", fill="y")
tk.Label(middle_frame, text="Sources", bg="#3e3e3e", fg="white").pack(pady=5)
sources_list = tk.Listbox(middle_frame)
sources_list.pack(expand=True, fill="both", padx=5, pady=5)
sources_list.insert(tk.END, "Webcam")
sources_list.insert(tk.END, "Screen")

# Right Panel - Audio Mixer + Controls
right_frame = tk.Frame(root, width=150, bg="#2e2e2e")
right_frame.pack(side="right", fill="y")
tk.Label(right_frame, text="Audio Mixer", bg="#2e2e2e", fg="white").pack(pady=5)

mic_btn = tk.Button(right_frame, text="🎤 On", command=toggle_mic)
mic_btn.pack(pady=10)

tk.Label(right_frame, text="Controls", bg="#2e2e2e", fg="white").pack(pady=5)
record_btn = tk.Button(right_frame, text="Start Recording", command=toggle_record)
record_btn.pack(pady=5)
settings_btn = tk.Button(right_frame, text="Settings", command=open_settings)
settings_btn.pack(pady=5)

# Main area - Preview placeholder
main_frame = tk.Frame(root, bg="black")
main_frame.pack(expand=True, fill="both")

tk.Label(main_frame, text="Preview will open in separate window", bg="black", fg="white").pack(expand=True)

root.mainloop()
