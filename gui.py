from __future__ import annotations

import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import main


class LogRedirector:
    def __init__(self, queue_obj, orig_stream):
        self.queue = queue_obj
        self.orig_stream = orig_stream

    def write(self, text):
        if text:
            self.queue.put(("log", text))
            try:
                self.orig_stream.write(text)
                self.orig_stream.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self.orig_stream.flush()
        except Exception:
            pass


class SketchfabUnlockerApp:
    BG_ROOT = "#0B0E14"
    BG_CARD = "#151922"
    BORDER = "#252D3D"
    ACCENT = "#6366F1"
    ACCENT_HOVER = "#4F46E5"
    ACCENT_ACTIVE = "#4338CA"
    TEXT_MAIN = "#F3F4F6"
    TEXT_MUTED = "#9CA3AF"
    TEXT_LOG = "#8B949E"
    BG_LOG = "#0C1017"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    BTN_SECONDARY_BG = "#252D3D"
    BTN_SECONDARY_HOVER = "#323B4E"
    BTN_SECONDARY_ACTIVE = "#1F2633"
    BTN_DISABLED_BG = "#1A202C"
    BTN_DISABLED_FG = "#4B5563"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.queue = queue.Queue()
        self.is_busy = False
        self.current_worker = None

        self.font_family = self._detect_font_family()
        self._check_environment()
        self._setup_window()
        self._setup_styles()
        self._build_ui()
        self._setup_streams()
        self._log_initial_status()

        self.root.after(50, self._poll_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _detect_font_family(self) -> str:
        try:
            fams = tkfont.families()
            if "Segoe UI Variable Display" in fams:
                return "Segoe UI Variable Display"
            if "Segoe UI" in fams:
                return "Segoe UI"
        except Exception:
            pass
        return "Arial"

    def _check_environment(self) -> None:
        self.node_path = shutil.which("node") or shutil.which("nodejs")
        self.node_ready = bool(self.node_path)
        worker, wasm_file = main._wasm_decrypt_paths()
        self.wasm_ready = bool(worker and wasm_file)

    def _setup_window(self) -> None:
        self.root.title("Sketchfab Unlocker")
        self.root.minsize(600, 550)
        self.root.configure(bg=self.BG_ROOT)

        w, h = 740, 720
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _setup_styles(self) -> None:
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=self.BG_ROOT,
            background=self.ACCENT,
            bordercolor=self.BORDER,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
        )
        self.style.configure(
            "Dark.Vertical.TScrollbar",
            troughcolor=self.BG_ROOT,
            background=self.BORDER,
            bordercolor=self.BG_ROOT,
            arrowcolor=self.TEXT_MUTED,
        )
        self.style.map(
            "Dark.Vertical.TScrollbar",
            background=[("active", self.BTN_SECONDARY_HOVER), ("pressed", self.BTN_SECONDARY_ACTIVE)],
        )

    def create_button(
        self,
        parent,
        text,
        command,
        bg="#252D3D",
        fg="#F3F4F6",
        hover_bg="#323B4E",
        active_bg="#1F2633",
        font=None,
        padx=12,
        pady=6,
    ) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=font or (self.font_family, 9, "bold"),
            cursor="hand2",
            padx=padx,
            pady=pady,
        )
        btn.default_bg = bg
        btn.hover_bg = hover_bg
        btn.default_fg = fg

        def on_enter(e):
            if str(btn["state"]) != "disabled":
                btn.configure(bg=btn.hover_bg)

        def on_leave(e):
            if str(btn["state"]) != "disabled":
                btn.configure(bg=btn.default_bg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def set_button_enabled(self, btn: tk.Button, enabled: bool, bg=None, fg=None) -> None:
        if enabled:
            use_bg = bg if bg is not None else getattr(btn, "default_bg", self.BTN_SECONDARY_BG)
            use_fg = fg if fg is not None else getattr(btn, "default_fg", self.TEXT_MAIN)
            btn.configure(state="normal", bg=use_bg, fg=use_fg, cursor="hand2")
        else:
            use_bg = bg if bg is not None else self.BTN_DISABLED_BG
            use_fg = fg if fg is not None else self.BTN_DISABLED_FG
            btn.configure(state="disabled", bg=use_bg, fg=use_fg, cursor="")

    def _build_ui(self) -> None:
        main_container = tk.Frame(self.root, bg=self.BG_ROOT)
        main_container.pack(fill="both", expand=True, padx=20, pady=16)

        header_frame = tk.Frame(main_container, bg=self.BG_ROOT)
        header_frame.pack(fill="x", pady=(0, 14))

        header_left = tk.Frame(header_frame, bg=self.BG_ROOT)
        header_left.pack(side="left")

        title_lbl = tk.Label(
            header_left,
            text="Sketchfab Unlocker",
            font=(self.font_family, 16, "bold"),
            fg=self.TEXT_MAIN,
            bg=self.BG_ROOT,
        )
        title_lbl.pack(side="left")

        badge_lbl = tk.Label(
            header_left,
            text="v2.0 Portable",
            font=(self.font_family, 8, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.BORDER,
            padx=8,
            pady=2,
        )
        badge_lbl.pack(side="left", padx=(10, 0))

        header_right = tk.Frame(header_frame, bg=self.BG_ROOT)
        header_right.pack(side="right")

        node_fg = self.SUCCESS if self.node_ready else self.ERROR
        node_lbl = tk.Label(
            header_right,
            text=f"● Node.js: {'Ready' if self.node_ready else 'Missing'}",
            font=(self.font_family, 9, "bold"),
            fg=node_fg,
            bg=self.BG_CARD,
            padx=10,
            pady=4,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        node_lbl.pack(side="left", padx=(0, 8))

        wasm_fg = self.SUCCESS if self.wasm_ready else self.ERROR
        wasm_lbl = tk.Label(
            header_right,
            text=f"● WASM: {'Ready' if self.wasm_ready else 'Missing'}",
            font=(self.font_family, 9, "bold"),
            fg=wasm_fg,
            bg=self.BG_CARD,
            padx=10,
            pady=4,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        wasm_lbl.pack(side="left")

        input_card = tk.Frame(
            main_container,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        input_card.pack(fill="x", pady=(0, 12))

        input_inner = tk.Frame(input_card, bg=self.BG_CARD, padx=14, pady=12)
        input_inner.pack(fill="x")

        input_top = tk.Frame(input_inner, bg=self.BG_CARD)
        input_top.pack(fill="x", pady=(0, 8))

        input_lbl = tk.Label(
            input_top,
            text="Ссылка на 3D-модель (или несколько ссылок):",
            font=(self.font_family, 10, "bold"),
            fg=self.TEXT_MAIN,
            bg=self.BG_CARD,
        )
        input_lbl.pack(side="left")

        input_actions = tk.Frame(input_top, bg=self.BG_CARD)
        input_actions.pack(side="right")

        self.paste_btn = self.create_button(
            input_actions,
            text="Вставить из буфера",
            command=self.paste_clipboard,
            bg=self.BTN_SECONDARY_BG,
            hover_bg=self.BTN_SECONDARY_HOVER,
            active_bg=self.BTN_SECONDARY_ACTIVE,
            fg=self.TEXT_MAIN,
            font=(self.font_family, 8, "bold"),
            padx=10,
            pady=4,
        )
        self.paste_btn.pack(side="left", padx=(0, 6))

        self.clear_btn = self.create_button(
            input_actions,
            text="Очистить",
            command=self.clear_urls,
            bg=self.BTN_SECONDARY_BG,
            hover_bg=self.BTN_SECONDARY_HOVER,
            active_bg=self.BTN_SECONDARY_ACTIVE,
            fg=self.TEXT_MAIN,
            font=(self.font_family, 8, "bold"),
            padx=10,
            pady=4,
        )
        self.clear_btn.pack(side="left")

        self.url_text = tk.Text(
            input_inner,
            height=3,
            font=(self.font_family, 9),
            bg=self.BG_ROOT,
            fg=self.TEXT_MAIN,
            insertbackground=self.TEXT_MAIN,
            relief="flat",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            highlightcolor=self.ACCENT,
            padx=8,
            pady=6,
            wrap="word",
        )
        self.url_text.pack(fill="x")

        settings_card = tk.Frame(
            main_container,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        settings_card.pack(fill="x", pady=(0, 12))

        settings_inner = tk.Frame(settings_card, bg=self.BG_CARD, padx=14, pady=12)
        settings_inner.pack(fill="x")

        row1 = tk.Frame(settings_inner, bg=self.BG_CARD)
        row1.pack(fill="x", pady=(0, 10))

        dir_lbl = tk.Label(
            row1,
            text="Папка сохранения:",
            font=(self.font_family, 9, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.BG_CARD,
            width=16,
            anchor="w",
        )
        dir_lbl.pack(side="left")

        self.out_dir_var = tk.StringVar(value=str(main.DOWNLOADS))
        self.out_dir_entry = tk.Entry(
            row1,
            textvariable=self.out_dir_var,
            font=(self.font_family, 9),
            bg=self.BG_ROOT,
            fg=self.TEXT_MAIN,
            insertbackground=self.TEXT_MAIN,
            relief="flat",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            highlightcolor=self.ACCENT,
        )
        self.out_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = self.create_button(
            row1,
            text="Обзор...",
            command=self.browse_output_dir,
            bg=self.BTN_SECONDARY_BG,
            hover_bg=self.BTN_SECONDARY_HOVER,
            active_bg=self.BTN_SECONDARY_ACTIVE,
            fg=self.TEXT_MAIN,
            font=(self.font_family, 8, "bold"),
            padx=10,
            pady=4,
        )
        self.browse_btn.pack(side="left", padx=(0, 6))

        self.open_folder_btn = self.create_button(
            row1,
            text="Открыть папку",
            command=self.open_output_dir,
            bg=self.BTN_SECONDARY_BG,
            hover_bg=self.BTN_SECONDARY_HOVER,
            active_bg=self.BTN_SECONDARY_ACTIVE,
            fg=self.TEXT_MAIN,
            font=(self.font_family, 8, "bold"),
            padx=10,
            pady=4,
        )
        self.open_folder_btn.pack(side="left")

        row2 = tk.Frame(settings_inner, bg=self.BG_CARD)
        row2.pack(fill="x")

        self.clean_var = tk.BooleanVar(value=True)
        clean_cb = tk.Checkbutton(
            row2,
            text="Очищать временные файлы (.key, .osgjs)",
            variable=self.clean_var,
            bg=self.BG_CARD,
            fg=self.TEXT_MAIN,
            selectcolor=self.BG_ROOT,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_MAIN,
            font=(self.font_family, 9),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        clean_cb.pack(side="left")

        proxy_container = tk.Frame(row2, bg=self.BG_CARD)
        proxy_container.pack(side="right")

        proxy_lbl = tk.Label(
            proxy_container,
            text="Прокси:",
            font=(self.font_family, 9, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.BG_CARD,
        )
        proxy_lbl.pack(side="left", padx=(0, 6))

        self.proxy_var = tk.StringVar(value="")
        self.proxy_entry = tk.Entry(
            proxy_container,
            textvariable=self.proxy_var,
            font=(self.font_family, 9),
            bg=self.BG_ROOT,
            fg=self.TEXT_MAIN,
            insertbackground=self.TEXT_MAIN,
            relief="flat",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            highlightcolor=self.ACCENT,
            width=24,
        )
        self.proxy_entry.pack(side="left")

        action_frame = tk.Frame(main_container, bg=self.BG_ROOT)
        action_frame.pack(fill="x", pady=(0, 12))

        self.download_btn = self.create_button(
            action_frame,
            text="Скачать модель",
            command=self.start_download,
            bg=self.ACCENT,
            hover_bg=self.ACCENT_HOVER,
            active_bg=self.ACCENT_ACTIVE,
            fg="#FFFFFF",
            font=(self.font_family, 11, "bold"),
            pady=9,
        )
        self.download_btn.pack(fill="x", pady=(0, 8))

        progress_info_frame = tk.Frame(action_frame, bg=self.BG_ROOT)
        progress_info_frame.pack(fill="x", pady=(0, 4))

        self.status_label = tk.Label(
            progress_info_frame,
            text="Готов к загрузке",
            font=(self.font_family, 9),
            fg=self.TEXT_MUTED,
            bg=self.BG_ROOT,
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.step_label = tk.Label(
            progress_info_frame,
            text="0%",
            font=(self.font_family, 9, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.BG_ROOT,
            anchor="e",
        )
        self.step_label.pack(side="right")

        self.progress_bar = ttk.Progressbar(
            action_frame,
            style="Dark.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )
        self.progress_bar.pack(fill="x")

        log_card = tk.Frame(
            main_container,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )
        log_card.pack(fill="both", expand=True)

        log_inner = tk.Frame(log_card, bg=self.BG_CARD, padx=14, pady=10)
        log_inner.pack(fill="both", expand=True)

        log_top = tk.Frame(log_inner, bg=self.BG_CARD)
        log_top.pack(fill="x", pady=(0, 6))

        log_lbl = tk.Label(
            log_top,
            text="Журнал операций:",
            font=(self.font_family, 9, "bold"),
            fg=self.TEXT_MUTED,
            bg=self.BG_CARD,
        )
        log_lbl.pack(side="left")

        clear_log_btn = self.create_button(
            log_top,
            text="Очистить",
            command=self.clear_log,
            bg=self.BTN_SECONDARY_BG,
            hover_bg=self.BTN_SECONDARY_HOVER,
            active_bg=self.BTN_SECONDARY_ACTIVE,
            fg=self.TEXT_MAIN,
            font=(self.font_family, 8, "bold"),
            padx=8,
            pady=3,
        )
        clear_log_btn.pack(side="right")

        text_container = tk.Frame(log_inner, bg=self.BG_LOG)
        text_container.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            text_container,
            font=("Consolas", 9),
            bg=self.BG_LOG,
            fg=self.TEXT_LOG,
            insertbackground=self.TEXT_MAIN,
            relief="flat",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            wrap="word",
            padx=8,
            pady=8,
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            text_container,
            orient="vertical",
            command=self.log_text.yview,
            style="Dark.Vertical.TScrollbar",
        )
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.tag_configure("success", foreground=self.SUCCESS, font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("warning", foreground=self.WARNING)
        self.log_text.tag_configure("error", foreground=self.ERROR, font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("accent", foreground="#818CF8")
        self.log_text.tag_configure("normal", foreground=self.TEXT_LOG)
        self.log_text.configure(state="disabled")

    def _setup_streams(self) -> None:
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        sys.stdout = LogRedirector(self.queue, self.orig_stdout)
        sys.stderr = LogRedirector(self.queue, self.orig_stderr)

    def _log_initial_status(self) -> None:
        self.append_log("Sketchfab Unlocker v2.0 Portable\n")
        self.append_log(f"Node.js: {'Ready' if self.node_ready else 'Missing'}\n")
        self.append_log(f"WASM Decryptor: {'Ready' if self.wasm_ready else 'Missing'}\n")
        self.append_log(f"Папка сохранения: {self.out_dir_var.get()}\n")
        self.append_log("Готов к работе.\n\n")

    def paste_clipboard(self) -> None:
        try:
            content = self.root.clipboard_get()
            if content:
                current = self.url_text.get("1.0", tk.END).strip()
                if current:
                    self.url_text.insert(tk.END, "\n" + content.strip())
                else:
                    self.url_text.delete("1.0", tk.END)
                    self.url_text.insert(tk.END, content.strip())
                self.set_status("Ссылка вставлена из буфера обмена", self.TEXT_MUTED)
        except Exception:
            pass

    def clear_urls(self) -> None:
        self.url_text.delete("1.0", tk.END)
        self.set_status("Поле ссылок очищено", self.TEXT_MUTED)

    def browse_output_dir(self) -> None:
        current = self.out_dir_var.get().strip() or str(main.DOWNLOADS)
        chosen = filedialog.askdirectory(initialdir=current, title="Выберите папку для сохранения моделей")
        if chosen:
            self.out_dir_var.set(chosen)

    def open_output_dir(self) -> None:
        out_dir_str = self.out_dir_var.get().strip()
        dest = Path(out_dir_str) if out_dir_str else main.DOWNLOADS
        dest.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(dest)
            else:
                subprocess.run(["xdg-open", str(dest)], check=False)
        except Exception as e:
            self.append_log(f"Не удалось открыть папку: {e}\n")

    def clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def set_status(self, text: str, color=None, progress_val=None) -> None:
        self.status_label.configure(text=text, fg=color or self.TEXT_MUTED)
        if progress_val is not None:
            val = max(0, min(100, progress_val))
            self.progress_bar["value"] = val
            self.step_label.configure(text=f"{int(val)}%")

    def append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        for line in text.splitlines(keepends=True):
            stripped = line.strip()
            tag = "normal"
            if stripped.startswith("✓") or "done" in stripped.lower() or "успешно" in stripped.lower():
                tag = "success"
            elif stripped.startswith("⚠") or "warning" in stripped.lower() or "внимание" in stripped.lower():
                tag = "warning"
            elif "error" in stripped.lower() or "ошибка" in stripped.lower() or "failed" in stripped.lower():
                tag = "error"
            elif stripped.startswith("$") or stripped.startswith("[") or stripped.startswith("↓") or stripped.startswith("==="):
                tag = "accent"
            self.log_text.insert(tk.END, line, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def set_busy_state(self, is_busy: bool) -> None:
        self.is_busy = is_busy
        if is_busy:
            self.set_button_enabled(self.download_btn, False, self.BTN_DISABLED_BG, self.BTN_DISABLED_FG)
            self.set_button_enabled(self.paste_btn, False)
            self.set_button_enabled(self.clear_btn, False)
            self.set_button_enabled(self.browse_btn, False)
            self.url_text.configure(state="disabled")
            self.root.config(cursor="wait")
        else:
            self.set_button_enabled(self.download_btn, True, self.ACCENT, "#FFFFFF")
            self.set_button_enabled(self.paste_btn, True)
            self.set_button_enabled(self.clear_btn, True)
            self.set_button_enabled(self.browse_btn, True)
            self.url_text.configure(state="normal")
            self.root.config(cursor="")

    def handle_step(self, token: str, model_index: int = 0, total_models: int = 1) -> None:
        step_base = 0
        step_text = ""
        color = self.TEXT_MUTED

        if token.startswith("step:viewer"):
            step_text = "Получение информации о модели..."
            step_base = 15
        elif token.startswith("step:model"):
            parts = token.split("|")
            name = parts[1] if len(parts) > 1 else ""
            author = parts[2] if len(parts) > 2 else ""
            if name and author:
                step_text = f"Модель: {name} ({author})"
            elif name:
                step_text = f"Модель: {name}"
            else:
                step_text = "Модель обнаружена"
            color = self.TEXT_MAIN
            step_base = 25
        elif token.startswith("step:format"):
            step_text = "Анализ структуры мешей..."
            step_base = 35
        elif token.startswith("step:keys"):
            step_text = "Получение ключей расшифровки..."
            step_base = 45
        elif token.startswith("step:legacy"):
            step_text = "Подготовка архивов..."
            step_base = 50
        elif token.startswith("step:mesh"):
            step_text = "Загрузка геометрии..."
            step_base = 60
        elif token.startswith("step:decrypt"):
            step_text = "Расшифровка..."
            step_base = 75
        elif token.startswith("step:textures"):
            step_text = "Загрузка текстур..."
            step_base = 85
        elif token.startswith("step:textures_warn"):
            step_text = "Загрузка текстур (с предупреждениями)..."
            color = self.WARNING
            step_base = 88
        elif token.startswith("step:export"):
            step_text = "Конвертация в glTF..."
            step_base = 95
        elif token.startswith("step:done"):
            step_text = "Конвертация в glTF... Готово!"
            color = self.SUCCESS
            step_base = 100

        if total_models > 1:
            full_text = f"[{model_index + 1}/{total_models}] {step_text}"
            model_slice = 100.0 / total_models
            overall_progress = (model_index * model_slice) + (step_base / 100.0 * model_slice)
        else:
            full_text = step_text
            overall_progress = step_base

        self.set_status(full_text, color, overall_progress)

    def start_download(self) -> None:
        raw = self.url_text.get("1.0", tk.END).strip()
        if not raw:
            self.set_status("Введите ссылку на модель Sketchfab", self.WARNING)
            return

        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        urls = []
        for line in lines:
            for token in re.split(r"[\s,;]+", line):
                token = token.strip()
                if not token:
                    continue
                norm = main._normalize_url(token)
                if norm:
                    urls.append(norm)
                elif re.search(r"sketchfab\.com", token, re.I):
                    urls.append(token)
                elif re.fullmatch(r"[a-f0-9]{32}", token, re.I):
                    urls.append(f"https://sketchfab.com/3d-models/{token}")

        urls = list(dict.fromkeys(urls))
        if not urls:
            self.set_status("Не найдено корректных ссылок на Sketchfab", self.WARNING)
            return

        out_dir_str = self.out_dir_var.get().strip()
        out_dir = Path(out_dir_str) if out_dir_str else main.DOWNLOADS
        proxy_val = self.proxy_var.get().strip() or None
        clean_val = self.clean_var.get()

        self.queue.put(("state", "busy"))
        self.set_status("Запуск загрузки...", self.TEXT_MUTED, 5)

        def worker():
            success_count = 0
            fail_count = 0
            total = len(urls)
            for idx, url in enumerate(urls):
                if total > 1:
                    self.queue.put(("status", f"[{idx + 1}/{total}] Инициализация {url}...", self.TEXT_MUTED, int(idx / total * 100)))
                    self.queue.put(("log", f"\n=== [{idx + 1}/{total}] {url} ===\n"))
                try:
                    result = main.download_one(
                        url,
                        out_root=out_dir,
                        proxy=proxy_val,
                        progress=lambda token, m_idx=idx, m_tot=total: self.queue.put(("step", token, m_idx, m_tot)),
                        clean_output=clean_val,
                    )
                    success_count += 1
                    model_name = result.get("name") or Path(result["path"]).stem
                    self.queue.put(("log", f"✓ Модель '{model_name}' успешно сохранена: {result['path']}\n"))
                except Exception as e:
                    fail_count += 1
                    self.queue.put(("log", f"ERROR: Ошибка при скачивании {url}: {e}\n"))
                    if total == 1:
                        self.queue.put(("status", f"Ошибка: {e}", self.ERROR, 0))

            if total > 1:
                if fail_count == 0:
                    self.queue.put(("status", f"Все модели успешно скачаны ({success_count}/{total})!", self.SUCCESS, 100))
                else:
                    self.queue.put(("status", f"Завершено: {success_count} успешно, {fail_count} с ошибками", self.WARNING, 100))
            elif success_count == 1:
                self.queue.put(("status", "Готово! Модель успешно скачана.", self.SUCCESS, 100))

            self.queue.put(("state", "idle"))

        self.current_worker = threading.Thread(target=worker, daemon=True)
        self.current_worker.start()

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self.queue.get_nowait()
                msg_type = item[0]
                if msg_type == "log":
                    self.append_log(item[1])
                elif msg_type == "step":
                    token = item[1]
                    m_idx = item[2] if len(item) > 2 else 0
                    m_tot = item[3] if len(item) > 3 else 1
                    self.handle_step(token, m_idx, m_tot)
                elif msg_type == "status":
                    text = item[1]
                    color = item[2] if len(item) > 2 else self.TEXT_MUTED
                    prog = item[3] if len(item) > 3 else None
                    self.set_status(text, color, prog)
                elif msg_type == "state":
                    self.set_busy_state(item[1] == "busy")
        except queue.Empty:
            pass
        self.root.after(50, self._poll_queue)

    def _on_close(self) -> None:
        try:
            sys.stdout = self.orig_stdout
            sys.stderr = self.orig_stderr
        except Exception:
            pass
        self.root.destroy()


def main_gui() -> int:
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    root = tk.Tk()
    app = SketchfabUnlockerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main_gui())
