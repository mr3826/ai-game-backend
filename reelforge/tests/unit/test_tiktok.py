def test_import_upload_to_tiktok():
    from services.social_upload.tiktok import upload_to_tiktok
    assert callable(upload_to_tiktok)
    res = upload_to_tiktok("dummy.mp4", "caption")
    assert isinstance(res, dict)
    assert "status" in res
