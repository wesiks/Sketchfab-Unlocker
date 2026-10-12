from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Optional

BUNDLE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parent
CURRENT_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import main


SETTINGS_FILE = CURRENT_DIR / "settings.json"
LOG_FILE = CURRENT_DIR / "sketchfab-unlocker.log"


def log_error(context: str) -> str:
    """Write the current exception (with traceback) to the log file and stderr; return the text."""
    import datetime
    import traceback

    text = traceback.format_exc()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {context}\n{text}\n")
    except OSError:
        pass
    print(text, file=sys.stderr)
    return text
SUPPORTED_LANGS = ("es", "en", "ru")
DEFAULT_LANG = "es"


def load_settings() -> dict[str, Any]:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


class Api:
    def __init__(self):
        self.window = None
        self._cancel_flag = False
        self._is_maximized = False

    def set_window(self, win):
        self.window = win

    def get_initial_state(self) -> dict[str, Any]:
        node_path = shutil.which("node") or shutil.which("nodejs")
        worker, wasm_file = main._wasm_decrypt_paths()
        return {
            "default_output_dir": str(main.DOWNLOADS),
            "language": load_settings().get("language", DEFAULT_LANG),
            "settings": load_settings().get("ui", {}),
            "node_ready": bool(node_path),
            "wasm_ready": bool(worker and wasm_file),
        }

    def set_language(self, lang: str) -> bool:
        if lang not in SUPPORTED_LANGS:
            return False
        try:
            data = load_settings()
            data["language"] = lang
            SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def save_settings(self, ui: dict[str, Any]) -> bool:
        try:
            data = load_settings()
            data["ui"] = ui
            SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def open_url(self, url: str) -> None:
        import webbrowser
        if str(url).startswith(("http://", "https://")):
            webbrowser.open(url)

    def select_folder(self, initial_dir: str = "") -> Optional[str]:
        chosen = None
        try:
            import webview
            target = initial_dir if initial_dir and Path(initial_dir).is_dir() else str(main.DOWNLOADS)
            res = self.window.create_file_dialog(webview.FileDialog.FOLDER, directory=target)
            if res and len(res) > 0:
                chosen = str(res[0])
        except Exception:
            pass

        if not chosen:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                res = filedialog.askdirectory(initialdir=initial_dir or str(main.DOWNLOADS))
                root.destroy()
                if res:
                    chosen = str(res)
            except Exception:
                pass
        return chosen

    def open_folder(self, path: str) -> None:
        try:
            target = Path(path) if path else main.DOWNLOADS
            target.mkdir(parents=True, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(str(target))
            else:
                subprocess.run(["xdg-open", str(target)], check=False)
        except Exception:
            pass

    def open_model_file(self, folder_path: str) -> None:
        try:
            p = Path(folder_path)
            candidates = list(p.glob("*.glb")) + list(p.glob("*.gltf"))
            if candidates:
                if sys.platform.startswith("win"):
                    os.startfile(str(candidates[0]))
                else:
                    subprocess.run(["xdg-open", str(candidates[0])], check=False)
            else:
                self.open_folder(folder_path)
        except Exception:
            pass

    def copy_to_clipboard(self, text: str) -> bool:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return True
        except Exception:
            return False

    def get_clipboard(self) -> str:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text or ""
        except Exception:
            return ""

    def get_my_models(self, save_dir: str) -> list[dict[str, Any]]:
        try:
            p = Path(save_dir) if save_dir else main.DOWNLOADS
            if not p.is_dir():
                return []
            res = []
            for folder in p.iterdir():
                if folder.is_dir():
                    has_model = list(folder.glob("*.gltf")) + list(folder.glob("*.glb"))
                    if has_model or (folder / "info.json").exists():
                        total_bytes = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
                        file_count = sum(1 for f in folder.rglob("*") if f.is_file())
                        if total_bytes >= 1024 * 1024:
                            size_str = f"{total_bytes / (1024 * 1024):.1f} MB"
                        else:
                            size_str = f"{max(1, total_bytes // 1024)} KB"
                        res.append({
                            "name": folder.name,
                            "path": str(folder),
                            "size": size_str,
                            "files": file_count,
                            "mtime": folder.stat().st_mtime
                        })
            res.sort(key=lambda x: x["mtime"], reverse=True)
            return res
        except Exception:
            return []

    def test_proxy(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            import requests
            ptype = str(data.get("type", "SOCKS5")).lower()
            if ptype == "socks5":
                ptype = "socks5h"
            host = str(data.get("host", "")).strip()
            port = str(data.get("port", "")).strip()
            user = str(data.get("user", "")).strip()
            pw = str(data.get("pass", "")).strip()
            if not host or not port:
                return {"success": False, "errorKey": "err.no_host"}
            auth = f"{user}:{pw}@" if user and pw else ""
            proxy_url = f"{ptype}://{auth}{host}:{port}"
            resp = requests.get(
                "https://sketchfab.com",
                headers={"User-Agent": main.USER_AGENT},
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=8,
            )
            if resp.status_code < 400:
                return {"success": True}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)[:120]}

    def minimize_window(self) -> None:
        if self.window:
            self.window.minimize()

    def maximize_window(self) -> None:
        if self.window:
            if self._is_maximized:
                self.window.restore()
                self._is_maximized = False
            else:
                self.window.maximize()
                self._is_maximized = True

    def close_window(self) -> None:
        self._cancel_flag = True
        main.request_cancel()
        if self.window:
            self.window.destroy()

    def cancel_queue(self) -> None:
        self._cancel_flag = True
        main.request_cancel()

    def start_queue(self, payload: dict[str, Any]) -> None:
        items = payload.get("items", [])
        save_path = payload.get("savePath")
        clean_output = payload.get("cleanOutput", True)
        proxy = payload.get("proxy")
        auto_open = payload.get("autoOpen", False)
        download_tex = payload.get("downloadTextures", True)
        keep_materials = payload.get("keepMaterials", True)
        fmt = str(payload.get("format", "glTF")).lower()
        api_token = str(payload.get("apiToken") or "").strip() or None
        converter = payload.get("converter", "auto")
        if converter not in ("auto", "osgconv", "python"):
            converter = "auto"
        self._cancel_flag = False
        main.clear_cancel()

        def worker():
            out_dir = Path(save_path) if save_path else main.DOWNLOADS
            out_dir.mkdir(parents=True, exist_ok=True)
            total = len(items)
            success_count = 0

            for idx, item in enumerate(items):
                if self._cancel_flag:
                    self._send_js("onQueueProgress", {
                        "id": item.get("id"), "uid": item.get("uid"),
                        "status": "queued", "statusKey": "status.queued",
                        "subText": "", "percent": 0
                    })
                    continue
                item_id = item.get("id")
                uid = item.get("uid")
                url = item.get("url") or f"https://sketchfab.com/3d-models/{uid}"

                self._send_js("onQueueProgress", {
                    "id": item_id,
                    "uid": uid,
                    "status": "downloading",
                    "statusKey": "status.preparing",
                    "subKey": "status.initializing",
                    "subParams": {"n": idx + 1, "total": total},
                    "percent": 5
                })

                def make_progress(i_id=item_id, u=uid):
                    def cb(token):
                        if token.startswith("step:model|"):
                            parts = token.split("|")
                            if len(parts) > 1 and parts[1]:
                                self._send_js("onQueueProgress", {"id": i_id, "uid": u, "name": parts[1][:60]})
                        pct = 10
                        msg = "step.default"
                        if "step:official_unavailable" in token:
                            pct, msg = 15, "step.official_unavailable"
                        elif "step:official_download" in token:
                            pct, msg = 60, "step.official_download"
                        elif "step:official" in token:
                            pct, msg = 12, "step.official"
                        elif "step:viewer" in token:
                            pct, msg = 20, "step.viewer"
                        elif "step:model" in token:
                            pct, msg = 30, "step.model"
                        elif "step:keys" in token:
                            pct, msg = 45, "step.keys"
                        elif "step:mesh" in token:
                            pct, msg = 65, "step.mesh"
                        elif "step:decrypt" in token:
                            pct, msg = 78, "step.decrypt"
                        elif "step:textures" in token:
                            pct, msg = 88, "step.textures"
                        elif "step:export" in token:
                            pct, msg = 95, "step.export"
                        elif "step:done" in token:
                            pct, msg = 100, "step.done"
                        self._send_js("onQueueProgress", {
                            "id": i_id,
                            "uid": u,
                            "status": "downloading",
                            "statusKey": "status.downloading_pct",
                            "statusParams": {"pct": pct},
                            "subKey": msg,
                            "percent": pct
                        })
                    return cb

                try:
                    res = main.download_one(
                        url,
                        out_root=out_dir,
                        proxy=proxy,
                        progress=make_progress(item_id, uid),
                        clean_output=clean_output,
                        download_tex=download_tex,
                        keep_materials=keep_materials,
                        fmt=fmt,
                        converter=converter,
                        api_token=api_token,
                    )
                    success_count += 1
                    res_path = Path(res.get("dir") or Path(res["path"]).parent)
                    folder_bytes = sum(f.stat().st_size for f in res_path.rglob("*") if f.is_file())
                    folder_files = sum(1 for f in res_path.rglob("*") if f.is_file())
                    if folder_bytes >= 1024 * 1024:
                        size_text = f"{folder_bytes / (1024 * 1024):.1f} MB"
                    else:
                        size_text = f"{max(1, folder_bytes // 1024)} KB"
                    self._send_js("onQueueProgress", {
                        "id": item_id,
                        "uid": uid,
                        "status": "done",
                        "statusKey": "status.done",
                        "subKey": "status.done_sub",
                        "subParams": {"size": size_text, "count": folder_files},
                        "percent": 100,
                        "name": res.get("name") or res_path.name,
                        "path": str(res_path)
                    })
                except main.Cancelled:
                    self._send_js("onQueueProgress", {
                        "id": item_id, "uid": uid,
                        "status": "queued", "statusKey": "status.queued",
                        "subText": "", "percent": 0
                    })
                    continue
                except Exception as e:
                    detail = log_error(f"download {url}")
                    self._send_js("onQueueProgress", {
                        "id": item_id,
                        "uid": uid,
                        "status": "error",
                        "errorDetail": f"{url}\n{detail}",
                        "statusKey": "status.error",
                        "subText": str(e).strip().splitlines()[-1][:90] if str(e).strip() else type(e).__name__,
                        "percent": 0
                    })

            if auto_open and success_count > 0:
                self.open_folder(str(out_dir))

            self._send_js("onQueueFinish", {
                "cancelled": self._cancel_flag,
                "messageKey": "status.cancelled" if self._cancel_flag else "status.finished",
                "messageParams": {"ok": success_count, "total": total}
            })

        threading.Thread(target=worker, daemon=True).start()

    def _send_js(self, fn_name: str, data: dict[str, Any]) -> None:
        if self.window:
            try:
                payload = json.dumps(data, ensure_ascii=False)
                self.window.evaluate_js(f"window.{fn_name}({payload});")
            except Exception:
                pass


