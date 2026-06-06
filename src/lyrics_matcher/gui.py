"""Lyrics Matcher GUI application with multi-provider search and multi-select support."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional, List, Tuple, Set
from concurrent.futures import ThreadPoolExecutor

from .audio import (
    get_metadata,
    is_supported_audio,
    save_lyrics_to_file,
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
from .i18n import i18n, LANGUAGES, set_language


class LyricsMatcherGUI:
    """Main GUI application for lyrics matching."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(i18n.t("app_title"))
        self.root.geometry("900x750")

        self.provider = MultiProvider(timeout=15, max_workers=4)
        self.selected_files: List[Path] = []
        self.search_results: List[Tuple[Path, LyricTrack]] = []
        self.current_lyrics: Optional[LyricTrack] = None
        self.selected_indices: Set[int] = set()
        self.current_format = tk.StringVar(value="lrc")

        self._create_menu()
        self._create_widgets()
        self._update_ui_texts()

    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=i18n.t("menu_file"), menu=file_menu)
        file_menu.add_command(label=i18n.t("menu_exit"), command=self.root.quit)

        # Language menu
        lang_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=i18n.t("menu_language"), menu=lang_menu)

        self.lang_var = tk.StringVar(value=i18n.get_language())
        for lang_code, lang_name in LANGUAGES.items():
            lang_menu.add_radiobutton(
                label=lang_name,
                variable=self.lang_var,
                value=lang_code,
                command=self._change_language,
            )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=i18n.t("menu_help"), menu=help_menu)
        help_menu.add_command(label=i18n.t("menu_about"), command=self._show_about)

    def _change_language(self):
        """Change the application language."""
        new_lang = self.lang_var.get()
        set_language(new_lang)
        i18n.set_language(new_lang)

        self.root.title(i18n.t("app_title"))
        self.root.config(menu="")
        self._create_menu()
        self._update_ui_texts()

    def _update_ui_texts(self):
        """Update all UI texts to current language."""
        self.btn_select_files.config(text=i18n.t("btn_select_files"))
        self.btn_select_folder.config(text=i18n.t("btn_select_folder"))
        self.btn_search.config(text=i18n.t("btn_search"))
        self.btn_clear.config(text=i18n.t("btn_clear"))
        self.btn_select_all.config(text=i18n.t("btn_select_all"))
        self.btn_deselect_all.config(text=i18n.t("btn_deselect_all"))
        self.btn_invert.config(text=i18n.t("btn_invert_selection"))
        self.btn_save_selected.config(text=i18n.t("btn_save_selected"))

        self.label_files.config(text=i18n.t("label_files"))
        self.label_results.config(text=i18n.t("label_results"))
        self.label_preview.config(text=i18n.t("label_preview"))

        self.radio_lrc.config(text=i18n.t("format_lrc"))
        self.radio_enhanced.config(text=i18n.t("format_enhanced"))
        self.radio_srt.config(text=i18n.t("format_srt"))
        self.radio_ass.config(text=i18n.t("format_ass"))

        if "Ready" in self.status_var.get() or not self.status_var.get():
            self.status_var.set(i18n.t("ready_status"))

    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            i18n.t("dialog_about_title"),
            i18n.t("dialog_about_text"),
        )

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

        self.btn_select_files = ttk.Button(
            btn_frame,
            text=i18n.t("btn_select_files"),
            command=self._select_files,
        )
        self.btn_select_files.grid(row=0, column=0, padx=(0, 5))

        self.btn_select_folder = ttk.Button(
            btn_frame,
            text=i18n.t("btn_select_folder"),
            command=self._select_folder,
        )
        self.btn_select_folder.grid(row=0, column=1, padx=(0, 5))

        self.btn_search = ttk.Button(
            btn_frame,
            text=i18n.t("btn_search"),
            command=self._search_lyrics,
        )
        self.btn_search.grid(row=0, column=2, padx=(0, 5))

        self.btn_clear = ttk.Button(
            btn_frame,
            text=i18n.t("btn_clear"),
            command=self._clear_all,
        )
        self.btn_clear.grid(row=0, column=3, padx=(0, 5))

        # Selection buttons
        selection_frame = ttk.LabelFrame(btn_frame, text=i18n.t("label_selection"), padding="5")
        selection_frame.grid(row=0, column=4, padx=(10, 0))

        self.btn_select_all = ttk.Button(
            selection_frame,
            text=i18n.t("btn_select_all"),
            command=self._select_all_results,
        )
        self.btn_select_all.grid(row=0, column=0, padx=(0, 3))

        self.btn_deselect_all = ttk.Button(
            selection_frame,
            text=i18n.t("btn_deselect_all"),
            command=self._deselect_all_results,
        )
        self.btn_deselect_all.grid(row=0, column=1, padx=(0, 3))

        self.btn_invert = ttk.Button(
            selection_frame,
            text=i18n.t("btn_invert_selection"),
            command=self._invert_selection,
        )
        self.btn_invert.grid(row=0, column=2)

        # Save button
        self.btn_save_selected = ttk.Button(
            btn_frame,
            text=i18n.t("btn_save_selected"),
            command=self._save_selected_to_file,
        )
        self.btn_save_selected.grid(row=0, column=5, padx=(10, 0))

        # Format selection
        format_frame = ttk.LabelFrame(btn_frame, text=i18n.t("label_format"), padding="5")
        format_frame.grid(row=0, column=6, padx=(10, 0))

        self.radio_lrc = ttk.Radiobutton(
            format_frame,
            text=i18n.t("format_lrc"),
            variable=self.current_format,
            value="lrc",
        )
        self.radio_lrc.grid(row=0, column=0, padx=(0, 5))

        self.radio_enhanced = ttk.Radiobutton(
            format_frame,
            text=i18n.t("format_enhanced"),
            variable=self.current_format,
            value="enhanced",
        )
        self.radio_enhanced.grid(row=0, column=1, padx=(0, 5))

        self.radio_srt = ttk.Radiobutton(
            format_frame,
            text=i18n.t("format_srt"),
            variable=self.current_format,
            value="srt",
        )
        self.radio_srt.grid(row=0, column=2, padx=(0, 5))

        self.radio_ass = ttk.Radiobutton(
            format_frame,
            text=i18n.t("format_ass"),
            variable=self.current_format,
            value="ass",
        )
        self.radio_ass.grid(row=0, column=3)

        self.status_var = tk.StringVar(value=i18n.t("ready_status"))
        ttk.Label(main_frame, textvariable=self.status_var).grid(
            row=1, column=0, sticky="w", pady=(0, 5)
        )

        # Selected files list
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        self.label_files = ttk.Label(list_frame, text=i18n.t("label_files"))
        self.label_files.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.file_listbox = tk.Listbox(list_frame, height=5)
        self.file_listbox.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # Search results
        self.label_results = ttk.LabelFrame(main_frame, text=i18n.t("label_results"), padding="5")
        self.label_results.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        self.label_results.columnconfigure(0, weight=1)
        self.label_results.rowconfigure(0, weight=1)

        self.results_listbox = tk.Listbox(
            self.label_results,
            height=6,
            selectmode=tk.EXTENDED,
        )
        self.results_listbox.grid(row=0, column=0, sticky="ew")
        self.results_listbox.bind("<<ListboxSelect>>", self._on_result_select)
        self.results_listbox.bind("<Control-a>", lambda e: self._select_all_results())

        scrollbar2 = ttk.Scrollbar(self.label_results, orient="vertical")
        scrollbar2.config(command=self.results_listbox.yview)
        scrollbar2.grid(row=0, column=1, sticky="ns")
        self.results_listbox.config(yscrollcommand=scrollbar2.set)

        # Lyrics preview
        self.label_preview = ttk.LabelFrame(main_frame, text=i18n.t("label_preview"), padding="5")
        self.label_preview.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        self.label_preview.columnconfigure(0, weight=1)
        self.label_preview.rowconfigure(0, weight=1)

        self.lyrics_text = tk.Text(self.label_preview, height=10, wrap="word")
        self.lyrics_text.grid(row=0, column=0, sticky="nsew")

        scrollbar3 = ttk.Scrollbar(self.label_preview, orient="vertical")
        scrollbar3.config(command=self.lyrics_text.yview)
        scrollbar3.grid(row=0, column=1, sticky="ns")
        self.lyrics_text.config(yscrollcommand=scrollbar3.set)

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _select_files(self):
        """Open file dialog to select audio files."""
        files = filedialog.askopenfilenames(
            title=i18n.t("dialog_select_audio"),
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
        folder = filedialog.askdirectory(title=i18n.t("dialog_select_folder"))
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
        self.status_var.set(i18n.t("status_loaded", count=len(self.selected_files)))

    def _search_lyrics(self):
        """Search for lyrics for selected files using multi-threading."""
        if not self.selected_files:
            self.status_var.set(i18n.t("status_no_files"))
            return

        self.status_var.set(i18n.t("status_searching"))
        self.root.update()

        self.results_listbox.delete(0, tk.END)
        self.search_results = []
        self.selected_indices = set()

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
                    self.status_var.set(i18n.t("status_searching_progress", current=idx + 1, total=len(futures)))
                    self.root.update()

        self._update_results()
        self.status_var.set(i18n.t("status_found", count=len(self.search_results)))

    def _update_results(self):
        """Update the results list display."""
        self.results_listbox.delete(0, tk.END)

        for idx, (file_path, track) in enumerate(self.search_results):
            source_icon = {"LRCLIB": "L", "Netease": "N", "QQ Music": "Q"}.get(track.source, "?")
            line = f"[{source_icon}] {track.artist_name} - {track.track_name}"
            self.results_listbox.insert(tk.END, line)

            if idx in self.selected_indices:
                self.results_listbox.selection_set(idx)

    def _on_result_select(self, event):
        """Handle result selection."""
        selection = self.results_listbox.curselection()
        if not selection:
            return

        self.selected_indices = set(selection)

        idx = selection[0]
        if idx < len(self.search_results):
            _, track = self.search_results[idx]
            self.current_lyrics = track

            lyrics = track.synced_lyrics or track.plain_lyrics or ""
            self.lyrics_text.delete("1.0", tk.END)
            self.lyrics_text.insert("1.0", lyrics)

    def _select_all_results(self):
        """Select all results."""
        self.results_listbox.select_set(0, tk.END)
        self.selected_indices = set(range(len(self.search_results)))

    def _deselect_all_results(self):
        """Deselect all results."""
        self.results_listbox.selection_clear(0, tk.END)
        self.selected_indices = set()

    def _invert_selection(self):
        """Invert current selection."""
        all_indices = set(range(len(self.search_results)))
        self.selected_indices = all_indices - self.selected_indices
        self.results_listbox.selection_clear(0, tk.END)
        for idx in self.selected_indices:
            self.results_listbox.selection_set(idx)

    def _get_formatted_lyrics(self, track: LyricTrack, file_path: Path) -> str:
        """Get lyrics in the selected format for a specific track."""
        base_lyrics = track.synced_lyrics or track.plain_lyrics or ""
        output_format = self.current_format.get()
        metadata = get_metadata(file_path)

        if output_format == "lrc":
            return base_lyrics
        elif output_format == "enhanced":
            return convert_to_enhanced_lrc(base_lyrics, track.duration)
        elif output_format == "srt":
            return convert_lrc_to_srt(base_lyrics)
        elif output_format == "ass":
            return convert_lrc_to_ass(base_lyrics, metadata.title or "", metadata.artist or "")

        return base_lyrics

    def _save_selected_to_file(self):
        """Save all selected lyrics to files."""
        if not self.selected_indices:
            self.status_var.set(i18n.t("status_no_selection"))
            return

        lyrics_format = LyricsFormat(self.current_format.get())
        saved_count = 0

        for idx in self.selected_indices:
            if idx < len(self.search_results):
                file_path, track = self.search_results[idx]
                lyrics = self._get_formatted_lyrics(track, file_path)
                if lyrics:
                    lyrics_path = save_lyrics_to_file(file_path, lyrics, lyrics_format)
                    saved_count += 1

        self.status_var.set(i18n.t("status_saved", count=saved_count))

    def _clear_all(self):
        """Clear all selections and results."""
        self.selected_files = []
        self.search_results = []
        self.current_lyrics = None
        self.selected_indices = set()
        self.file_listbox.delete(0, tk.END)
        self.results_listbox.delete(0, tk.END)
        self.lyrics_text.delete("1.0", tk.END)
        self.status_var.set(i18n.t("status_cleared"))

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()