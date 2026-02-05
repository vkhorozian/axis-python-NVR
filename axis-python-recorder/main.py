import multiprocessing
import signal
import sys
from pathlib import Path

from recorder.ffmpeg_recorder import FFmpegRecorder
from recorder.utils import (
    check_ffmpeg_available,
    load_config,
    build_rtsp_url_with_auth,
)


def run_camera_process(camera_name: str, rtsp_url: str, base_dir: str, segment_seconds: int):
    """Entry point for each camera process: runs the recorder loop."""
    recorder = FFmpegRecorder(
        camera_name=camera_name,
        rtsp_url=rtsp_url,
        base_dir=Path(base_dir),
    )
    recorder.record_loop(segment_seconds=segment_seconds)


def main():
    # Check FFmpeg availability before proceeding
    if not check_ffmpeg_available():
        print("[ERROR] FFmpeg not found in system PATH.")
        print("Please install FFmpeg and add it to your PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Get the script's directory to resolve paths relative to the script location
    script_dir = Path(__file__).parent
    config_path = script_dir / "config" / "cameras.json"
    config = load_config(config_path)
    
    # Resolve recordings_dir relative to script directory
    recordings_dir = script_dir / config["recordings_dir"]
    segment_minutes = config.get("segment_minutes", 15)
    segment_seconds = segment_minutes * 60

    processes: list[multiprocessing.Process] = []

    def shutdown(*args):
        for p in processes:
            if p.is_alive():
                p.terminate()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)
    except (ValueError, OSError):
        pass

    for cam in config["cameras"]:
        base_dir = recordings_dir / cam["name"]
        rtsp_url = build_rtsp_url_with_auth(
            cam["rtsp_url"],
            username=cam.get("username"),
            password=cam.get("password"),
        )
        p = multiprocessing.Process(
            target=run_camera_process,
            args=(cam["name"], rtsp_url, str(base_dir), segment_seconds),
            name=f"recorder-{cam['name']}",
        )
        p.start()
        processes.append(p)
        print(f"[INFO] Started process for {cam['name']} (PID {p.pid})")

    for p in processes:
        p.join()

    print("[INFO] All recorder processes finished.")


if __name__ == "__main__":
    # Required for Windows multiprocessing support
    multiprocessing.freeze_support()
    main()
