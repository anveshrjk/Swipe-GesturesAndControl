# ui.py
import cv2
import customtkinter as ctk
from PIL import Image
from threading import Thread
from gestures import GestureController
from utils import FPSCounter
import time


class SwipeApp(ctk.CTk):
    def __init__(self, camera_index=0):
        super().__init__()

        self.title("SWIPE Gesture Control")
        self.geometry("1050x650")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # Layout frames
        self.left_frame = ctk.CTkFrame(self, width=700, height=600, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=(20, 10), pady=20)

        self.right_frame = ctk.CTkFrame(self, width=300, height=600, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=(10, 20), pady=20)

        self.bottom_bar = ctk.CTkFrame(self, height=40, fg_color="#e8e8e8", corner_radius=0)
        self.bottom_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Camera and gesture modules
        self.cap = cv2.VideoCapture(camera_index)
        self.gesture_controller = GestureController()
        self.fps_counter = FPSCounter()
        self.running = True

        # Left frame: Camera feed
        self.video_label = ctk.CTkLabel(self.left_frame, text="")
        self.video_label.pack(padx=10, pady=10, fill="both", expand=True)

        # Right frame: Gesture status
        self.mode_label = ctk.CTkLabel(self.right_frame, text="Mode: Idle", font=("Poppins", 20))
        self.mode_label.pack(pady=(40, 20))

        self.status_label = ctk.CTkLabel(self.right_frame, text="No gesture detected", font=("Poppins", 16))
        self.status_label.pack(pady=10)

        # Bottom bar: FPS
        self.fps_label = ctk.CTkLabel(self.bottom_bar, text="FPS: --", font=("Poppins", 14))
        self.fps_label.pack(side="right", padx=15, pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start threads
        self.update_thread = Thread(target=self.update_camera_feed, daemon=True)
        self.update_thread.start()

    def update_camera_feed(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frame, mode = self.gesture_controller.detect(frame)
            self.mode_label.configure(text=f"Mode: {mode.capitalize()}")

            # Update gesture feedback text
            if mode == "volume_active":
                self.status_label.configure(text="Volume Mode Active (Index Up/Down)")
            elif mode == "idle":
                self.status_label.configure(text="No gesture detected")

            # Convert OpenCV frame to ImageTk
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ctk.CTkImage(light_image=img, size=(680, 500))
            self.video_label.configure(image=img)
            self.video_label.image = img

            # FPS calculation
            fps = self.fps_counter.update()
            self.fps_label.configure(text=f"FPS: {fps}")

            time.sleep(0.01)

    def on_close(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()


if __name__ == "__main__":
    app = SwipeApp()
    app.mainloop()
