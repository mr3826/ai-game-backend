import os
import tempfile
import subprocess

from services.video_processing.ffmpeg_renderer import render_video


def test_render_video_no_clips_raises():
    try:
        render_video([], None, None, "out.mp4")
    except ValueError:
        return
    raise AssertionError("Expected ValueError when no clips provided")


def test_render_video_single_clip_monkeypatched(monkeypatch, tmp_path):
    # Create a fake input clip file path (contents unused because we mock ffmpeg)
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"dummy")
    out = tmp_path / "out.mp4"

    # Monkeypatch subprocess.run to simulate ffmpeg creating the output file
    def fake_run(cmd, capture_output=True, text=True):
        # Last arg is expected to be the output temp path in our implementation
        out_path = cmd[-1]
        # create a tiny placeholder file to simulate ffmpeg output
        with open(out_path, "wb") as f:
            f.write(b"\x00")

        class R:
            returncode = 0
            stderr = ""

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = render_video([str(clip)], None, None, str(out))
    assert os.path.exists(result)
    assert str(out) == result
