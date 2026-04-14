from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from ..config import Settings


class ObjectStorageClientProtocol(Protocol):
    def upload_file(
        self,
        *,
        local_path: Path,
        bucket: str,
        key: str,
        metadata: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> None: ...

    def download_file(self, *, bucket: str, key: str, local_path: Path) -> None: ...


class S3CompatibleObjectStorageClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def upload_file(
        self,
        *,
        local_path: Path,
        bucket: str,
        key: str,
        metadata: dict[str, str] | None = None,
        content_type: str | None = None,
    ) -> None:
        extra_args: dict[str, object] = {}
        if metadata:
            extra_args["Metadata"] = metadata
        if content_type:
            extra_args["ContentType"] = content_type
        self._client.upload_file(str(local_path), bucket, key, ExtraArgs=extra_args or None)

    def download_file(self, *, bucket: str, key: str, local_path: Path) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(bucket, key, str(local_path))


def build_object_storage_client(
    settings: Settings,
    *,
    client_factory: Any | None = None,
) -> S3CompatibleObjectStorageClient:
    factory = client_factory
    if factory is None:
        import boto3

        factory = boto3.client

    kwargs: dict[str, object] = {}
    if settings.object_storage_endpoint_url:
        kwargs["endpoint_url"] = settings.object_storage_endpoint_url
    if settings.object_storage_region:
        kwargs["region_name"] = settings.object_storage_region
    if settings.object_storage_access_key_id:
        kwargs["aws_access_key_id"] = settings.object_storage_access_key_id
    if settings.object_storage_secret_access_key:
        kwargs["aws_secret_access_key"] = settings.object_storage_secret_access_key
    if settings.object_storage_session_token:
        kwargs["aws_session_token"] = settings.object_storage_session_token
    if settings.object_storage_force_path_style:
        from botocore.config import Config

        kwargs["config"] = Config(s3={"addressing_style": "path"})

    client = factory("s3", **kwargs)
    return S3CompatibleObjectStorageClient(client)
