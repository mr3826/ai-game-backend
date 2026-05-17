import os
from services.storage.s3_storage import upload_file, generate_presigned_url


def test_upload_file_fallback(tmp_path, monkeypatch):
    p = tmp_path / "foo.txt"
    p.write_text("hello")

    # Ensure no S3 bucket configured so adapter falls back to local artifacts
    monkeypatch.delenv("S3_BUCKET", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    url = upload_file(str(p), "uploads/foo.txt")
    assert url.startswith("file://")
    local_path = url[len("file://"):]
    assert os.path.exists(local_path)
    with open(local_path, "r") as fh:
        assert fh.read() == "hello"


def test_generate_presigned_url_fallback(monkeypatch):
    monkeypatch.delenv("S3_BUCKET", raising=False)
    url = generate_presigned_url("uploads/foo.txt")
    assert url.startswith("file://")
