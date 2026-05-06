import subprocess
import shutil
from pathlib import Path


def encode_to_mp3(input_wav: str, output_mp3: str) -> None:
    from pathlib import Path

    ffmpeg_path = _find_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found. Install ffmpeg and add to PATH.")

    cmd = [
        str(ffmpeg_path),
        "-y",
        "-i", input_wav,
        "-codec:a", "libmp3lame",
        "-qscale:a", "2",
        output_mp3,
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")


def _find_ffmpeg() -> Path | None:
    for name in ["ffmpeg", "ffmpeg.exe"]:
        path = shutil.which(name)
        if path:
            return Path(path)

    common_paths = [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Users/yeahsure/AppData/Local/Microsoft/Winget/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"),
    ]

    for path in common_paths:
        if path.exists():
            return path

    return None
