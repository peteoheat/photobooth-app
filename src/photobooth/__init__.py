import json
import locale
import os
import re
import subprocess
from pathlib import Path

# set locale to systems default
locale.setlocale(locale.LC_ALL, "")

# folder not touched, used by user
USERDATA_PATH = "./userdata/"
# logfiles
LOG_PATH = "./log/"
# configuration
CONFIG_PATH = "./config/"


def sanitize_event_name(event_name: str | None) -> str:
    """reduce event name to a filesystem-safe folder name. Empty result means no event is active."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", (event_name or "").strip())


def _read_active_event_name() -> str:
    """Read common.event_name directly from config.json. AppConfig cannot be used here because it depends on the paths defined in
    this module. Any problem reading the file results in no event active, the AppConfig validation later reports broken configs."""
    try:
        with open(f"{CONFIG_PATH}config.json", encoding="utf-8") as config_file:
            return sanitize_event_name(json.load(config_file).get("common", {}).get("event_name", ""))
    except Exception:
        return ""


# event the app was started with. Changing the event in config requires a restart to take effect.
ACTIVE_EVENT_NAME = _read_active_event_name()
# no event set keeps the original layout in the app's root dir, so existing installations are unaffected
EVENT_PATH = f"./events/{ACTIVE_EVENT_NAME}/" if ACTIVE_EVENT_NAME else "./"

# database
DATABASE_PATH = f"{EVENT_PATH}database/"
# mediaitems cache for resized versions
CACHE_PATH = f"{EVENT_PATH}cache/"
# media collection files
MEDIA_PATH = f"{EVENT_PATH}media/"
PATH_CAMERA_ORIGINAL = "".join([MEDIA_PATH, "camera_original/"])
PATH_UNPROCESSED = "".join([MEDIA_PATH, "unprocessed_original/"])  # remove later, when clear_all doesnt handle it in later v9 release
PATH_PROCESSED = "".join([MEDIA_PATH, "processed_full/"])
# all other stuff that is used temporarily
TMP_PATH = f"{EVENT_PATH}tmp/"
# recycle dir if delete moves to recycle instead actual removing
RECYCLE_PATH = f"{EVENT_PATH}recycle/"


def _create_basic_folders():
    os.makedirs(DATABASE_PATH, exist_ok=True)
    os.makedirs(CACHE_PATH, exist_ok=True)
    os.makedirs(MEDIA_PATH, exist_ok=True)
    os.makedirs(PATH_CAMERA_ORIGINAL, exist_ok=True)
    os.makedirs(PATH_PROCESSED, exist_ok=True)
    os.makedirs(USERDATA_PATH, exist_ok=True)
    os.makedirs(LOG_PATH, exist_ok=True)
    os.makedirs(CONFIG_PATH, exist_ok=True)
    os.makedirs(TMP_PATH, exist_ok=True)
    os.makedirs(RECYCLE_PATH, exist_ok=True)


def _copy_demo_assets_to_userdata():
    def create_link(src_path: Path, dst_path: Path):
        # https://discuss.python.org/t/add-os-junction-pathlib-path-junction-to/50394

        if os.name == "nt":
            cmd = ["mklink", "/j", os.fsdecode(dst_path), os.fsdecode(src_path)]
            # mklink junction no need for privileges on win systems.

            proc = subprocess.run(cmd, shell=True, capture_output=True)
            if proc.returncode:
                raise OSError(proc.stderr.decode().strip())
        else:
            os.symlink(src_path, dst_path, target_is_directory=True)

    src_path = Path(__file__).parent.resolve().joinpath("demoassets/userdata").absolute()
    dst_path = Path(USERDATA_PATH, "demoassets").absolute()

    if not dst_path.exists():
        create_link(src_path, dst_path)
    elif dst_path.is_symlink() or (os.name == "nt" and dst_path.is_junction()):
        return
    else:
        raise RuntimeError(f"error setup demoassets, {dst_path} exists but is no symlink!")


try:
    _create_basic_folders()
    _copy_demo_assets_to_userdata()
except Exception as exc:
    raise RuntimeError(f"cannot initialize data folders, error: {exc}") from exc
