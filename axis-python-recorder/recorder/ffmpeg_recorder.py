import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

from recorder.utils import get_ffmpeg_path

# Default segment duration in seconds (15 minutes)
SEGMENT_SECONDS = 15 * 60


class FFmpegRecorder:
    def __init__(self, camera_name: str, rtsp_url: str, base_dir: Path):
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.base_dir = base_dir
        self._stop_requested = False
        # Resolve FFmpeg path once at initialization
        self._ffmpeg_path = get_ffmpeg_path()

    def _request_stop(self, *args):
        self._stop_requested = True

    def _record_one_segment(self, output_file: Path, duration_seconds: int) -> subprocess.Popen | None:
        """Record a single segment of given duration. Returns the FFmpeg process."""
        cmd = [
            self._ffmpeg_path,
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-c", "copy",
            "-f", "mp4",
            "-t", str(duration_seconds),
            "-y",
            str(output_file)
        ]
        try:
            # Don't capture stdout/stderr so FFmpeg errors are visible in the console
            return subprocess.Popen(cmd)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"FFmpeg not found. Please install FFmpeg and add it to your PATH.\n"
                f"Download from: https://ffmpeg.org/download.html\n"
                f"Original error: {e}"
            )

    def record(self):
        """Record a single segment (legacy one-shot behavior)."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = self.base_dir / f"{self.camera_name}_{timestamp}.mp4"
        cmd = [
            self._ffmpeg_path,
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-c", "copy",
            "-f", "mp4",
            str(output_file)
        ]
        print(f"[INFO] Recording {self.camera_name}")
        print(f"[INFO] Output file: {output_file}")
        subprocess.run(cmd)

    def record_loop(self, segment_seconds: int = SEGMENT_SECONDS):
        """
        Record continuously with automatic file rotation every segment_seconds.
        Runs until interrupted (e.g. Ctrl+C).
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._stop_requested = False

        # Allow graceful stop on SIGINT/SIGTERM
        try:
            signal.signal(signal.SIGINT, self._request_stop)
            signal.signal(signal.SIGTERM, self._request_stop)
        except (ValueError, OSError):
            # Signals may not be available in all contexts (e.g. some threads)
            pass

        print(f"[INFO] {self.camera_name}: starting record loop (segment = {segment_seconds}s)")

        while not self._stop_requested:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = self.base_dir / f"{self.camera_name}_{timestamp}.mp4"
            print(f"[INFO] {self.camera_name}: recording -> {output_file.name}")

            proc = self._record_one_segment(output_file, segment_seconds)
            if proc is None:
                break

            try:
                proc.wait()
            except KeyboardInterrupt:
                self._stop_requested = True
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                break

            if proc.returncode != 0:
                # 255 = FFmpeg exited on SIGINT (Ctrl+C), 143 = SIGTERM — not real failures
                if proc.returncode in (255, 143) and output_file.exists() and output_file.stat().st_size > 0:
                    print(f"[INFO] {self.camera_name}: segment saved (recording stopped by user).")
                elif proc.returncode not in (255, 143):
                    print(f"[ERROR] {self.camera_name}: segment failed (exit code {proc.returncode}). No file written.")
                    print(f"[ERROR] Check RTSP URL, camera power/network, and any FFmpeg messages above.")
                    if not self._stop_requested:
                        time.sleep(5)

        print(f"[INFO] {self.camera_name}: record loop stopped")
