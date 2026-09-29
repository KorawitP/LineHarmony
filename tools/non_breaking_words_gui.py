"""
Tk GUI for managing non-breaking words JSON file.
"""

from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

# Ensure project root is on sys.path for `from src...` imports
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.lexicon.non_breaking_store_json import JSONNonBreakingStore
from src.utils.config import get_config


class App(tk.Tk):
    def __init__(self, initial_path: str | None = None, default_path: str | None = None):
        super().__init__()
        self.title("Non-breaking Words Manager")

        self.geometry("720x520")
        self._default_path = default_path or ""
        self._path_var = tk.StringVar(value=initial_path or default_path or "")
        self._filter_var = tk.StringVar(value="")

        self._store: JSONNonBreakingStore | None = None
        init = initial_path or default_path
        if init:
            self._store = JSONNonBreakingStore(init)

        self._build_ui()
        self._refresh_list()

    # UI
    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(top, text="JSON Path:").pack(side=tk.LEFT)
        tk.Entry(top, textvariable=self._path_var, width=60).pack(side=tk.LEFT, padx=6)
        tk.Button(top, text="Open...", command=self._choose_file).pack(side=tk.LEFT)
        tk.Button(top, text="Use Default", command=self._use_default).pack(side=tk.LEFT, padx=6)
        tk.Button(top, text="Save", command=self._save).pack(side=tk.LEFT)

        mid = tk.Frame(self)
        mid.pack(fill=tk.X, padx=8)
        tk.Label(mid, text="Filter:").pack(side=tk.LEFT)
        e = tk.Entry(mid, textvariable=self._filter_var, width=30)
        e.pack(side=tk.LEFT, padx=6)
        e.bind("<KeyRelease>", lambda _e: self._refresh_list())

        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btns = tk.Frame(self)
        btns.pack(fill=tk.X, padx=8, pady=8)
        tk.Button(btns, text="Add...", command=self._add_words).pack(side=tk.LEFT)
        tk.Button(btns, text="Remove Selected", command=self._remove_selected).pack(side=tk.LEFT, padx=6)
        tk.Button(btns, text="Import JSON...", command=self._import_json).pack(side=tk.LEFT, padx=6)
        tk.Button(btns, text="Export JSON...", command=self._export_json).pack(side=tk.LEFT, padx=6)

        # Paste JSON area
        paste = tk.LabelFrame(self, text="Paste JSON to import (expects {\"non_breaking_words\": [...]})")
        paste.pack(fill=tk.BOTH, expand=False, padx=8, pady=(0, 8))
        text_frame = tk.Frame(paste)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self._json_text = tk.Text(text_frame, height=6)
        self._json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2 = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._json_text.yview)
        self._json_text.config(yscrollcommand=sb2.set)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)

        paste_btns = tk.Frame(paste)
        paste_btns.pack(fill=tk.X, pady=4)
        tk.Button(paste_btns, text="Import from Text", command=self._import_from_text).pack(side=tk.LEFT)

        status = tk.Frame(self)
        status.pack(fill=tk.X, padx=8, pady=4)
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self._status_var, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Actions
    def _choose_file(self):
        path = filedialog.askopenfilename(
            title="Open JSON file",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        self._path_var.set(path)
        self._store = JSONNonBreakingStore(path)
        self._refresh_list()
        self._set_status("Opened file")

    def _use_default(self):
        if not self._default_path:
            self._set_status("No default path configured")
            return
        self._path_var.set(self._default_path)
        self._store = JSONNonBreakingStore(self._default_path)
        self._refresh_list()
        self._set_status("Using default path")

    def _save(self):
        if not self._ensure_store():
            return
        self._store.save()
        self._set_status("Saved")

    def _ensure_store(self) -> bool:
        if self._store is None:
            path = self._path_var.get().strip()
            if not path:
                messagebox.showwarning("No File", "Please choose a JSON file first.")
                return False
            self._store = JSONNonBreakingStore(path)
        return True

    def _refresh_list(self):
        words = sorted(self._store.get_all()) if self._store else []
        flt = self._filter_var.get().strip()
        if flt:
            words = [w for w in words if flt in w]
        self._listbox.delete(0, tk.END)
        for w in words:
            self._listbox.insert(tk.END, w)
        self._set_status(f"Loaded {len(words)} words")

    def _add_words(self):
        if not self._ensure_store():
            return
        text = simpledialog.askstring(
            "Add Words",
            "Enter words (one per line):",
            parent=self,
        )
        if text is None:
            return
        items = [line for line in text.splitlines()]
        added, skipped = self._store.add(items)
        self._refresh_list()
        self._set_status(f"Added {added}, skipped {skipped}")

    def _remove_selected(self):
        if not self._ensure_store():
            return
        idxs = list(self._listbox.curselection())
        if not idxs:
            return
        words = [self._listbox.get(i) for i in idxs]
        removed = self._store.remove(words)
        self._refresh_list()
        self._set_status(f"Removed {removed}")

    def _import_json(self):
        if not self._ensure_store():
            return
        path = filedialog.askopenfilename(
            title="Import JSON",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            words = data.get("non_breaking_words", []) if isinstance(data, dict) else []
            added, skipped = self._store.add(words)
            self._refresh_list()
            self._set_status(f"Imported: added {added}, skipped {skipped}")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _export_json(self):
        if not self._ensure_store():
            return
        path = filedialog.asksaveasfilename(
            title="Export JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            data = {"non_breaking_words": sorted(self._store.get_all())}
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._set_status("Exported JSON")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _import_from_text(self):
        if not self._ensure_store():
            return
        raw = self._json_text.get("1.0", tk.END).strip()
        if not raw:
            self._set_status("No JSON content to import")
            return
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object with key 'non_breaking_words'")
            words = data.get("non_breaking_words", [])
            if not isinstance(words, list):
                raise ValueError("'non_breaking_words' must be a list of strings")
            added, skipped = self._store.add(words)
            self._refresh_list()
            self._json_text.delete("1.0", tk.END)
            self._set_status(f"Imported from text: added {added}, skipped {skipped}")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))


if __name__ == "__main__":
    # Load default path from config
    cfg = get_config()
    default_path = cfg.get("tokenizer.non_breaking_words_path", str(_ROOT / "data/lexicons/non_breaking_words.json"))
    App(initial_path=default_path, default_path=default_path).mainloop()
