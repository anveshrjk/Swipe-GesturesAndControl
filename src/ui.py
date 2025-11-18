# File: src/ui.py
# main UI: preview, controls, debug overlay, button to open editor.
import customtkinter as ctk
from PIL import Image, ImageTk
import queue
import cv2
import warnings
import os

from camera import CameraThread
from processing import ProcessingThread
from gesture_mapper import GestureMapper
from gesture_editor import GestureEditor

warnings.filterwarnings("ignore")

class App(ctk.CTk):
    """main window: preview + controls + open editor window."""
    def __init__(self):
        super().__init__()
        self.title("Swipe")
        self.geometry("1400x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # queues and mapper
        self.raw_frame_queue = queue.Queue(maxsize=2)
        self.results_queue = queue.Queue(maxsize=2)
        self.mapper = GestureMapper()

        # UI frames
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=16, pady=(12,6))
        title = ctk.CTkLabel(top, text="Swipe", font=("Helvetica", 24, "bold"))
        title.pack(side="left", padx=6)

        editor_btn = ctk.CTkButton(top, text="Open Gesture Editor", command=self.open_editor)
        editor_btn.pack(side="right", padx=6)

        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=16, pady=6)

        # left: preview; right: controls
        preview_frame = ctk.CTkFrame(main)
        preview_frame.grid(row=0, column=0, padx=(12,8), pady=8, sticky="nsew")
        control_frame = ctk.CTkFrame(main, width=360)
        control_frame.grid(row=0, column=1, padx=(8,12), pady=8, sticky="ns")
        main.grid_columnconfigure(0, weight=1)

        # preview label
        self.preview_w, self.preview_h = 960, 540
        self.video_label = ctk.CTkLabel(preview_frame, text="")
        self.video_label.pack(padx=12, pady=12)

        # debug overlay label top-left small
        self.debug_var = ctk.StringVar(value="No gesture")
        self.debug_label = ctk.CTkLabel(preview_frame, textvariable=self.debug_var, fg_color="#202a3a")
        self.debug_label.place(x=10, y=10)

        # control widgets
        self.enable_var = ctk.BooleanVar(value=True)
        enable_switch = ctk.CTkSwitch(control_frame, text="Enable Gestures", variable=self.enable_var, command=self.apply_settings)
        enable_switch.pack(pady=(12,10))

        ctk.CTkLabel(control_frame, text="Swipe Sensitivity").pack(pady=(8,4))
        self.sens_var = ctk.DoubleVar(value=60)
        sens_slider = ctk.CTkSlider(control_frame, from_=20, to=150, number_of_steps=130, variable=self.sens_var, command=lambda v: self.apply_settings())
        sens_slider.pack(padx=12, pady=(0,12))

        ctk.CTkLabel(control_frame, text="Vertical Swipe Sensitivity").pack(pady=(8,4))
        self.vsens_var = ctk.DoubleVar(value=40)
        vsens_slider = ctk.CTkSlider(control_frame, from_=10, to=120, number_of_steps=110, variable=self.vsens_var, command=lambda v: self.apply_settings())
        vsens_slider.pack(padx=12, pady=(0,12))

        ctk.CTkLabel(control_frame, text="Palm Close Threshold").pack(pady=(8,4))
        self.close_var = ctk.DoubleVar(value=40)
        close_slider = ctk.CTkSlider(control_frame, from_=15, to=120, number_of_steps=105, variable=self.close_var, command=lambda v: self.apply_settings())
        close_slider.pack(padx=12, pady=(0,12))

        ctk.CTkLabel(control_frame, text="Cooldown (s)").pack(pady=(8,4))
        self.cool_var = ctk.DoubleVar(value=0.7)
        cool_slider = ctk.CTkSlider(control_frame, from_=0.1, to=2.0, number_of_steps=38, variable=self.cool_var, command=lambda v: self.apply_settings())
        cool_slider.pack(padx=12, pady=(0,12))

        # status
        self.fps_var = ctk.StringVar(value="FPS: 0")
        fps_label = ctk.CTkLabel(control_frame, textvariable=self.fps_var)
        fps_label.pack(pady=(16,6))

        # threads
        self.camera_thread = CameraThread(self.raw_frame_queue, width=1280, height=720)
        self.processing_thread = ProcessingThread(self.raw_frame_queue, self.results_queue, self.mapper, preview_size=(self.preview_w, self.preview_h))

        self.camera_thread.start()
        self.processing_thread.start()
        self.apply_settings()

        self.update_frame()

    def apply_settings(self):
        """push UI settings to processing thread."""
        self.processing_thread.gesture_enabled = self.enable_var.get()
        self.processing_thread.swipe_sensitivity = int(self.sens_var.get())
        self.processing_thread.swipe_vertical_sensitivity = int(self.vsens_var.get())
        self.processing_thread.close_threshold = int(self.close_var.get())
        self.processing_thread.cooldown_sec = float(self.cool_var.get())

    def open_editor(self):
        """open gesture editor window."""
        def on_save():
            # mapper saved; nothing else needed now
            pass
        GestureEditor(self, self.mapper, on_save=on_save)

    def update_frame(self):
        """pull processed frames and show them."""
        try:
            frame, fps, gesture = self.results_queue.get_nowait()
            self.fps_var.set(f"FPS: {fps}")
            self.debug_var.set(gesture)
        except queue.Empty:
            self.after(15, self.update_frame)
            return

        # resize and show
        frame = cv2.resize(frame, (self.preview_w, self.preview_h))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(frame_rgb)
        tk_img = ImageTk.PhotoImage(pil)
        self.video_label.img = tk_img
        self.video_label.configure(image=tk_img)

        self.after(15, self.update_frame)

    def on_closing(self):
        self.camera_thread.stop()
        self.processing_thread.stop()
        self.destroy()
