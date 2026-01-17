import json
import queue
import threading
from datetime import datetime
from pathlib import Path
from tkinter import Toplevel, StringVar, BooleanVar, Text, END, ttk, filedialog, messagebox

import soundfile as sf

from .api_client import transcribe_audio
from .audio import AudioRecorder
from .settings import AppSettings, load_settings, save_settings, APP_DIR


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Lemonfox Transkriptor")

        self.settings = load_settings()
        self.recorder = AudioRecorder()
        self.task_queue = queue.Queue()

        self.status_var = StringVar(value="Ready")
        self.toggle_active = False

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        self.root.minsize(780, 520)
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Subtle.TLabel", foreground="#666666")
        style.configure("Section.TLabelframe", padding=10)

        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Lemonfox Transkriptor", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="Record, transcribe, and save.", style="Subtle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        ttk.Button(header, text="Settings", command=self.open_settings).grid(
            row=0, column=1, rowspan=2, sticky="e"
        )

        left = ttk.Frame(container)
        left.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        container.rowconfigure(1, weight=1)
        container.columnconfigure(0, weight=1)

        controls = ttk.Labelframe(left, text="Controls", style="Section.TLabelframe")
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)

        self.record_button = ttk.Button(controls, text="Hold to Record")
        self.record_button.grid(row=0, column=0, sticky="w")
        self.record_button.bind("<ButtonPress-1>", self.on_record_press)
        self.record_button.bind("<ButtonRelease-1>", self.on_record_release)

        self.toggle_button = ttk.Button(controls, text="Click to Start", command=self.on_toggle_click)
        self.toggle_button.grid(row=0, column=1, padx=(10, 0), sticky="w")

        ttk.Button(controls, text="Transcribe File", command=self.transcribe_file_dialog).grid(
            row=1, column=0, pady=(10, 0), sticky="w"
        )
        ttk.Button(controls, text="Transcribe URL", command=self.transcribe_url_dialog).grid(
            row=1, column=1, pady=(10, 0), sticky="w", padx=(10, 0)
        )

        output_frame = ttk.Labelframe(left, text="Transcript", style="Section.TLabelframe")
        output_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        left.rowconfigure(1, weight=1)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output = Text(output_frame, height=18, wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)

        status = ttk.Label(container, textvariable=self.status_var, anchor="w", style="Subtle.TLabel")
        status.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def on_record_press(self, event):
        if self.toggle_active:
            return
        self.start_recording()

    def on_record_release(self, event):
        if self.toggle_active:
            return
        self.stop_recording()

    def on_toggle_click(self):
        if self.recorder.recording:
            self.stop_recording()
            self.toggle_active = False
            self.toggle_button.configure(text="Click to Start")
        else:
            self.toggle_active = True
            self.toggle_button.configure(text="Click to Stop")
            self.start_recording()

    def start_recording(self):
        if self.recorder.recording:
            return
        try:
            sample_rate = int(self.settings.sample_rate)
            channels = int(self.settings.channels)
        except ValueError:
            messagebox.showerror("Invalid settings", "Sample rate and channels must be numbers.")
            return
        self.recorder.start(sample_rate, channels)
        self.status_var.set("Recording...")

    def stop_recording(self):
        if not self.recorder.recording:
            return
        audio = self.recorder.stop()
        self.status_var.set("Processing audio...")
        if audio is None:
            self.status_var.set("No audio captured.")
            return
        audio_path = self.save_audio(audio)
        self.queue_transcription(audio_path, source_type="file")

    def save_audio(self, audio):
        audio_dir = self.resolve_dir(self.settings.audio_dir, APP_DIR / "audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = audio_dir / f"recording_{timestamp}.wav"
        sf.write(audio_path, audio, int(self.settings.sample_rate))
        return audio_path

    def transcribe_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.opus *.webm *.mp4 *.mov *.mpeg"), ("All files", "*.*")],
        )
        if not path:
            return
        audio_path = Path(path)
        stored_path = self.copy_audio_file(audio_path)
        self.queue_transcription(stored_path, source_type="file")

    def transcribe_url_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Transcribe URL")
        dialog.resizable(False, False)
        ttk.Label(dialog, text="Public URL").grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")
        url_var = StringVar()
        entry = ttk.Entry(dialog, textvariable=url_var, width=60)
        entry.grid(row=1, column=0, padx=10, pady=6)
        entry.focus_set()

        def submit():
            url = url_var.get().strip()
            if not url:
                messagebox.showerror("Missing URL", "Please enter a URL.")
                return
            dialog.destroy()
            self.queue_transcription(url, source_type="url")

        ttk.Button(dialog, text="Transcribe", command=submit).grid(
            row=2, column=0, padx=10, pady=(6, 10), sticky="e"
        )

    def copy_audio_file(self, audio_path: Path):
        audio_dir = self.resolve_dir(self.settings.audio_dir, APP_DIR / "audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = audio_dir / f"{audio_path.stem}_{timestamp}{audio_path.suffix}"
        if audio_path.resolve() != target.resolve():
            target.write_bytes(audio_path.read_bytes())
        return target

    def queue_transcription(self, source, source_type="file"):
        if not self.settings.api_token:
            messagebox.showerror("Missing token", "Set your API token in Settings.")
            self.status_var.set("Missing token.")
            return
        self.status_var.set("Sending to API...")
        thread = threading.Thread(
            target=self._transcribe_worker,
            args=(source, source_type),
            daemon=True,
        )
        thread.start()

    def _transcribe_worker(self, source, source_type):
        try:
            payload, response_text = transcribe_audio(self.settings, source, source_type)
            display_text = self.extract_display_text(payload, response_text)
            json_path = self.save_transcript(payload, response_text, display_text)
            self.task_queue.put(("success", display_text, json_path))
        except Exception as exc:
            self.task_queue.put(("error", str(exc), None))

    def extract_display_text(self, payload, response_text):
        if payload is None:
            return response_text or ""
        if self.settings.response_format == "json":
            return payload.get("text", "")
        if self.settings.response_format == "verbose_json":
            segments = payload.get("segments", [])
            lines = []
            for seg in segments:
                start = seg.get("start")
                end = seg.get("end")
                speaker = seg.get("speaker")
                text = seg.get("text", "")
                ts = ""
                if start is not None and end is not None:
                    ts = f"[{start:>6.2f}-{end:>6.2f}]"
                speaker_part = f"{speaker}: " if speaker else ""
                line = f"{ts} {speaker_part}{text}".strip()
                if line:
                    lines.append(line)
            if lines:
                return "\n".join(lines)
            return payload.get("text", "")
        return ""

    def save_transcript(self, payload, response_text, display_text):
        text_dir = self.resolve_dir(self.settings.text_dir, APP_DIR / "text")
        text_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result = {
            "saved_at": timestamp,
            "response_format": self.settings.response_format,
            "data": payload,
            "text": display_text or response_text,
        }
        json_path = text_dir / f"transcript_{timestamp}.json"
        json_path.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
        return json_path

    def resolve_dir(self, path_value, fallback):
        if not path_value:
            return Path(fallback)
        return Path(path_value)

    def _poll_queue(self):
        try:
            while True:
                kind, message, path = self.task_queue.get_nowait()
                if kind == "success":
                    self.output.delete(1.0, END)
                    self.output.insert(END, message)
                    self.status_var.set(f"Done. Saved to {path}")
                else:
                    self.status_var.set(f"Error: {message}")
        except queue.Empty:
            pass
        self.root.after(200, self._poll_queue)

    def open_settings(self):
        dialog = Toplevel(self.root)
        dialog.title("Settings")
        dialog.resizable(False, False)
        dialog.columnconfigure(1, weight=1)

        row = 0

        def add_entry_row(label_text, var, show=None):
            nonlocal row
            ttk.Label(dialog, text=label_text).grid(row=row, column=0, padx=10, pady=4, sticky="w")
            entry_kwargs = {"textvariable": var, "width": 50}
            if show is not None:
                entry_kwargs["show"] = show
            entry = ttk.Entry(dialog, **entry_kwargs)
            entry.grid(row=row, column=1, padx=10, pady=4, sticky="ew")
            row += 1
            return entry

        def add_combo_row(label_text, var, values, state="readonly", width=47):
            nonlocal row
            ttk.Label(dialog, text=label_text).grid(row=row, column=0, padx=10, pady=4, sticky="w")
            combo = ttk.Combobox(dialog, textvariable=var, values=values, width=width, state=state)
            combo.grid(row=row, column=1, padx=10, pady=4, sticky="ew")
            row += 1
            return combo

        def add_check_row(label_text, var, command=None):
            nonlocal row
            ttk.Label(dialog, text=label_text).grid(row=row, column=0, padx=10, pady=4, sticky="w")
            check = ttk.Checkbutton(dialog, variable=var, command=command)
            check.grid(row=row, column=1, padx=10, pady=4, sticky="w")
            row += 1
            return check

        def add_dir_row(label_text, var):
            nonlocal row
            ttk.Label(dialog, text=label_text).grid(row=row, column=0, padx=10, pady=4, sticky="w")
            entry = ttk.Entry(dialog, textvariable=var, width=50)
            entry.grid(row=row, column=1, padx=(10, 0), pady=4, sticky="ew")
            ttk.Button(dialog, text="Browse", command=lambda: self.browse_dir(var)).grid(
                row=row, column=2, padx=6, pady=4
            )
            row += 1
            return entry

        api_token = StringVar(value=self.settings.api_token)
        api_base = StringVar(value=self.settings.api_base)
        language = StringVar(value=self.settings.language)
        response_format = StringVar(value=self.settings.response_format)
        prompt = StringVar(value=self.settings.prompt)
        translate = BooleanVar(value=self.settings.translate)
        speaker_labels = BooleanVar(value=self.settings.speaker_labels)
        min_speakers = StringVar(value=self.settings.min_speakers)
        max_speakers = StringVar(value=self.settings.max_speakers)
        word_timestamps = BooleanVar(value=self.settings.word_timestamps)
        callback_url = StringVar(value=self.settings.callback_url)
        audio_dir = StringVar(value=self.settings.audio_dir)
        text_dir = StringVar(value=self.settings.text_dir)
        sample_rate = StringVar(value=self.settings.sample_rate)
        channels = StringVar(value=self.settings.channels)

        add_entry_row("API token", api_token, show="*")

        add_combo_row(
            "API base",
            api_base,
            ["https://api.lemonfox.ai", "https://eu-api.lemonfox.ai"],
            state="readonly",
        )

        language_values = [
            "english",
            "german",
            "spanish",
            "french",
            "italian",
            "dutch",
            "portuguese",
            "russian",
            "polish",
            "turkish",
            "arabic",
            "hindi",
            "japanese",
            "korean",
            "chinese",
        ]
        add_combo_row("Language", language, language_values, state="normal")

        response_combo = add_combo_row(
            "Response format",
            response_format,
            ["json", "text", "srt", "vtt", "verbose_json"],
            state="readonly",
        )

        ttk.Label(
            dialog,
            text="Speaker labels and word timestamps require verbose_json.",
            foreground="#666666",
        ).grid(row=row, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="w")
        row += 1

        add_entry_row("Prompt", prompt)

        add_check_row("Translate to English", translate)
        speaker_check = add_check_row("Speaker labels", speaker_labels)
        min_entry = add_entry_row("Min speakers", min_speakers)
        max_entry = add_entry_row("Max speakers", max_speakers)
        word_check = add_check_row("Word timestamps", word_timestamps)
        add_entry_row("Callback URL", callback_url)

        add_dir_row("Audio folder", audio_dir)
        add_dir_row("Text folder", text_dir)

        add_combo_row("Sample rate", sample_rate, ["8000", "16000", "22050", "44100", "48000"], state="normal")
        add_combo_row("Channels", channels, ["1", "2"], state="normal")

        def update_speaker_fields():
            enabled = speaker_labels.get() and response_format.get().strip() == "verbose_json"
            state = "normal" if enabled else "disabled"
            min_entry.configure(state=state)
            max_entry.configure(state=state)

        def update_verbose_fields():
            is_verbose = response_format.get().strip() == "verbose_json"
            speaker_check.configure(state="normal" if is_verbose else "disabled")
            word_check.configure(state="normal" if is_verbose else "disabled")
            if not is_verbose:
                speaker_labels.set(False)
                word_timestamps.set(False)
            update_speaker_fields()

        speaker_check.configure(command=update_speaker_fields)
        response_combo.bind("<<ComboboxSelected>>", lambda event: update_verbose_fields())
        update_verbose_fields()

        def save():
            self.settings = AppSettings(
                api_token=api_token.get().strip(),
                api_base=api_base.get().strip(),
                language=language.get().strip(),
                response_format=response_format.get().strip(),
                prompt=prompt.get().strip(),
                translate=translate.get(),
                speaker_labels=speaker_labels.get(),
                min_speakers=min_speakers.get().strip(),
                max_speakers=max_speakers.get().strip(),
                word_timestamps=word_timestamps.get(),
                callback_url=callback_url.get().strip(),
                audio_dir=audio_dir.get().strip(),
                text_dir=text_dir.get().strip(),
                sample_rate=sample_rate.get().strip(),
                channels=channels.get().strip(),
            )
            save_settings(self.settings)
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(
            row=row, column=2, padx=10, pady=10, sticky="e"
        )

    def browse_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)
