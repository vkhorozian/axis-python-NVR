import json
import shutil
from pathlib import Path
from urllib.parse import quote


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in the system PATH."""
    return shutil.which("ffmpeg") is not None


def build_rtsp_url_with_auth(
    rtsp_url: str,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """
    Return an RTSP URL with optional credentials.
    If username is set, inserts 'username:password@' after 'rtsp://'.
    Passwords are URL-encoded so special characters work.
    """
    if not username:
        return rtsp_url
    if not rtsp_url.startswith("rtsp://"):
        return rtsp_url
    rest = rtsp_url[7:]  # after "rtsp://"
    safe_user = quote(username, safe="")
    safe_pass = quote(password or "", safe="")
    return f"rtsp://{safe_user}:{safe_pass}@{rest}"


def get_ffmpeg_path() -> str:
    """Get the full path to FFmpeg executable, or raise an error if not found."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise FileNotFoundError(
            "FFmpeg not found in system PATH. Please install FFmpeg and add it to your PATH.\n"
            "Download from: https://ffmpeg.org/download.html"
        )
    return ffmpeg_path
