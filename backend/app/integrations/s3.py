from __future__ import annotations

from typing import Any, NoReturn

import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore

from app.core.config import settings


class S3Error(Exception):
    """Base class for S3-related errors."""

    pass


class S3NoSuchBucketError(S3Error):
    pass


class S3NoSuchKeyError(S3Error):
    pass


class S3AccessDeniedError(S3Error):
    pass


class S3InvalidBucketNameError(S3Error):
    pass


class S3InvalidObjectStateError(S3Error):
    pass


class S3NoSuchUploadError(S3Error):
    pass


# Map of S3 error codes to their custom exception classes
S3_ERROR_MAP: dict[str, type[S3Error]] = {
    "NoSuchBucket": S3NoSuchBucketError,
    "NoSuchKey": S3NoSuchKeyError,
    "AccessDenied": S3AccessDeniedError,
    "InvalidBucketName": S3InvalidBucketNameError,
    "InvalidObjectState": S3InvalidObjectStateError,
    "NoSuchUpload": S3NoSuchUploadError,
}


def raise_s3_error(e: ClientError) -> NoReturn:
    """Raise a custom exception based on the S3 error code, or re-raise if not mapped."""
    code = e.response["Error"]["Code"]
    exc_class = S3_ERROR_MAP.get(code)
    if exc_class:
        message = e.response["Error"].get("Message", "Unknown error")
        raise exc_class(f"{code}: {message}") from e
    raise e


class S3:
    """A wrapper around the S3 client to handle basic operations and errors."""

    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )

    def create(
        self,
        bucket_name: str,
        object_key: str,
        data: Any,
        content_type: str | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        """
        Create or upload an object to S3.

        :param bucket_name: Name of the S3 bucket.
        :param object_key: Key (path) of the object in the bucket.
        :param data: The data to upload (could be a file path str or bytes).
        :param content_type: Optional content type of the data.
        :param extra_args: Additional arguments for the S3 upload.
        """
        if extra_args is None:
            extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        try:
            if isinstance(data, str):
                # If `data` is a string, treat it as a file path on disk
                with open(data, "rb") as f:
                    self.client.upload_fileobj(
                        f, bucket_name, object_key, ExtraArgs=extra_args
                    )
            else:
                # Otherwise, assume `data` is raw bytes or a file-like object
                self.client.put_object(
                    Bucket=bucket_name, Key=object_key, Body=data, **extra_args
                )
        except ClientError as e:
            raise_s3_error(e)

    def read(self, bucket_name: str, object_key: str) -> bytes:
        """
        Read the contents of an object from S3.

        :param bucket_name: Name of the S3 bucket.
        :param object_key: Key (path) of the object in the bucket.
        :return: The object's data as bytes.
        """
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=object_key)
            return response["Body"].read()  # type: ignore
        except ClientError as e:
            raise_s3_error(e)

    def update(
        self,
        bucket_name: str,
        object_key: str,
        data: Any,
        content_type: str | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        """
        Update (overwrite) an object in S3 with new data.
        This reuses the create method internally.
        """
        self.create(bucket_name, object_key, data, content_type, extra_args)

    def delete(self, bucket_name: str, object_key: str) -> None:
        """
        Delete an object from S3.

        :param bucket_name: Name of the S3 bucket.
        :param object_key: Key (path) of the object in the bucket.
        """
        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_key)
        except ClientError as e:
            raise_s3_error(e)

    def exists(self, bucket_name: str, object_key: str) -> bool:
        """
        Check if an object exists in S3.

        :param bucket_name: Name of the S3 bucket.
        :param object_key: Key (path) of the object in the bucket.
        :return: True if the object exists, False otherwise.
        """
        try:
            self.client.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise_s3_error(e)

    def list_objects(
        self, bucket_name: str, prefix: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List objects in an S3 bucket, optionally filtered by a prefix.

        :param bucket_name: Name of the S3 bucket.
        :param prefix: Optional prefix to filter the object keys.
        :return: A list of object metadata dictionaries.
        """
        try:
            if prefix:
                response = self.client.list_objects_v2(
                    Bucket=bucket_name, Prefix=prefix
                )
            else:
                response = self.client.list_objects_v2(Bucket=bucket_name)

            if "Contents" not in response:
                return []

            return response["Contents"]  # type: ignore
        except ClientError as e:
            raise_s3_error(e)
