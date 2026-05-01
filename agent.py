"""
agent.py — Startup agent.
On boot: capture webcam photo → upload to Cloudflare R2 → done.
"""

import os
import sys
import time
import logging
import tempfile
from pathlib import Path
from datetime import datetime

# ── R2 CONFIG — FILL THESE ────────────────────────────────────────────────────
R2_ACCOUNT_ID   = ""   # ✅ done
R2_ACCESS_KEY   = ""
R2_SECRET_KEY   = ""
R2_BUCKET_NAME  = ""
R2_FOLDER       = ""           # folder inside bucket (can change)
# ─────────────────────────────────────────────────────────────────────────────

STARTUP_DELAY = 30    # seconds wait after boot for system to settle
RETRY_COUNT   = 3
RETRY_WAIT    = 10

APP_NAME  = "MyBackgroundAgent"
LOG_DIR   = Path.home() / "AppData" / "Local" / APP_NAME
LOG_FILE  = LOG_DIR / "agent.log"
LOCK_FILE = Path(tempfile.gettempdir()) / f"{APP_NAME}.lock"
TEMP_PHOTO = Path(tempfile.gettempdir()) / "startup_capture.jpg"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(APP_NAME)


# ── SINGLE INSTANCE LOCK ──────────────────────────────────────────────────────
def acquire_lock():
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            os.kill(pid, 0)
            log.warning(f"Already running (PID {pid}). Exiting.")
            return False
        except (ProcessLookupError, ValueError):
            pass
    LOCK_FILE.write_text(str(os.getpid()))
    return True

def release_lock():
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  TASK 1 — Capture Webcam Photo (temp file, not saved to desktop)
# ══════════════════════════════════════════════════════════════════════════════
def task_capture_photo() -> Path | None:
    log.info("=== TASK: Capture Webcam Photo ===")

    try:
        import cv2
    except ImportError:
        log.error("opencv-python not installed. Run: pip install opencv-python")
        return None

    cap = None
    for idx in range(3):
        for attempt in range(1, RETRY_COUNT + 1):
            try:
                log.info(f"Trying camera index {idx}, attempt {attempt}...")
                c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if c.isOpened():
                    cap = c
                    log.info(f"Camera opened at index {idx}.")
                    break
                c.release()
            except Exception as e:
                log.warning(f"Camera {idx} attempt {attempt} error: {e}")
            time.sleep(3)
        if cap:
            break

    if cap is None or not cap.isOpened():
        log.error("Could not open camera. Check Windows camera privacy settings.")
        return None

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Warmup — discard 10 frames so exposure adjusts
        log.info("Warming up camera...")
        for _ in range(10):
            cap.read()
            time.sleep(0.1)

        ret, frame = cap.read()
        if not ret or frame is None:
            log.error("Camera returned empty frame.")
            return None

        # Save to TEMP only (not desktop)
        cv2.imwrite(str(TEMP_PHOTO), frame)
        log.info(f"Photo captured to temp: {TEMP_PHOTO}")
        return TEMP_PHOTO

    except Exception as e:
        log.error(f"Capture error: {e}")
        return None

    finally:
        cap.release()


# ══════════════════════════════════════════════════════════════════════════════
#  TASK 2 — Upload Photo to Cloudflare R2
# ══════════════════════════════════════════════════════════════════════════════
def task_upload_to_r2(photo_path: Path) -> bool:
    log.info("=== TASK: Upload to Cloudflare R2 ===")

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        log.error("boto3 not installed. Run: pip install boto3")
        return False

    endpoint = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name="auto",
        )

        timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        object_key  = f"{R2_FOLDER}/photo_{timestamp}.jpg"

        log.info(f"Uploading to R2 bucket '{R2_BUCKET_NAME}' → {object_key}")

        for attempt in range(1, RETRY_COUNT + 1):
            try:
                s3.upload_file(
                    str(photo_path),
                    R2_BUCKET_NAME,
                    object_key,
                    ExtraArgs={"ContentType": "image/jpeg"},
                )
                log.info(f"Upload success: {object_key}")
                return True
            except (BotoCoreError, ClientError) as e:
                log.error(f"Upload attempt {attempt} failed: {e}")
                if attempt < RETRY_COUNT:
                    time.sleep(RETRY_WAIT)

        log.error("All upload attempts failed.")
        return False

    except Exception as e:
        log.error(f"R2 client error: {e}")
        return False

    finally:
        # Delete temp photo regardless of upload result
        try:
            photo_path.unlink(missing_ok=True)
            log.info("Temp photo deleted.")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if not acquire_lock():
        sys.exit(0)

    log.info("Agent started.")

    try:
        log.info(f"Waiting {STARTUP_DELAY}s for system to settle...")
        time.sleep(STARTUP_DELAY)

        photo = task_capture_photo()

        if photo and photo.exists():
            task_upload_to_r2(photo)
        else:
            log.error("No photo captured. Skipping upload.")

    finally:
        release_lock()
        log.info("All tasks done. Agent exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()