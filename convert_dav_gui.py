#!/usr/bin/env python3
"""
DAV to MP4 Converter - GUI Version
A user-friendly interface for converting Hikvision .dav files to .mp4
Works on Windows, Mac, and Linux
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import sys
import threading
from pathlib import Path
import os

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class DAVConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DAV to MP4 Converter")
        self.root.geometry("720x640")
        self.root.resizable(True, True)

        # Set colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#f0f0f0"
        self.accent_color = "#e1490f"
        self.accent_hover = "#ff5a1f"
        self.entry_bg = "#2a2a2a"
        self.log_bg = "#141414"

        self.root.configure(bg=self.bg_color)

        # Set window icon
        self._set_icon()

        # Variables
        self.input_path = None
        self.output_dir = None
        self.is_converting = False
        self.progress_bar_rect = None

        # Check FFmpeg first
        if not self._check_ffmpeg():
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is required but not installed.\n\n"
                "Mac: Run in Terminal: brew install ffmpeg\n"
                "Windows: Download from https://www.gyan.dev/ffmpeg/builds/\n"
                "Linux: Run: sudo apt-get install ffmpeg",
            )
            self.root.destroy()
            return

        self._setup_ui()

    @staticmethod
    def _asset_path(filename):
        """Resolve asset path — works both normally and inside a PyInstaller bundle."""
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS) / filename
        return Path(__file__).parent / filename

    def _load_logo(self, height):
        """Load logo.png scaled to the given height with high-quality resampling."""
        logo_path = self._asset_path("logo.png")
        if not logo_path.exists():
            return None
        try:
            if HAS_PIL:
                img = Image.open(logo_path)
                ratio = height / img.height
                new_w = int(img.width * ratio)
                img = img.resize((new_w, height), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            else:
                return tk.PhotoImage(file=str(logo_path))
        except Exception:
            return None

    def _set_icon(self):
        icon = self._load_logo(64)
        if icon:
            self._icon_ref = icon
            self.root.iconphoto(True, icon)

    @staticmethod
    def _check_ffmpeg():
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    # ── UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        # Header with logo
        header = tk.Frame(self.root, bg=self.bg_color)
        header.pack(fill=tk.X, padx=20, pady=(15, 5))

        self._header_logo = self._load_logo(48)
        if self._header_logo:
            logo_label = tk.Label(header, image=self._header_logo, bg=self.bg_color)
            logo_label.pack(side=tk.LEFT, padx=(0, 12))

        title = tk.Label(
            header,
            text="DAV to MP4 Converter",
            font=("Helvetica", 20, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
        )
        title.pack(side=tk.LEFT)

        # Separator
        tk.Frame(self.root, height=2, bg=self.accent_color).pack(
            fill=tk.X, padx=20, pady=8
        )

        # ── Input section ───────────────────────────────────────────────
        self._section_label("Select Input:")

        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=20, pady=(2, 8))

        self.input_text = tk.Entry(
            input_frame,
            font=("Helvetica", 10),
            bg=self.entry_bg,
            fg=self.fg_color,
            disabledbackground=self.entry_bg,
            disabledforeground="#999999",
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#444",
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.input_text.config(state="disabled")

        self._make_button(input_frame, "Folder", self._select_folder).pack(
            side=tk.LEFT, padx=2
        )
        self._make_button(input_frame, "File", self._select_file).pack(
            side=tk.LEFT, padx=2
        )

        # ── Output section ──────────────────────────────────────────────
        self._section_label("Output Directory (optional):")

        output_frame = tk.Frame(self.root, bg=self.bg_color)
        output_frame.pack(fill=tk.X, padx=20, pady=(2, 8))

        self.output_text = tk.Entry(
            output_frame,
            font=("Helvetica", 10),
            bg=self.entry_bg,
            fg=self.fg_color,
            disabledbackground=self.entry_bg,
            disabledforeground="#999999",
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#444",
        )
        self.output_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.output_text.config(state="disabled")

        self._make_button(output_frame, "Browse", self._select_output).pack(
            side=tk.LEFT
        )

        # Separator
        tk.Frame(self.root, height=1, bg="#444").pack(fill=tk.X, padx=20, pady=8)

        # ── Log ─────────────────────────────────────────────────────────
        self._section_label("Conversion Log:")

        self.log_output = scrolledtext.ScrolledText(
            self.root,
            height=10,
            font=("Courier", 10),
            bg=self.log_bg,
            fg="#cccccc",
            insertbackground="#cccccc",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#333",
        )
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=20, pady=(2, 8))
        self.log_output.config(state="disabled")

        # ── Progress ────────────────────────────────────────────────────
        progress_frame = tk.Frame(self.root, bg=self.bg_color)
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 6))

        self.progress_label = tk.Label(
            progress_frame,
            text="Ready",
            font=("Helvetica", 9),
            bg=self.bg_color,
            fg="#999999",
        )
        self.progress_label.pack(anchor="w")

        self.progress_bar = tk.Canvas(
            progress_frame,
            height=14,
            bg="#333333",
            highlightthickness=0,
        )
        self.progress_bar.pack(fill=tk.X, pady=(4, 0))

        # ── Bottom buttons ──────────────────────────────────────────────
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        self.convert_btn = self._make_button(
            btn_frame, "Convert", self._start_conversion, bold=True
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._make_button(btn_frame, "Clear", self._clear_log, secondary=True).pack(
            side=tk.LEFT, padx=(0, 6)
        )

        self._make_button(
            btn_frame, "Exit", self.root.quit, secondary=True
        ).pack(side=tk.LEFT)

    def _section_label(self, text):
        tk.Label(
            self.root,
            text=text,
            font=("Helvetica", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(anchor="w", padx=20)

    def _make_button(self, parent, text, command, bold=False, secondary=False):
        """Label-based button — macOS ignores bg/fg on native tk.Button."""
        bg = "#555555" if secondary else self.accent_color
        hover_bg = "#777777" if secondary else self.accent_hover

        frame = tk.Frame(parent, bg=bg, cursor="hand2")
        label = tk.Label(
            frame,
            text=text,
            bg=bg,
            fg=self.fg_color,
            font=("Helvetica", 10, "bold" if bold else "normal"),
            padx=14,
            pady=5,
        )
        label.pack()

        # Store for state toggling
        frame._btn_bg = bg
        frame._btn_hover = hover_bg
        frame._btn_label = label
        frame._btn_enabled = True

        def on_enter(_):
            if frame._btn_enabled:
                frame.config(bg=hover_bg)
                label.config(bg=hover_bg)

        def on_leave(_):
            cur_bg = frame._btn_bg if frame._btn_enabled else "#444444"
            frame.config(bg=cur_bg)
            label.config(bg=cur_bg)

        def on_click(_):
            if frame._btn_enabled:
                command()

        for widget in (frame, label):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

        # Mimic .config(state=...) for the convert button
        _orig_config = frame.config
        def _patched_config(self_=frame, **kw):
            if "state" in kw:
                if kw["state"] == "disabled":
                    self_._btn_enabled = False
                    self_.config(bg="#444444")
                    self_._btn_label.config(bg="#444444", fg="#888888")
                elif kw["state"] == "normal":
                    self_._btn_enabled = True
                    self_.config(bg=self_._btn_bg)
                    self_._btn_label.config(bg=self_._btn_bg, fg=self.fg_color)
                del kw["state"]
            if kw:
                _orig_config(**kw)
        frame.config = _patched_config

        return frame

    # ── Logging / progress (always called on main thread) ───────────────

    def _log(self, message):
        self.log_output.config(state="normal")
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)
        self.log_output.config(state="disabled")

    def _update_progress(self, percent):
        self.progress_label.config(text=f"Progress: {percent}%")
        self.progress_bar.delete("bar")
        width = self.progress_bar.winfo_width()
        if width > 1:
            fill = max(0, (width * percent / 100))
            self.progress_bar.create_rectangle(
                0, 0, fill, 14, fill=self.accent_color, outline="", tags="bar"
            )

    # Thread-safe wrappers — schedule on the main thread
    def _log_safe(self, message):
        self.root.after(0, self._log, message)

    def _progress_safe(self, percent):
        self.root.after(0, self._update_progress, percent)

    # ── File pickers ────────────────────────────────────────────────────

    def _set_entry(self, entry, value):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.config(state="disabled")

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select folder with .dav files")
        if folder:
            self.input_path = Path(folder)
            self._set_entry(self.input_text, str(self.input_path))
            self._log(f"Selected folder: {self.input_path.name}")

    def _select_file(self):
        file = filedialog.askopenfilename(
            title="Select a .dav file",
            filetypes=[("DAV Files", "*.dav"), ("All Files", "*.*")],
        )
        if file:
            self.input_path = Path(file)
            self._set_entry(self.input_text, str(self.input_path))
            self._log(f"Selected file: {self.input_path.name}")

    def _select_output(self):
        folder = filedialog.askdirectory(title="Select output directory")
        if folder:
            self.output_dir = Path(folder)
            self._set_entry(self.output_text, str(self.output_dir))
            self._log(f"Output directory: {self.output_dir.name}")

    # ── Conversion ──────────────────────────────────────────────────────

    def _convert_single(self, input_path: Path, output_path: Path) -> bool:
        self._log_safe(f"Converting: {input_path.name} ...")

        # Try stream copy first (fast)
        cmd = ["ffmpeg", "-y", "-i", str(input_path), "-c", "copy", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            self._log_safe("  Stream copy failed, re-encoding ...")
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                str(output_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            self._log_safe(f"  Done: {input_path.name} ({size_mb:.1f} MB)")
            return True

        err = (result.stderr.splitlines()[-1] if result.stderr else "Unknown error")
        self._log_safe(f"  FAILED: {input_path.name} — {err}")
        return False

    def _collect_dav_files(self):
        if self.input_path.is_file():
            if self.input_path.suffix.lower() == ".dav":
                return [self.input_path], self.output_dir or self.input_path.parent
            messagebox.showerror("Invalid Input", f"Not a .dav file: {self.input_path}")
            return [], None

        if self.input_path.is_dir():
            # Case-insensitive, deduplicated
            seen = set()
            files = []
            for f in sorted(self.input_path.iterdir()):
                if f.suffix.lower() == ".dav" and f.name not in seen:
                    seen.add(f.name)
                    files.append(f)
            return files, self.output_dir or self.input_path

        messagebox.showerror("Invalid Input", f"Path not found: {self.input_path}")
        return [], None

    def _conversion_thread(self, dav_files, output_dir):
        success = failed = 0
        total = len(dav_files)

        self._log_safe(f"\n{'=' * 50}")
        self._log_safe(f"Starting conversion — {total} file(s)")
        self._log_safe(f"Output: {output_dir}")
        self._log_safe(f"{'=' * 50}\n")

        for i, dav in enumerate(dav_files, 1):
            out = output_dir / (dav.stem + ".mp4")
            if self._convert_single(dav, out):
                success += 1
            else:
                failed += 1
            self._progress_safe(int(i / total * 100))

        self._log_safe(f"\n{'=' * 50}")
        self._log_safe(f"Converted: {success}   Failed: {failed}")
        self._log_safe(f"{'=' * 50}")

        self.root.after(0, lambda: self.convert_btn.config(state="normal"))
        self.is_converting = False

    def _start_conversion(self):
        if self.is_converting:
            return
        if not self.input_path:
            messagebox.showwarning("No Input", "Please select a .dav file or folder.")
            return

        dav_files, output_dir = self._collect_dav_files()
        if not dav_files:
            if output_dir is not None:
                messagebox.showwarning("No Files", f"No .dav files found in: {self.input_path}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        self.is_converting = True
        self.convert_btn.config(state="disabled")
        self._update_progress(0)

        threading.Thread(
            target=self._conversion_thread,
            args=(dav_files, output_dir),
            daemon=True,
        ).start()

    def _clear_log(self):
        self.log_output.config(state="normal")
        self.log_output.delete(1.0, tk.END)
        self.log_output.config(state="disabled")
        self.progress_bar.delete("bar")
        self.progress_label.config(text="Ready")


if __name__ == "__main__":
    root = tk.Tk()
    app = DAVConverterGUI(root)
    root.mainloop()
