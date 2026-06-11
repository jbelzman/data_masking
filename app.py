from __future__ import annotations

import os
import platform
import subprocess
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
if os.name == "nt":
    VENV_PYTHON = APP_DIR / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = APP_DIR / ".venv" / "bin" / "python"


def _native_error(title: str, message: str) -> None:
    if platform.system() == "Darwin":
        escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')
        escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display dialog "{escaped_message}" with title "{escaped_title}" '
                    'buttons {"OK"} default button "OK" with icon stop',
                ],
                check=False,
            )
            return
        except Exception:
            pass
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}", file=sys.stderr)


def _use_private_environment() -> None:
    if os.environ.get("MASKING_TOOL_VENV") == "1":
        return
    if not VENV_PYTHON.exists():
        return
    current = Path(sys.executable).resolve()
    if current == VENV_PYTHON.resolve():
        return
    environment = os.environ.copy()
    environment["MASKING_TOOL_VENV"] = "1"
    try:
        os.execve(
            str(VENV_PYTHON),
            [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
            environment,
        )
    except OSError as exc:
        _native_error(
            "Local Data Masking Tool",
            "The app could not start its private Python environment.\n\n"
            f"{exc}\n\nRun the setup launcher for your operating system, then run the app launcher.",
        )
        raise SystemExit(1)


_use_private_environment()

try:
    import pandas as pd
except ImportError as exc:
    _native_error(
        "Local Data Masking Tool",
        "Required packages are not installed.\n\n"
        "Run the setup launcher for your operating system, then open the app launcher.",
    )
    raise SystemExit(1) from exc

from masking_tool.core import (
    AGGREGATIONS,
    load_dataframe,
    mask_and_aggregate,
    restore_dataframe_checked,
    save_masked_package,
    save_restored_package,
)
from masking_tool.vault import generate_masking_key, read_vault, write_vault


APP_NAME = "Local Data Masking Tool"
BG = "#edf4ff"
CARD = "#ffffff"
INK = "#10233f"
MUTED = "#53657d"
ACCENT = "#1769e0"
ACCENT_DARK = "#0d4fad"
ACCENT_LIGHT = "#dceaff"
BORDER = "#bfd2ee"
INPUT_BG = "#f8fbff"
SUCCESS = "#18794e"


class DataMaskingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} 2.0")
        self.geometry("1280x1000")
        self.minsize(1080, 900)
        self.configure(bg=BG)

        self.data: pd.DataFrame | None = None
        self.column_config: dict[str, dict[str, object]] = {}
        self.dimension_columns: list[str] = []
        self.metric_columns: list[str] = []
        self.mask_vars: dict[str, tk.BooleanVar] = {}
        self.aggregation_vars: dict[str, tk.StringVar] = {}
        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*Listbox.background", INPUT_BG)
        self.option_add("*Listbox.foreground", INK)
        self.option_add("*Listbox.selectBackground", ACCENT)
        self.option_add("*Listbox.selectForeground", "#ffffff")
        self.option_add("*Listbox.highlightBackground", BORDER)
        self.option_add("*Listbox.highlightColor", ACCENT)
        self.option_add("*Listbox.relief", "flat")
        self.option_add("*Listbox.borderWidth", 1)

        style.configure(".", font=("Segoe UI", 10), background=BG, foreground=INK)
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure(
            "Card.TLabelframe",
            background=CARD,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=CARD,
            foreground=ACCENT_DARK,
            font=("Segoe UI Semibold", 10),
        )
        style.configure("TLabel", background=BG, foreground=INK)
        style.configure("Card.TLabel", background=CARD, foreground=INK)
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED)
        style.configure(
            "Title.TLabel",
            font=("Segoe UI Semibold", 24),
            background=BG,
            foreground=ACCENT_DARK,
        )
        style.configure(
            "Section.TLabel",
            font=("Segoe UI Semibold", 12),
            background=CARD,
            foreground=ACCENT_DARK,
        )
        style.configure(
            "Primary.TButton",
            background=ACCENT,
            foreground="white",
            bordercolor=ACCENT,
            lightcolor=ACCENT,
            darkcolor=ACCENT_DARK,
            padding=(16, 9),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Primary.TButton",
            background=[("active", ACCENT_DARK), ("disabled", "#aabbd3")],
            foreground=[("disabled", "#f4f7fb")],
        )
        style.configure(
            "Secondary.TButton",
            background=ACCENT_LIGHT,
            foreground=ACCENT_DARK,
            bordercolor=BORDER,
            lightcolor=ACCENT_LIGHT,
            darkcolor=BORDER,
            padding=(12, 8),
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#c8ddfb")],
            foreground=[("active", "#073d88")],
        )
        style.configure(
            "TEntry",
            fieldbackground=INPUT_BG,
            foreground=INK,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=6,
        )
        style.map("TEntry", bordercolor=[("focus", ACCENT)])
        style.configure(
            "TCombobox",
            fieldbackground=INPUT_BG,
            background=INPUT_BG,
            foreground=INK,
            arrowcolor=ACCENT_DARK,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=5,
        )
        style.map(
            "TCombobox",
            bordercolor=[("focus", ACCENT)],
            fieldbackground=[("readonly", INPUT_BG)],
            selectbackground=[("readonly", INPUT_BG)],
            selectforeground=[("readonly", INK)],
        )
        style.configure(
            "Treeview",
            rowheight=29,
            background=INPUT_BG,
            fieldbackground=INPUT_BG,
            foreground=INK,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
        )
        style.map(
            "Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI Semibold", 9),
            background=ACCENT_LIGHT,
            foreground=ACCENT_DARK,
            bordercolor=BORDER,
            relief="flat",
            padding=(8, 7),
        )
        style.map("Treeview.Heading", background=[("active", "#c8ddfb")])
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure(
            "TNotebook.Tab",
            background="#d5e2f4",
            foreground=MUTED,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=(18, 9),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT), ("active", "#c5daf7")],
            foreground=[("selected", "#ffffff"), ("active", ACCENT_DARK)],
            padding=[("selected", (26, 14)), ("active", (20, 10))],
            font=[("selected", ("Segoe UI Semibold", 12))],
        )
        style.configure(
            "TCheckbutton",
            background=CARD,
            foreground=INK,
            focuscolor=CARD,
            padding=2,
        )
        style.map(
            "TCheckbutton",
            background=[("active", CARD)],
            foreground=[("active", ACCENT_DARK)],
            indicatorcolor=[("selected", ACCENT), ("!selected", INPUT_BG)],
        )
        style.configure("Horizontal.TProgressbar", background=ACCENT)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(28, 22, 28, 12))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Mask and aggregate locally. Encrypted lookup keys stay separate from the output.",
            foreground=MUTED,
        ).pack(anchor="w", pady=(4, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        self.mask_tab_host = ttk.Frame(notebook)
        self.restore_tab = ttk.Frame(notebook)
        notebook.add(self.mask_tab_host, text="Mask data")
        notebook.add(self.restore_tab, text="Restore data")
        self._build_mask_scroll_area()
        self._build_mask_tab()
        self._build_restore_tab()

        self.status_var = tk.StringVar(value="Ready. Everything runs on this computer.")
        status = ttk.Frame(self, padding=(28, 8, 28, 12))
        status.pack(fill="x")
        ttk.Label(status, textvariable=self.status_var, foreground=MUTED).pack(side="left")
        self.progress = ttk.Progressbar(status, mode="indeterminate", length=180)
        self.progress.pack(side="right")

    def _build_mask_scroll_area(self) -> None:
        self.mask_tab_host.rowconfigure(0, weight=1)
        self.mask_tab_host.columnconfigure(0, weight=1)
        self.mask_canvas = tk.Canvas(
            self.mask_tab_host,
            background=BG,
            borderwidth=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            self.mask_tab_host,
            orient="vertical",
            command=self.mask_canvas.yview,
        )
        self.mask_canvas.configure(yscrollcommand=scrollbar.set)
        self.mask_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.mask_tab = ttk.Frame(self.mask_canvas)
        self.mask_tab_window = self.mask_canvas.create_window(
            (0, 0), window=self.mask_tab, anchor="nw"
        )
        self.mask_tab.bind(
            "<Configure>",
            lambda _event: self.mask_canvas.configure(
                scrollregion=self.mask_canvas.bbox("all")
            ),
        )
        self.mask_canvas.bind(
            "<Configure>",
            lambda event: self.mask_canvas.itemconfigure(
                self.mask_tab_window, width=event.width
            ),
        )
        self.bind_all("<MouseWheel>", self._on_master_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_master_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_master_mousewheel, add="+")

    def _on_master_mousewheel(self, event) -> None:
        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        left = self.mask_canvas.winfo_rootx()
        top = self.mask_canvas.winfo_rooty()
        right = left + self.mask_canvas.winfo_width()
        bottom = top + self.mask_canvas.winfo_height()
        if left <= x <= right and top <= y <= bottom:
            if getattr(event, "num", None) == 4 or event.delta > 0:
                direction = -1
            else:
                direction = 1
            self.mask_canvas.yview_scroll(direction * 3, "units")

    def _card(
        self, parent: tk.Widget, title: str, subtitle: str
    ) -> tuple[ttk.Frame, ttk.Frame]:
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        ttk.Label(card, text=title, style="Section.TLabel").pack(anchor="w")
        ttk.Label(card, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(2, 14))
        body = ttk.Frame(card, style="Card.TFrame")
        body.pack(fill="both", expand=True)
        return card, body

    def _build_mask_tab_legacy(self) -> None:
        self.mask_tab.columnconfigure(0, weight=1)
        self.mask_tab.rowconfigure(1, weight=1)

        source, source_body = self._card(
            self.mask_tab,
            "1. Choose source data",
            "CSV and Excel files stay local. The first rows appear below after loading.",
        )
        source.grid(row=0, column=0, sticky="ew", pady=(14, 10))
        source_body.columnconfigure(0, weight=1)
        self.source_var = tk.StringVar()
        ttk.Entry(source_body, textvariable=self.source_var).pack(side="left", fill="x", expand=True)
        ttk.Button(source_body, text="Browse", style="Secondary.TButton", command=self._browse_source).pack(
            side="left", padx=(10, 0)
        )

        middle = ttk.Panedwindow(self.mask_tab, orient="horizontal")
        middle.grid(row=1, column=0, sticky="nsew", pady=0)

        preview_card, preview_body = self._card(
            middle,
            "Preview",
            "A read-only sample of the selected file.",
        )
        config_card, config_body = self._card(
            middle,
            "2. Configure columns",
            "Select one or several columns, then add them as dimensions or metrics.",
        )
        middle.add(preview_card, weight=1)
        middle.add(config_card, weight=1)

        preview_frame = ttk.Frame(preview_body, style="Card.TFrame")
        preview_frame.pack(fill="both", expand=True)
        self.preview = ttk.Treeview(preview_frame, show="headings", height=12)
        px = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview.xview)
        py = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview.yview)
        self.preview.configure(xscrollcommand=px.set, yscrollcommand=py.set)
        self.preview.grid(row=0, column=0, sticky="nsew")
        py.grid(row=0, column=1, sticky="ns")
        px.grid(row=1, column=0, sticky="ew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        selection = ttk.Frame(config_body, style="Card.TFrame")
        selection.pack(fill="both", expand=True)
        selection.columnconfigure(0, weight=1)
        selection.columnconfigure(2, weight=1)
        selection.columnconfigure(4, weight=1)
        selection.rowconfigure(1, weight=1)

        ttk.Label(selection, text="Available columns", style="Card.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(selection, text="Dimensions", style="Card.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        ttk.Label(selection, text="Metrics", style="Card.TLabel").grid(
            row=0, column=4, sticky="w"
        )
        self.available_list = self._create_column_list(selection, 1, 0)
        self.dimension_list = self._create_column_list(selection, 1, 2)
        self.metric_list = self._create_column_list(selection, 1, 4)

        dimension_buttons = ttk.Frame(selection, style="Card.TFrame")
        dimension_buttons.grid(row=1, column=1, padx=8)
        ttk.Button(
            dimension_buttons, text="Add →", command=self._add_dimensions, width=9
        ).pack(pady=(12, 5))
        ttk.Button(
            dimension_buttons, text="← Remove", command=self._remove_dimensions, width=9
        ).pack(pady=5)

        metric_buttons = ttk.Frame(selection, style="Card.TFrame")
        metric_buttons.grid(row=1, column=3, padx=8)
        ttk.Button(
            metric_buttons, text="Add →", command=self._add_metrics, width=9
        ).pack(pady=(12, 5))
        ttk.Button(
            metric_buttons, text="← Remove", command=self._remove_metrics, width=9
        ).pack(pady=5)

        options_pane = ttk.Panedwindow(config_body, orient="horizontal")
        options_pane.pack(fill="both", expand=True, pady=(14, 0))
        mask_box = ttk.LabelFrame(
            options_pane, text="Mask dimensions", padding=8, style="Card.TLabelframe"
        )
        aggregation_box = ttk.LabelFrame(
            options_pane,
            text="Metric aggregation",
            padding=8,
            style="Card.TLabelframe",
        )
        options_pane.add(mask_box, weight=1)
        options_pane.add(aggregation_box, weight=1)
        self.mask_options = self._create_scrollable_panel(mask_box)
        self.aggregation_options = self._create_scrollable_panel(aggregation_box)
        self._refresh_option_panels()

        output, output_body = self._card(
            self.mask_tab,
            "3. Save securely",
            "Choose different folders for shareable masked data and the encrypted key vault.",
        )
        output.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        output_body.columnconfigure(1, weight=1)
        self.output_dir_var = tk.StringVar()
        self.vault_dir_var = tk.StringVar()
        self.base_name_var = tk.StringVar(value="masked_data")
        self.format_var = tk.StringVar(value="Excel (.xlsx)")
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)
        self._folder_row(output_body, 0, "Masked output folder", self.output_dir_var)
        self._folder_row(output_body, 1, "Encrypted vault folder", self.vault_dir_var)

        options = ttk.Frame(output_body, style="Card.TFrame")
        options.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        options.columnconfigure(0, weight=2)
        options.columnconfigure(1, weight=1)
        options.columnconfigure(2, weight=1)
        options.columnconfigure(3, weight=1)
        self._labeled_entry(options, 0, "Base name", self.base_name_var)
        ttk.Label(options, text="Format", style="Card.TLabel").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Combobox(
            options,
            textvariable=self.format_var,
            values=["Excel (.xlsx)", "CSV (.csv)"],
            state="readonly",
            width=15,
        ).grid(row=1, column=1, sticky="ew", padx=(10, 0))
        self.password_entry = self._labeled_entry(
            options, 2, "Vault password", self.password_var, show="*"
        )
        self.confirm_password_entry = self._labeled_entry(
            options, 3, "Confirm password", self.confirm_password_var, show="*"
        )
        ttk.Checkbutton(
            options,
            text="Show passwords",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
        ).grid(row=2, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=(5, 0))
        ttk.Button(
            options,
            text="Mask and save",
            style="Primary.TButton",
            command=self._start_masking,
        ).grid(row=1, column=4, padx=(16, 0), sticky="e")

    def _build_mask_tab(self) -> None:
        self.mask_tab.columnconfigure(0, weight=1)

        source, source_body = self._card(
            self.mask_tab,
            "1. Choose source data",
            "CSV and Excel files stay local. The first rows appear below after loading.",
        )
        source.grid(row=0, column=0, sticky="ew", pady=(14, 10))
        self.source_var = tk.StringVar()
        ttk.Entry(source_body, textvariable=self.source_var).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            source_body,
            text="Browse",
            style="Secondary.TButton",
            command=self._browse_source,
        ).pack(side="left", padx=(10, 0))

        preview_card, preview_body = self._card(
            self.mask_tab,
            "2. Review data",
            "A full-width, read-only sample of the selected file.",
        )
        preview_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        preview_frame = ttk.Frame(preview_body, style="Card.TFrame")
        preview_frame.pack(fill="both", expand=True)
        self.preview = ttk.Treeview(preview_frame, show="headings", height=5)
        px = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview.xview)
        py = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview.yview)
        self.preview.configure(xscrollcommand=px.set, yscrollcommand=py.set)
        self.preview.grid(row=0, column=0, sticky="nsew")
        py.grid(row=0, column=1, sticky="ns")
        px.grid(row=1, column=0, sticky="ew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        selection_card, selection_body = self._card(
            self.mask_tab,
            "3. Select columns",
            "Batch-select available fields, then add them as dimensions or numeric metrics.",
        )
        selection_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        selection_body.columnconfigure(0, weight=1)
        selection_body.columnconfigure(2, weight=1)

        ttk.Label(
            selection_body, text="Available columns", style="Card.TLabel"
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(selection_body, text="Dimensions", style="Card.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        self.available_list = self._create_column_list(
            selection_body, 1, 0, height=8, rowspan=4
        )
        self.dimension_list = self._create_column_list(
            selection_body, 1, 2, height=3
        )

        dimension_buttons = ttk.Frame(selection_body, style="Card.TFrame")
        dimension_buttons.grid(row=1, column=1, padx=14, sticky="n")
        ttk.Button(
            dimension_buttons,
            text="Add dimension >",
            command=self._add_dimensions,
            width=14,
        ).pack(pady=(5, 5))
        ttk.Button(
            dimension_buttons,
            text="< Remove",
            command=self._remove_dimensions,
            width=14,
        ).pack(pady=5)

        ttk.Separator(selection_body, orient="horizontal").grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=8
        )
        ttk.Label(selection_body, text="Metrics", style="Card.TLabel").grid(
            row=3, column=2, sticky="w"
        )
        self.metric_list = self._create_column_list(
            selection_body, 4, 2, height=3
        )

        metric_buttons = ttk.Frame(selection_body, style="Card.TFrame")
        metric_buttons.grid(row=4, column=1, padx=14, sticky="n")
        ttk.Button(
            metric_buttons,
            text="Add metric >",
            command=self._add_metrics,
            width=14,
        ).pack(pady=(5, 5))
        ttk.Button(
            metric_buttons,
            text="< Remove",
            command=self._remove_metrics,
            width=14,
        ).pack(pady=5)

        config_card, config_body = self._card(
            self.mask_tab,
            "4. Configure masking and aggregation",
            "Choose sensitive dimensions to mask and how each metric should be summarized.",
        )
        config_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        config_body.columnconfigure(0, weight=1)
        config_body.columnconfigure(1, weight=1)
        mask_box = ttk.LabelFrame(
            config_body,
            text="Mask dimensions",
            padding=10,
            style="Card.TLabelframe",
        )
        aggregation_box = ttk.LabelFrame(
            config_body,
            text="Metric aggregation",
            padding=10,
            style="Card.TLabelframe",
        )
        mask_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        aggregation_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.mask_options = self._create_scrollable_panel(mask_box)
        self.aggregation_options = self._create_scrollable_panel(aggregation_box)
        self._refresh_option_panels()

        self.context_enabled_var = tk.BooleanVar(value=False)
        context_toggle = ttk.Frame(config_body, style="Card.TFrame")
        context_toggle.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )
        ttk.Checkbutton(
            context_toggle,
            text="Create AI context layer",
            variable=self.context_enabled_var,
            command=self._toggle_context_layer,
        ).pack(side="left")
        ttk.Label(
            context_toggle,
            text="Describe what dimensions mean without including sensitive values.",
            style="Muted.TLabel",
        ).pack(side="left", padx=(10, 0))

        self.context_frame = ttk.Frame(
            config_body, style="Card.TFrame", padding=(0, 8, 0, 0)
        )
        self.context_frame.grid(
            row=2, column=0, columnspan=2, sticky="ew"
        )
        self.context_frame.columnconfigure(0, weight=1)
        self.context_text = tk.Text(
            self.context_frame,
            height=5,
            wrap="word",
            background=INPUT_BG,
            foreground=INK,
            insertbackground=INK,
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            font=("Segoe UI", 10),
            padx=8,
            pady=7,
        )
        self.context_text.grid(row=0, column=0, sticky="ew")
        self.context_frame.grid_remove()

        output, output_body = self._card(
            self.mask_tab,
            "5. Save securely",
            "Choose different folders for shareable masked data and the encrypted key vault.",
        )
        output.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        output_body.columnconfigure(1, weight=1)
        self.output_dir_var = tk.StringVar()
        self.vault_dir_var = tk.StringVar()
        self.base_name_var = tk.StringVar(value="masked_data")
        self.format_var = tk.StringVar(value="Excel (.xlsx)")
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)
        self._folder_row(output_body, 0, "Masked output folder", self.output_dir_var)
        self._folder_row(output_body, 1, "Encrypted vault folder", self.vault_dir_var)

        options = ttk.Frame(output_body, style="Card.TFrame")
        options.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        options.columnconfigure(0, weight=2)
        options.columnconfigure(1, weight=1)
        options.columnconfigure(2, weight=1)
        options.columnconfigure(3, weight=1)
        self._labeled_entry(options, 0, "Base name", self.base_name_var)
        ttk.Label(options, text="Format", style="Card.TLabel").grid(
            row=0, column=1, sticky="w", padx=(10, 0)
        )
        ttk.Combobox(
            options,
            textvariable=self.format_var,
            values=["Excel (.xlsx)", "CSV (.csv)"],
            state="readonly",
            width=15,
        ).grid(row=1, column=1, sticky="ew", padx=(10, 0))
        self.password_entry = self._labeled_entry(
            options, 2, "Vault password", self.password_var, show="*"
        )
        self.confirm_password_entry = self._labeled_entry(
            options, 3, "Confirm password", self.confirm_password_var, show="*"
        )
        ttk.Checkbutton(
            options,
            text="Show passwords",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
        ).grid(
            row=2,
            column=2,
            columnspan=2,
            sticky="w",
            padx=(10, 0),
            pady=(5, 0),
        )
        ttk.Button(
            options,
            text="Mask and save",
            style="Primary.TButton",
            command=self._start_masking,
        ).grid(row=1, column=4, padx=(16, 0), sticky="e")

    def _build_restore_tab(self) -> None:
        self.restore_tab.columnconfigure(0, weight=1)
        restore, restore_body = self._card(
            self.restore_tab,
            "Restore authorized data",
            "Select a masked file and its separate vault. The password decrypts the lookup only in memory.",
        )
        restore.grid(row=0, column=0, sticky="new", pady=(14, 0))
        restore_body.columnconfigure(1, weight=1)

        self.restore_data_var = tk.StringVar()
        self.restore_vault_var = tk.StringVar()
        self.restore_output_var = tk.StringVar()
        self.restore_password_var = tk.StringVar()
        self.show_restore_password_var = tk.BooleanVar(value=False)
        self._file_row(restore_body, 0, "Masked data file", self.restore_data_var, [("Data", "*.csv *.xlsx")])
        self._file_row(restore_body, 1, "Encrypted vault", self.restore_vault_var, [("Mask vault", "*.maskvault")])
        self._save_row(restore_body, 2, "Restored output file", self.restore_output_var)

        password_frame = ttk.Frame(restore_body, style="Card.TFrame")
        password_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        password_frame.columnconfigure(0, weight=1)
        ttk.Label(password_frame, text="Vault password", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.restore_password_entry = ttk.Entry(
            password_frame, textvariable=self.restore_password_var, show="*"
        )
        self.restore_password_entry.grid(
            row=1, column=0, sticky="ew", pady=(4, 0)
        )
        ttk.Checkbutton(
            password_frame,
            text="Show password",
            variable=self.show_restore_password_var,
            command=self._toggle_restore_password_visibility,
        ).grid(row=2, column=0, sticky="w", pady=(5, 0))
        ttk.Button(
            password_frame,
            text="Restore and save",
            style="Primary.TButton",
            command=self._start_restore,
        ).grid(row=1, column=1, padx=(16, 0))

        note = ttk.Frame(self.restore_tab, style="Card.TFrame", padding=18)
        note.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(note, text="Security note", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            note,
            text=(
                "Restored files contain original sensitive values. Store them with the same care as the source. "
                "The app never saves or logs the vault password."
            ),
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(5, 0))

    def _folder_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=10, pady=4)
        ttk.Button(
            parent,
            text="Choose",
            command=lambda: self._choose_folder(variable),
        ).grid(row=row, column=2, pady=4)

    def _create_column_list(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        height: int = 10,
        rowspan: int = 1,
    ) -> tk.Listbox:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, rowspan=rowspan, sticky="nsew")
        listbox = tk.Listbox(
            frame, selectmode=tk.EXTENDED, exportselection=False, height=height
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return listbox

    def _create_scrollable_panel(self, parent: ttk.Frame) -> ttk.Frame:
        container = ttk.Frame(parent, style="Card.TFrame")
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(
            container,
            background=CARD,
            borderwidth=0,
            highlightthickness=0,
            height=155,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        content = ttk.Frame(canvas, style="Card.TFrame")
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window, width=event.width),
        )
        return content

    def _file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        filetypes: list[tuple[str, str]],
    ) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(
            parent,
            text="Browse",
            command=lambda: variable.set(filedialog.askopenfilename(filetypes=filetypes) or variable.get()),
        ).grid(row=row, column=2, pady=5)

    def _save_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(
            parent,
            text="Choose",
            command=lambda: variable.set(
                filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")],
                )
                or variable.get()
            ),
        ).grid(row=row, column=2, pady=5)

    def _labeled_entry(
        self,
        parent: ttk.Frame,
        column: int,
        label: str,
        variable: tk.StringVar,
        show: str | None = None,
    ) -> ttk.Entry:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(
            row=0, column=column, sticky="w", padx=(10 if column else 0, 0)
        )
        entry = ttk.Entry(parent, textvariable=variable, show=show)
        entry.grid(
            row=1, column=column, sticky="ew", padx=(10 if column else 0, 0)
        )
        return entry

    def _browse_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose source data",
            filetypes=[("Data files", "*.csv *.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        self.source_var.set(path)
        self._set_busy(True, "Loading source data...")
        threading.Thread(target=self._load_source_worker, args=(path,), daemon=True).start()

    def _load_source_worker(self, path: str) -> None:
        try:
            data = load_dataframe(path)
            if data.empty:
                raise ValueError("The selected file is empty.")
            self.after(0, lambda: self._finish_load(path, data))
        except Exception as exc:
            self.after(0, lambda exc=exc: self._show_error("Could not load file", exc))

    def _finish_load(self, path: str, data: pd.DataFrame) -> None:
        data = data.copy()
        data.columns = [str(column) for column in data.columns]
        self.data = data
        self.column_config.clear()
        self.dimension_columns.clear()
        self.metric_columns.clear()
        self.mask_vars.clear()
        self.aggregation_vars.clear()
        for column in data.columns:
            self.column_config[str(column)] = {
                "role": "Ignore",
                "mask": False,
                "aggregation": "SUM",
            }
        source = Path(path)
        self.base_name_var.set(f"{source.stem}_masked")
        self.output_dir_var.set(str(source.parent / "masked_output"))
        self.vault_dir_var.set(str(source.parent / "masking_vaults"))
        self._refresh_preview()
        self._refresh_column_lists()
        self._refresh_option_panels()
        self._set_busy(False, f"Loaded {len(data):,} rows and {len(data.columns)} columns.")

    def _refresh_preview(self) -> None:
        assert self.data is not None
        self.preview.delete(*self.preview.get_children())
        columns = [str(column) for column in self.data.columns]
        self.preview["columns"] = columns
        for column in columns:
            self.preview.heading(column, text=column)
            self.preview.column(column, width=max(100, min(180, len(column) * 10)), stretch=False)
        for _, row in self.data.head(12).iterrows():
            self.preview.insert("", "end", values=["" if pd.isna(value) else str(value) for value in row])

    def _selected_list_values(self, listbox: tk.Listbox) -> list[str]:
        return [str(listbox.get(index)) for index in listbox.curselection()]

    def _refresh_column_lists(self) -> None:
        all_columns = list(self.column_config)
        available = [
            column
            for column in all_columns
            if column not in self.dimension_columns and column not in self.metric_columns
        ]
        for listbox, values in (
            (self.available_list, available),
            (self.dimension_list, self.dimension_columns),
            (self.metric_list, self.metric_columns),
        ):
            listbox.delete(0, tk.END)
            for value in values:
                listbox.insert(tk.END, value)

    def _add_dimensions(self) -> None:
        selected = self._selected_list_values(self.available_list)
        if not selected:
            return
        for column in selected:
            if column not in self.dimension_columns:
                self.dimension_columns.append(column)
            self.column_config[column]["role"] = "Dimension"
        self._refresh_column_lists()
        self._refresh_option_panels()

    def _remove_dimensions(self) -> None:
        selected = self._selected_list_values(self.dimension_list)
        if not selected:
            return
        self.dimension_columns = [
            column for column in self.dimension_columns if column not in selected
        ]
        for column in selected:
            self.column_config[column]["role"] = "Ignore"
            self.column_config[column]["mask"] = False
            self.mask_vars.pop(column, None)
        self._refresh_column_lists()
        self._refresh_option_panels()

    def _add_metrics(self) -> None:
        selected = self._selected_list_values(self.available_list)
        if not selected:
            return
        assert self.data is not None
        invalid = [
            column
            for column in selected
            if not pd.api.types.is_numeric_dtype(self.data[column])
        ]
        if invalid:
            messagebox.showerror(
                APP_NAME,
                "Metrics must be numeric. These columns were not added:\n\n"
                + "\n".join(invalid),
            )
            selected = [column for column in selected if column not in invalid]
        for column in selected:
            if column not in self.metric_columns:
                self.metric_columns.append(column)
            self.column_config[column]["role"] = "Metric"
        self._refresh_column_lists()
        self._refresh_option_panels()

    def _remove_metrics(self) -> None:
        selected = self._selected_list_values(self.metric_list)
        if not selected:
            return
        self.metric_columns = [
            column for column in self.metric_columns if column not in selected
        ]
        for column in selected:
            self.column_config[column]["role"] = "Ignore"
            self.aggregation_vars.pop(column, None)
        self._refresh_column_lists()
        self._refresh_option_panels()

    def _refresh_option_panels(self) -> None:
        for child in self.mask_options.winfo_children():
            child.destroy()
        for child in self.aggregation_options.winfo_children():
            child.destroy()

        if not self.dimension_columns:
            ttk.Label(
                self.mask_options,
                text="Add dimensions to choose which ones to mask.",
                style="Muted.TLabel",
                wraplength=240,
            ).pack(anchor="w")
        else:
            for column in self.dimension_columns:
                variable = self.mask_vars.get(column)
                if variable is None:
                    variable = tk.BooleanVar(
                        value=bool(self.column_config[column]["mask"])
                    )
                    self.mask_vars[column] = variable
                ttk.Checkbutton(
                    self.mask_options,
                    text=column,
                    variable=variable,
                    command=lambda name=column, var=variable: self._set_mask(name, var),
                ).pack(anchor="w", pady=2)

        if not self.metric_columns:
            ttk.Label(
                self.aggregation_options,
                text="Add numeric metrics to choose an aggregation.",
                style="Muted.TLabel",
                wraplength=240,
            ).pack(anchor="w")
        else:
            for row, column in enumerate(self.metric_columns):
                variable = self.aggregation_vars.get(column)
                if variable is None:
                    variable = tk.StringVar(
                        value=str(self.column_config[column]["aggregation"])
                    )
                    self.aggregation_vars[column] = variable
                ttk.Label(
                    self.aggregation_options, text=column, style="Card.TLabel"
                ).grid(row=row, column=0, sticky="w", pady=2)
                combo = ttk.Combobox(
                    self.aggregation_options,
                    textvariable=variable,
                    values=list(AGGREGATIONS),
                    state="readonly",
                    width=12,
                )
                combo.grid(row=row, column=1, sticky="e", padx=(8, 0), pady=2)
                combo.bind(
                    "<<ComboboxSelected>>",
                    lambda _event, name=column, var=variable: self._set_aggregation(
                        name, var
                    ),
                )
            self.aggregation_options.columnconfigure(0, weight=1)

    def _set_mask(self, column: str, variable: tk.BooleanVar) -> None:
        self.column_config[column]["mask"] = variable.get()

    def _set_aggregation(self, column: str, variable: tk.StringVar) -> None:
        self.column_config[column]["aggregation"] = variable.get()

    def _toggle_password_visibility(self) -> None:
        show = "" if self.show_password_var.get() else "*"
        self.password_entry.configure(show=show)
        self.confirm_password_entry.configure(show=show)

    def _toggle_restore_password_visibility(self) -> None:
        self.restore_password_entry.configure(
            show="" if self.show_restore_password_var.get() else "*"
        )

    def _toggle_context_layer(self) -> None:
        if self.context_enabled_var.get():
            self.context_frame.grid()
            if not self.context_text.get("1.0", "end").strip():
                self._insert_context_template()
        else:
            self.context_frame.grid_remove()

    def _insert_context_template(self) -> None:
        dimensions = self.dimension_columns or ["[dimension name]"]
        lines = [
            "Dataset context:",
            "[Briefly explain what this dataset measures and how it should be used.]",
            "",
            "Dimension definitions:",
        ]
        lines.extend(f"- {dimension}: " for dimension in dimensions)
        lines.extend(
            [
                "",
                "Interpretation notes:",
                "[Add useful caveats, units, date ranges, or grouping guidance. "
                "Do not include real sensitive values.]",
            ]
        )
        self.context_text.delete("1.0", "end")
        self.context_text.insert("1.0", "\n".join(lines))

    def _choose_folder(self, variable: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=variable.get() or None)
        if selected:
            variable.set(selected)

    def _validate_mask_job(self) -> tuple[Path, Path, Path, Path]:
        if self.data is None:
            raise ValueError("Load a source file first.")
        if not self.dimension_columns:
            raise ValueError("Add at least one dimension before masking.")
        output_dir = Path(self.output_dir_var.get().strip()).expanduser().resolve()
        vault_dir = Path(self.vault_dir_var.get().strip()).expanduser().resolve()
        if output_dir == vault_dir:
            raise ValueError("Masked output and encrypted vault must use different folders.")
        base_name = "".join(
            character for character in self.base_name_var.get().strip()
            if character not in '<>:"/\\|?*'
        ).strip(". ")
        if not base_name:
            raise ValueError("Enter a valid base name.")
        password = self.password_var.get()
        if len(password) < 12:
            raise ValueError("Use a vault password of at least 12 characters.")
        if password != self.confirm_password_var.get():
            raise ValueError("Vault passwords do not match.")
        extension = ".xlsx" if self.format_var.get().startswith("Excel") else ".csv"
        output_path = output_dir / f"{base_name}{extension}"
        vault_path = vault_dir / f"{base_name}.maskvault"
        return output_dir, vault_dir, output_path, vault_path

    def _start_masking(self) -> None:
        try:
            output_dir, vault_dir, output_path, vault_path = self._validate_mask_job()
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        if (output_path.exists() or vault_path.exists()) and not messagebox.askyesno(
            APP_NAME, "One or more output files already exist. Replace them?"
        ):
            return
        self._set_busy(True, "Masking and aggregating...")
        job = {
            "data": self.data.copy(),
            "source_name": Path(self.source_var.get()).name,
            "password": self.password_var.get(),
            "context_text": (
                self.context_text.get("1.0", "end").strip()
                if self.context_enabled_var.get()
                else ""
            ),
            "dimensions": self.dimension_columns.copy(),
            "metrics": {
                column: str(self.column_config[column]["aggregation"])
                for column in self.metric_columns
            },
            "masked_columns": [
                column
                for column in self.dimension_columns
                if self.column_config[column]["mask"]
            ],
        }
        threading.Thread(
            target=self._mask_worker,
            args=(job, output_dir, vault_dir, output_path, vault_path),
            daemon=True,
        ).start()

    def _mask_worker(
        self,
        job: dict[str, object],
        output_dir: Path,
        vault_dir: Path,
        output_path: Path,
        vault_path: Path,
    ) -> None:
        try:
            dimensions = job["dimensions"]
            metrics = job["metrics"]
            masked_columns = job["masked_columns"]
            key = generate_masking_key()
            result = mask_and_aggregate(
                job["data"], dimensions, metrics, masked_columns, key
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            vault_dir.mkdir(parents=True, exist_ok=True)
            temporary_output = output_path.with_name(
                f".{output_path.stem}.tmp{output_path.suffix}"
            )
            context_path = save_masked_package(
                result.data, temporary_output, str(job["context_text"])
            )
            write_vault(
                vault_path,
                job["password"],
                key,
                result.mappings,
                {
                    "source_name": job["source_name"],
                    "masked_file_name": output_path.name,
                    "dimensions": dimensions,
                    "metrics": metrics,
                    "masked_columns": masked_columns,
                },
            )
            os.replace(temporary_output, output_path)
            if context_path is not None:
                final_context_path = output_path.with_name(
                    f"{output_path.stem}_context.txt"
                )
                os.replace(context_path, final_context_path)
            else:
                final_context_path = None
                stale_context_path = output_path.with_name(
                    f"{output_path.stem}_context.txt"
                )
                if output_path.suffix.lower() == ".csv" and stale_context_path.exists():
                    stale_context_path.unlink()
            self.after(
                0,
                lambda: self._mask_complete(
                    output_path,
                    vault_path,
                    len(result.data),
                    bool(job["context_text"]),
                    final_context_path,
                ),
            )
        except Exception as exc:
            self.after(0, lambda exc=exc: self._show_error("Masking failed", exc))

    def _mask_complete(
        self,
        output_path: Path,
        vault_path: Path,
        row_count: int,
        context_included: bool,
        context_path: Path | None,
    ) -> None:
        self.password_var.set("")
        self.confirm_password_var.set("")
        self._set_busy(False, f"Complete. Saved {row_count:,} rows.")
        context_message = ""
        if context_included:
            context_message = (
                "\n\nContext layer: included as the Context_Layer tab."
                if context_path is None
                else f"\n\nContext file:\n{context_path}"
            )
        messagebox.showinfo(
            "Masking complete",
            f"Masked data:\n{output_path}\n\nEncrypted vault:\n{vault_path}\n\n"
            f"Keep these files and the password separate.{context_message}",
        )

    def _start_restore(self) -> None:
        data_path = Path(self.restore_data_var.get().strip())
        vault_path = Path(self.restore_vault_var.get().strip())
        output_path = Path(self.restore_output_var.get().strip())
        if not data_path.is_file() or not vault_path.is_file():
            messagebox.showerror(APP_NAME, "Choose an existing masked data file and vault.")
            return
        if not output_path.name:
            messagebox.showerror(APP_NAME, "Choose where to save the restored file.")
            return
        if not self.restore_password_var.get():
            messagebox.showerror(APP_NAME, "Enter the vault password.")
            return
        mapper_path = (
            output_path.with_name(f"{output_path.stem}_mapper.csv")
            if output_path.suffix.lower() == ".csv"
            else None
        )
        existing_outputs = output_path.exists() or (
            mapper_path is not None and mapper_path.exists()
        )
        if existing_outputs and not messagebox.askyesno(
            APP_NAME, "Replace the existing restored output and mapper?"
        ):
            return
        self._set_busy(True, "Decrypting vault and restoring authorized values...")
        threading.Thread(
            target=self._restore_worker,
            args=(data_path, vault_path, output_path, self.restore_password_var.get()),
            daemon=True,
        ).start()

    def _restore_worker(
        self,
        data_path: Path,
        vault_path: Path,
        output_path: Path,
        password: str,
    ) -> None:
        try:
            data = load_dataframe(data_path)
            payload = read_vault(vault_path, password)
            result = restore_dataframe_checked(data, payload["mappings"])
            mapper_path = save_restored_package(
                result.data, payload["mappings"], output_path
            )
            self.after(
                0,
                lambda: self._restore_complete(
                    output_path,
                    len(result.data),
                    result.restored_columns,
                    result.restored_values,
                    mapper_path,
                ),
            )
        except Exception as exc:
            self.after(0, lambda exc=exc: self._show_error("Restore failed", exc))

    def _restore_complete(
        self,
        output_path: Path,
        row_count: int,
        restored_columns: list[str],
        restored_values: int,
        mapper_path: Path | None,
    ) -> None:
        self.restore_password_var.set("")
        self._set_busy(False, f"Restored {row_count:,} rows.")
        columns = ", ".join(restored_columns)
        mapper_message = (
            "\n\nMapper tab included in the workbook."
            if mapper_path is None
            else f"\n\nMapper CSV:\n{mapper_path}"
        )
        messagebox.showinfo(
            "Restore complete",
            f"Restored {restored_values:,} value(s) in: {columns}\n\n"
            f"Saved {row_count:,} rows to:\n{output_path}"
            f"{mapper_message}",
        )

    def _set_busy(self, busy: bool, message: str) -> None:
        self.status_var.set(message)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _show_error(self, title: str, error: Exception) -> None:
        self._set_busy(False, str(error))
        messagebox.showerror(title, str(error))


def main() -> None:
    try:
        app = DataMaskingApp()
        error_path = APP_DIR / "startup-error.log"
        if error_path.exists():
            error_path.unlink()
        app.mainloop()
    except Exception as exc:
        error_path = APP_DIR / "startup-error.log"
        error_path.write_text(traceback.format_exc(), encoding="utf-8")
        _native_error(
            "Local Data Masking Tool",
            f"The app could not start:\n\n{exc}\n\nDetails were saved to:\n{error_path}",
        )
        raise


if __name__ == "__main__":
    main()
