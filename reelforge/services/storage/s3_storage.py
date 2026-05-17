import os
import shutil
import logging
from typing import Optional

import boto3

logger = logging.getLogger(__name__)


def _make_s3_client():
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    session_kwargs = {}
    if aws_key and aws_secret:
        session_kwargs["aws_access_key_id"] = aws_key
        session_kwargs["aws_secret_access_key"] = aws_secret

    client_kwargs = session_kwargs.copy()
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    return boto3.client("s3", **client_kwargs)


def upload_file(local_path: str, s3_key: str, bucket: Optional[str] = None) -> str:
    """Upload a local file to S3/R2 or fallback to local `artifacts/` directory.

    Returns a URL-like path string (s3://bucket/key or file://...)
    """
    bucket = bucket or os.getenv("S3_BUCKET")
    if bucket:
        try:
            s3 = _make_s3_client()
            s3.upload_file(local_path, bucket, s3_key)
            endpoint = os.getenv("S3_ENDPOINT_URL")
            if endpoint:
                # R2 or custom endpoint: return endpoint-based URL if possible
                return f"{endpoint.rstrip('/')}/{bucket}/{s3_key}"
            return f"s3://{bucket}/{s3_key}"
        except Exception:
            logger.exception("S3 upload failed, falling back to local storage")

    # Fallback to local artifacts directory
    artifacts_dir = os.path.abspath(os.getenv("LOCAL_ARTIFACTS_DIR", "artifacts"))
    os.makedirs(artifacts_dir, exist_ok=True)
    dest_path = os.path.join(artifacts_dir, os.path.basename(s3_key))
    shutil.copy2(local_path, dest_path)
    return f"file://{dest_path}"


def generate_presigned_url(s3_key: str, bucket: Optional[str] = None, expires_in: int = 3600) -> str:
    """Generate a presigned GET URL for an object in S3/R2 if credentials are configured.

    Falls back to a `file://` path when running locally without S3 configured.
    """
    bucket = bucket or os.getenv("S3_BUCKET")
    if not bucket:
        # No bucket configured; treat key as local artifact name
        artifacts_dir = os.path.abspath(os.getenv("LOCAL_ARTIFACTS_DIR", "artifacts"))
        local_path = os.path.join(artifacts_dir, os.path.basename(s3_key))
        return f"file://{local_path}"

    try:
        s3 = _make_s3_client()
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": s3_key}, ExpiresIn=expires_in
        )
        return url
    except Exception:
        logger.exception("Failed to generate presigned URL, returning s3:// path")
        return f"s3://{bucket}/{s3_key}"
