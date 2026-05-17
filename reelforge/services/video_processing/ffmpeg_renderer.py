import os
import tempfile
import subprocess
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def _run(cmd: List[str]):
    logger.debug("Running ffmpeg: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("ffmpeg failed: %s", result.stderr)
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")


def render_video(clips: List[str], voice_path: Optional[str], captions_path: Optional[str], output_path: str, width: int = 1080, height: int = 1920) -> str:
    """Render a vertical short-form video from one or more clips.

    - Concats multiple clips using the concat demuxer.
    - Scales to provided width/height.
    - Optionally mixes in a voice track and overlays captions (SRT).
    """
    if not clips:
        raise ValueError("No clips provided")

    tmp_files: List[str] = []
    try:
        # If more than one clip, create a concat listfile and produce a single intermediate
        if len(clips) > 1:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as listf:
                for p in clips:
                    listf.write(f"file '{os.path.abspath(p)}'\n")
                listfile_path = listf.name
            intermediate = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            tmp_files.append(listfile_path)
            tmp_files.append(intermediate)
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                listfile_path,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                intermediate,
            ]
            _run(cmd)
            input_video = intermediate
        else:
            input_video = clips[0]

        # Prepare final encoding command
        final_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        tmp_files.append(final_tmp)
        vf_filters = [f"scale={width}:{height}"]
        if captions_path:
            vf_filters.append(f"subtitles={captions_path}")

        cmd = ["ffmpeg", "-y", "-i", input_video]

        if voice_path:
            cmd += ["-i", voice_path]

        # Video filters
        if vf_filters:
            cmd += ["-vf", ",".join(vf_filters)]

        # Audio handling: if voice provided, map it; otherwise copy any existing audio
        if voice_path:
            # map video from first input, audio from second input
            cmd += ["-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-c:a", "aac", "-shortest", final_tmp]
        else:
            cmd += ["-c:v", "libx264", "-c:a", "aac", final_tmp]

        _run(cmd)

        # Move final_tmp to output_path
        os.replace(final_tmp, output_path)
        # Remove any created intermediates from tmp_files (they will be cleaned below)
        return output_path
    finally:
        for f in tmp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                logger.exception("Failed to cleanup temp file %s", f)
