"""
save.py — Cross-platform config file saving.

  Windows / Linux / macOS  →  Desktop → Downloads → home
  Android (APK)            →  /sdcard/Download
  Web                      →  UrlLauncher data: URI  (Flet >= 0.90)
"""

import base64
import datetime
import pathlib
import platform
import sys


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def make_filename(base_name: str = "") -> str:
    ts = _timestamp()
    if base_name:
        return f"{base_name}_{ts}.json"
    return f"proxy_chain_{ts}.json"


def _is_android() -> bool:
    return hasattr(sys, "getandroidapilevel") or (
        platform.system() == "Linux" and (
            pathlib.Path("/sdcard").exists() or
            pathlib.Path("/data/data").exists()
        )
    )


def _is_web(page=None) -> bool:
    """
    Detect web mode reliably.
    page.web is True only in browser builds — not in desktop flet run.
    """
    if page is not None:
        return getattr(page, "web", False)
    return "pyodide" in sys.modules or "flet_web" in sys.modules


async def save_config(json_text: str, page=None, name: str = "") -> tuple[bool, str]:
    """
    Save / download the config. Returns (success, message).
    Must be awaited because the web path uses UrlLauncher (async).
    """
    filename = make_filename(name)

    # ── Web ───────────────────────────────────────────────────────────────────
    if _is_web(page) and page is not None:
        try:
            import flet as ft
            b64      = base64.b64encode(json_text.encode("utf-8")).decode("ascii")
            data_uri = f"data:application/json;base64,{b64}"
            # Flet 0.90+: UrlLauncher takes no constructor args;
            # url is passed to launch_url() or open_url()
            launcher = ft.UrlLauncher()
            page.overlay.append(launcher)
            page.update()
            await launcher.launch_url(data_uri)
            return True, f"DOWNLOAD ✓  {filename}"
        except Exception as ex:
            return False, f"WEB DOWNLOAD ERROR: {ex}"

    # ── Android ───────────────────────────────────────────────────────────────
    if _is_android():
        candidates = [
            pathlib.Path("/sdcard/Download"),
            pathlib.Path("/storage/emulated/0/Download"),
        ]
        for folder in candidates:
            if folder.exists():
                try:
                    path = folder / filename
                    path.write_text(json_text, encoding="utf-8")
                    return True, f"SAVED ✓  {path}"
                except Exception:
                    continue
        try:
            import os
            app_dir = pathlib.Path(os.environ.get("HOME", "/data/local/tmp"))
            path    = app_dir / filename
            path.write_text(json_text, encoding="utf-8")
            return True, f"SAVED ✓  {path}"
        except Exception as ex:
            return False, f"ANDROID SAVE ERROR: {ex}"

    # ── Windows / Linux / macOS ───────────────────────────────────────────────
    for folder in [
        pathlib.Path.home() / "Desktop",
        pathlib.Path.home() / "Downloads",
        pathlib.Path.home(),
        pathlib.Path.cwd(),
    ]:
        if folder.exists():
            try:
                path = folder / filename
                path.write_text(json_text, encoding="utf-8")
                return True, str(path)        # full absolute path
            except Exception:
                continue

    return False, "SAVE FAILED: no writable folder found"