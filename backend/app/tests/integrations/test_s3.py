from __future__ import annotations

import uuid

import pytest
from botocore.exceptions import ClientError  # type: ignore

from app.integrations.s3 import (
    S3,
    S3AccessDeniedError,
    S3InvalidBucketNameError,
    S3InvalidObjectStateError,
    S3NoSuchBucketError,
    S3NoSuchKeyError,
    S3NoSuchUploadError,
    raise_s3_error,
)


@pytest.fixture(scope="session")
def s3_crud() -> S3:
    """Pytest fixture that creates (or reuses) an S3 bucket for testing and returns an S3 client."""
    s3 = S3()
    test_bucket = "test-bucket"
    try:
        s3.client.create_bucket(Bucket=test_bucket)
    except s3.client.exceptions.BucketAlreadyOwnedByYou:
        pass
    except s3.client.exceptions.BucketAlreadyExists:
        pass
    return s3


def test_no_such_bucket(s3_crud: S3) -> None:
    """Test reading from a non-existent bucket."""
    random_bucket = f"non-existent-{uuid.uuid4()}"
    with pytest.raises(S3NoSuchBucketError):
        s3_crud.read(random_bucket, "any-key")


def test_read_no_such_key(s3_crud: S3) -> None:
    """Test reading a non-existent key from an existing bucket."""
    bucket = "test-bucket"
    random_key = f"missing-{uuid.uuid4()}.txt"
    with pytest.raises(S3NoSuchKeyError):
        s3_crud.read(bucket, random_key)


def test_create_read_delete(s3_crud: S3) -> None:
    """Test creating an object, reading it back, then deleting it."""
    bucket = "test-bucket"
    key = f"test-{uuid.uuid4()}.txt"
    data = b"hello from integration test"

    s3_crud.create(bucket, key, data)
    read_data = s3_crud.read(bucket, key)
    assert read_data == data

    s3_crud.delete(bucket, key)
    with pytest.raises(S3NoSuchKeyError):
        s3_crud.read(bucket, key)


def test_update(s3_crud: S3) -> None:
    """Test updating (overwriting) an existing object with new data."""
    bucket = "test-bucket"
    key = f"update-{uuid.uuid4()}.txt"
    original = b"original data"
    updated = b"updated data"

    s3_crud.create(bucket, key, original)
    s3_crud.update(bucket, key, updated)
    read_data = s3_crud.read(bucket, key)
    assert read_data == updated

    s3_crud.delete(bucket, key)


def test_exists(s3_crud: S3) -> None:
    """Test checking existence of an object."""
    bucket = "test-bucket"
    key = f"exists-{uuid.uuid4()}.txt"
    data = b"exists data"

    s3_crud.create(bucket, key, data)
    assert s3_crud.exists(bucket, key) is True

    s3_crud.delete(bucket, key)
    assert s3_crud.exists(bucket, key) is False


def test_list_objects(s3_crud: S3) -> None:
    """Test listing objects in a bucket."""
    bucket = "test-bucket"
    key = f"list-{uuid.uuid4()}.txt"

    s3_crud.create(bucket, key, b"list content")
    objs = s3_crud.list_objects(bucket)
    assert any(o["Key"] == key for o in objs)

    s3_crud.delete(bucket, key)
    objs_after = s3_crud.list_objects(bucket)
    assert not any(o["Key"] == key for o in objs_after)


def test_raise_s3_error_unmapped() -> None:
    """Test raising an unmapped S3 error defaults to the original ClientError."""
    err = ClientError(
        {"Error": {"Code": "SomeUnknownCode", "Message": "???"}}, "MockedOperation"
    )
    with pytest.raises(ClientError):
        raise_s3_error(err)


@pytest.mark.parametrize(
    "error_code, exception_class",
    [
        ("NoSuchBucket", S3NoSuchBucketError),
        ("NoSuchKey", S3NoSuchKeyError),
        ("AccessDenied", S3AccessDeniedError),
        ("InvalidBucketName", S3InvalidBucketNameError),
        ("InvalidObjectState", S3InvalidObjectStateError),
        ("NoSuchUpload", S3NoSuchUploadError),
    ],
)
def test_raise_s3_error_mapped(
    error_code: str, exception_class: type[Exception]
) -> None:
    """Test that known error codes raise mapped custom exceptions."""
    err = ClientError(
        {"Error": {"Code": error_code, "Message": f"Mocked {error_code}"}},
        "MockedOperation",
    )
    with pytest.raises(exception_class) as exc:
        raise_s3_error(err)
    assert error_code in str(exc.value)
