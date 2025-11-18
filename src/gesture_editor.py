# File: src/gesture_editor.py
# advanced editor window, modern look, save/load functionality.
import customtkinter as ctk
from tkinter import ttk
from typing import Dict
import json
import os

class GestureEditor(ctk.CTkToplevel):
    """rich gesture editor window to edit mappings and test actions."""
    def __init__(self, parent, mapper, on_save=None):
        super().__init__(parent)
        self.title("Swipe — Gesture Editor")
        self.geometry("800x520")
        self.mapper = mapper
        self.on_save = on_save

        self.configure(fg_color="#11151a")  # dark background

        header = ctk.CTkLabel(self, text="Gesture Editor", font=("Helvetica", 20, "bold"))
        header.pack(pady=(12,6))

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        # left: list, right: editor
        self.gestures = list(self.mapper.map.keys())
        self.vars = {}
        left = ctk.CTkFrame(frame)
        left.grid(row=0, column=0, sticky="ns", padx=(8,12), pady=8)
        right = ctk.CTkFrame(frame)
        right.grid(row=0, column=1, sticky="nsew", padx=(12,8), pady=8)
        frame.grid_columnconfigure(1, weight=1)

        # listbox of gestures
        self.listbox = ctk.CTkScrollableFrame(left, width=180)
        self.listbox.pack(fill="y", expand=True)
        for g in self.gestures:
            b = ctk.CTkButton(self.listbox, text=g, command=lambda gg=g: self.select(gg))
            b.pack(fill="x", pady=4, padx=6)

        # editor fields
        self.selected = None
        self.action_entry = ctk.CTkEntry(right, placeholder_text="action (e.g. media_play_pause)")
        self.action_entry.pack(pady=(12,6), padx=8, fill="x")
        self.hint = ctk.CTkLabel(right, text="Examples: media_play_pause, media_next, win+d, volume up, left_click", wraplength=380)
        self.hint.pack(padx=8, pady=6)

        btn_frame = ctk.CTkFrame(right)
        btn_frame.pack(pady=8, padx=8, fill="x")
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=self.save)
        save_btn.pack(side="left", padx=6)
        test_btn = ctk.CTkButton(btn_frame, text="Test", command=self.test)
        test_btn.pack(side="left", padx=6)
        reset_btn = ctk.CTkButton(btn_frame, text="Reset Defaults", command=self.reset_defaults)
        reset_btn.pack(side="left", padx=6)

        self.status = ctk.CTkLabel(self, text="", fg_color=None)
        self.status.pack(pady=(6,12))

        # initialize
        first = self.gestures[0] if self.gestures else None
        if first: self.select(first)

    def select(self, gesture):
        """populate editor fields for gesture."""
        self.selected = gesture
        action = self.mapper.get_action(gesture)
        self.action_entry.delete(0, "end")
        self.action_entry.insert(0, action)
        self.status.configure(text=f"Editing: {gesture}")

    def save(self):
        """save current entry to mapper and update file."""
        if not self.selected:
            return
        action = self.action_entry.get().strip()
        if action == "":
            action = "noop"
        self.mapper.set_mapping(self.selected, action)
        self.status.configure(text=f"Saved mapping for {self.selected}")
        if self.on_save:
            self.on_save()

    def test(self):
        """execute the mapped action once for testing."""
        if not self.selected:
            return
        self.mapper.simulate_action(self.selected)
        self.status.configure(text=f"Tested: {self.selected}")

    def reset_defaults(self):
        """reset all mappings to defaults and save."""
        # overwrite with defaults by re-saving defaults in mapper
        from gesture_mapper import DEFAULT_MAP
        for k, v in DEFAULT_MAP.items():
            self.mapper.set_mapping(k, v)
        self.status.configure(text="Reset to defaults")
        if self.on_save:
            self.on_save()
