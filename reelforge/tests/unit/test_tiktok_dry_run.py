import os
import json


def test_upload_to_tiktok_dry_run(tmp_path):
    from services.social_upload.tiktok import upload_to_tiktok

    video = tmp_path / "video.mp4"
    video.write_bytes(b"\x00")

    res = upload_to_tiktok(f"file://{video}", "caption text", ["#tag1"], dry_run=True)
    assert res["status"] == "dry-run"
    assert res["platform"] == "tiktok"
    assert "meta_path" in res
    meta_path = res["meta_path"]
    assert meta_path.startswith("file://")
    path = meta_path[len("file://"):]
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    assert meta["caption"] == "caption text"
    assert meta["hashtags"] == ["#tag1"]
