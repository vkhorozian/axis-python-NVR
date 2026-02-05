# Axis Python Recorder

A lightweight Python-based camera recorder designed for Axis IP cameras using RTSP.
The project relies on FFmpeg for efficient, low-CPU stream recording.

## Features
- Records RTSP streams directly to MP4
- No re-encoding (stream copy)
- Configurable camera list
- Windows 11 friendly
- Designed to scale to multiple cameras
- **One process per camera** for parallel recording
- **Automatic file rotation** every 15 minutes

## Requirements
- Python 3.10+
- FFmpeg (must be in system PATH)

## Setup
1. Install Python
2. Install FFmpeg and add it to PATH
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example config and add your cameras:
   - **Windows:** `copy config\cameras.json.example config\cameras.json`
   - **Linux/Mac:** `cp config/cameras.json.example config/cameras.json`
   Then edit `config/cameras.json` with your camera URLs and credentials.
5. Run:

   ```bash
   python main.py
   ```

## Reducing network usage (less data)

Data over the network is determined by **which stream** you use and **how the camera is configured**. The recorder does not control bitrate; it just records what the camera sends.

**Best options (in order):**

1. **Use the camera’s substream**  
   Many Axis cameras expose a second RTSP URL for a lower-resolution, lower-bitrate stream (e.g. “Substream” or “Stream profile 2”). In the camera’s web UI, open **Video** or **Stream profiles**, find the substream, and copy its RTSP path or URL. Put that URL in `config/cameras.json` instead of the main stream. Same protocol (RTSP), much less data.

2. **Lower the stream in the camera**  
   In the camera’s web UI (e.g. **Video → Stream**), for the profile you use for recording: reduce **Resolution** (e.g. 720p or lower), **Frame rate** (e.g. 5–10 fps), and **Bitrate** (e.g. 512–1024 kbps). Then use that stream’s URL in `cameras.json`.

3. **Keep main stream only when needed**  
   If you only need the high-quality stream for live viewing sometimes, use the substream URL in this recorder and leave the main stream for other uses. No code changes—only the URL in config.

Transcoding (re-encoding) in the app can reduce **storage** but not **network**: the camera still sends the same stream. To use less data on the network, the camera must send a lighter stream (substream or lower settings).

## Notes

* This project intentionally uses FFmpeg directly instead of OpenCV for reliability.
* Designed as a foundation for a future NVR-style application.
