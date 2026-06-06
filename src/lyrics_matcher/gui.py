"""Lyrics Matcher GUI application with multi-provider search."""

import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor

from .audio import (
    get_metadata,
    is_supported_audio,
    save_lyrics_to_file,
    write_lyrics_to_tag,
    SUPPORTED_FORMATS,
    LyricsFormat,
    convert_lrc_to_srt,
    convert_lrc_to_ass,
)
from .provider import (
    MultiProvider,
    LyricTrack,
    convert_to_enhanced_lrc,
)


class LyricsMatcherGUI:
    """Main GUI application for lyrics matching."""

    def __init__(self):
        self.provider = MultiProvider(timeout=15, max_workers=4)
        self.selected_files: List[Path] = []
        self.search_results: List[Tuple[Path, LyricTrack]] = []
        self.current_lyrics: Optional[LyricTrack] = None
        self.current_format = tk.StringVar(value="lrc")

        self.root = tk.Tk()
        self.root.title("Lyrics Matcher v0.2")
        self.root.geometry("900x700")

        self._create_widgets()

    def _create_widgets(self):
        """Create GUI widgets."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(
            btn_frame,
            text="Select Files",
            command=self._select_files,
        ).grid(row=0, column=0, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Select Folder",
            command=self._select_folder,
        ).grid(row=0, column=1, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Search Lyrics",
            command=self._search_lyrics,
        ).grid(row=0, column=2, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Save to File",
            command=self._save_to_file,
        ).grid(row=0, column=3, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Write to Tag",
            command=self._write_to_tag,
        ).grid(row=0, column=4, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="Clear",
            command=self._clear_all,
        ).grid(row=0, column=5)

        format_frame = ttk.LabelFrame(btn_frame, text="Format", padding="5")
        format_frame.grid(row=0, column=6, padx=(10, 0))

        ttk.Radiobutton(
            format_frame,
            text="LRC",
            variable=self.current_format,
            value="lrc",
        ).grid(row=0, column=0, padx=(0, 5))

        ttk.Radiobutton(
            format_frame,
            text="Enhanced",
            variable=self.current_format,
            value="enhanced",
        ).grid(row=0, column=1, padx=(0, 5))

        ttk.Radiobutton(
            format_frame,
            text="SRT",
            variable=self.current_format,
            value="srt",
        ).grid(row=0, column=2, padx=(0, 5))

        ttk.Radiobutton(
            format_frame,
            text="ASS",
            variable=self.current_format,
            value="ass",
        ).grid(row=0, column=3)

        self.status_var = tk.StringVar(value="Ready - Select files or folder to begin")
        ttk.Label(main_frame, textvariable=self.status_var).grid(
            row=1, column=0, sticky="w", pady=(0, 5)
        )

        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        file_label = ttk.Label(list_frame, text="Selected Files:")
        file_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.file_listbox = tk.Listbox(list_frame, height=6)
        self.file_listbox.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        results_frame = ttk.LabelFrame(main_frame, text="Search Results (Multi-Provider)", padding="5")
        results_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.results_listbox = tk.Listbox(results_frame, height=6)
        self.results_listbox.grid(row=0, column=0, sticky="ew")
        self.results_listbox.bind("<<ListboxSelect>>", self._on_result_select)

        scrollbar2 = ttk.Scrollbar(results_frame, orient="vertical")
        scrollbar2.config(command=self.results_listbox.yview)
        scrollbar2.grid(row=0, column=1, sticky="ns")
        self.results_listbox.config(yscrollcommand=scrollbar2.set)

        lyrics_frame = ttk.LabelFrame(main_frame, text="Lyrics Preview", padding="5")
        lyrics_frame.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        lyrics_frame.columnconfigure(0, weight=1)
        lyrics_frame.rowconfigure(0, weight=1)

        self.lyrics_text = tk.Text(lyrics_frame, height=10, wrap="word")
        self.lyrics_text.grid(row=0, column=0, sticky="nsew")

        scrollbar3 = ttk.Scrollbar(lyrics_frame, orient="vertical")
        scrollbar3.config(command=self.lyrics_text.yview)
        scrollbar3.grid(row=0, column=1, sticky="ns")
        self.lyrics_text.config(yscrollcommand=scrollbar3.set)

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _select_files(self):
        """Open file dialog to select audio files."""
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[
                ("Audio Files", " ".join(f"*{ext}" for ext in SUPPORTED_FORMATS)),
                ("All Files", "*.*"),
            ],
        )
        if files:
            self.selected_files = [Path(f) for f in files]
            self._update_file_list()

    def _select_folder(self):
        """Open folder dialog to select directory."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            folder_path = Path(folder)
            self.selected_files = [
                f
                for f in folder_path.rglob("*")
                if f.is_file() and is_supported_audio(f)
            ]
            self._update_file_list()

    def _update_file_list(self):
        """Update the file list display."""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            metadata = get_metadata(file_path)
            title = metadata.title or file_path.stem
            self.file_listbox.insert(tk.END, f"{title} ({file_path.name})")
        self.status_var.set(f"Loaded {len(self.selected_files)} files")

    def _search_lyrics(self):
        """Search for lyrics for selected files using multi-threading."""
        if not self.selected_files:
            self.status_var.set("No files selected")
            return

        self.status_var.set("Searching via multiple providers...")
        self.root.update()

        self.results_listbox.delete(0, tk.END)
        self.search_results = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for file_path in self.selected_files[:20]:
                metadata = get_metadata(file_path)
                future = executor.submit(
                    self.provider.search_all,
                    metadata.title or file_path.stem,
                    metadata.artist or "",
                    metadata.duration,
                )
                futures[future] = file_path

            for idx, future in enumerate(futures):
                file_path = futures[future]
                try:
                    tracks = future.result()
                    for track in tracks[:3]:
                        self.search_results.append((file_path, track))
                except Exception:
                    pass

                if idx % 5 == 0:
                    self.status_var.set(f"Searching... ({idx + 1}/{len(futures)})")
                    self.root.update()

        self._update_results()
        self.status_var.set(f"Found {len(self.search_results)} lyrics options")

    def _update_results(self):
        """Update the results list display."""
        self.results_listbox.delete(0, tk.END)

        for file_path, track in self.search_results:
            source_icon = {"LRCLIB": "L", "Netease": "N", "QQ Music": "Q"}.get(track.source, "?")
            line = f"[{source_icon}] {track.artist_name} - {track.track_name}"
            self.results_listbox.insert(tk.END, line)

    def _on_result_select(self, event):
        """Handle result selection."""
        selection = self.results_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < len(self.search_results):
            _, track = self.search_results[idx]
            self.current_lyrics = track

            lyrics = track.synced_lyrics or track.plain_lyrics or ""
            self.lyrics_text.delete("1.0", tk.END)
            self.lyrics_text.insert("1.0", lyrics)

    def _get_formatted_lyrics(self) -> str:
        """Get lyrics in the selected format."""
        if not self.current_lyrics:
            return ""

        base_lyrics = self.current_lyrics.synced_lyrics or self.current_lyrics.plain_lyrics or ""
        output_format = self.current_format.get()
        metadata = None

        for file_path, track in self.search_results:
            if track.id == self.current_lyrics.id:
                metadata = get_metadata(file_path)
                break

        if output_format == "lrc":
            return base_lyrics
        elif output_format == "enhanced":
            return convert_to_enhanced_lrc(base_lyrics, self.current_lyrics.duration)
        elif output_format == "srt":
            return convert_lrc_to_srt(base_lyrics)
        elif output_format == "ass":
            title = metadata.title if metadata else ""
            artist = metadata.artist if metadata else ""
            return convert_lrc_to_ass(base_lyrics, title, artist)

        return base_lyrics

    def _save_to_file(self):
        """Save selected lyrics to a separate file."""
        if not self.current_lyrics:
            self.status_var.set("No lyrics selected")
            return

        selection = self.results_listbox.curselection()
        if not selection:
            self.status_var.set("Please select a lyrics result first")
            return

        idx = selection[0]
        file_path, _ = self.search_results[idx]

        lyrics = self._get_formatted_lyrics()
        lyrics_format = LyricsFormat(self.current_format.get())
        lyrics_path = save_lyrics_to_file(file_path, lyrics, lyrics_format)
        self.status_var.set(f"Saved to {lyrics_path.name}")

    def _write_to_tag(self):
        """Write lyrics directly to audio file metadata tags."""
        if not self.current_lyrics:
            self.status_var.set("No lyrics selected")
            return

        selection = self.results_listbox.curselection()
        if not selection:
            self.status_var.set("Please select a lyrics result first")
            return

        idx = selection[0]
        file_path, _ = self.search_results[idx]

        lyrics = self.current_lyrics.synced_lyrics or self.current_lyrics.plain_lyrics or ""
        if write_lyrics_to_tag(file_path, lyrics):
            self.status_var.set(f"Wrote lyrics to tag: {file_path.name}")
        else:
            self.status_var.set(f"Failed to write lyrics to tag: {file_path.name}")

    def _clear_all(self):
        """Clear all selections and results."""
        self.selected_files = []
        self.search_results = []
        self.current_lyrics = None
        self.file_listbox.delete(0, tk.END)
        self.results_listbox.delete(0, tk.END)
        self.lyrics_text.delete("1.0", tk.END)
        self.status_var.set("Cleared")

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()