class TkinterFallbackApp:
    BG_ROOT = "#0B0E14"
    BG_CARD = "#151922"
    BORDER = "#252D3D"
    ACCENT = "#2563EB"
    TEXT_MAIN = "#F3F4F6"
    TEXT_MUTED = "#9CA3AF"

    def __init__(self, root):
        self.root = root
        self.root.title("Sketchfab Unlocker")
        self.root.geometry("700x550")
        self.root.configure(bg=self.BG_ROOT)
        lbl = tk.Label(
            self.root,
            text="Sketchfab Unlocker",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_ROOT,
            fg=self.TEXT_MAIN,
        )
        lbl.pack(pady=20)


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

    html_file = BUNDLE_DIR / "ui" / "index.html"
    if not html_file.exists():
        html_file = CURRENT_DIR / "ui" / "index.html"

    try:
        import webview
        api = Api()
        window = webview.create_window(
            title="Sketchfab Unlocker",
            url=str(html_file),
            width=1220,
            height=780,
            frameless=True,
            easy_drag=True,
            min_size=(900, 620),
            background_color="#0B0F19",
            js_api=api
        )
        api.set_window(window)
        webview.start(debug=False)
        return 0
    except Exception:
        import tkinter as tk
        root = tk.Tk()
        app = TkinterFallbackApp(root)
        root.mainloop()
        return 0


if __name__ == "__main__":
    raise SystemExit(main_gui())
