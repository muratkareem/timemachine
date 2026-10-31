import os

import pytest

from timemachine.errors import TimeMachineError
from timemachine.objects import ObjectStore


def put(store, path, payload):
    path.write_bytes(payload)
    fd = os.open(path, os.O_RDONLY)
    try:
        return store.put_fd(fd, 10000)
    finally:
        os.close(fd)


def test_quota_inventory_is_once_per_locked_store(project, monkeypatch, tmp_path):
    store = ObjectStore(project.store, 10000)
    original = store.usage
    calls = []

    def count():
        calls.append(1)
        return original()

    monkeypatch.setattr(store, "usage", count)
    for i in range(100):
        put(store, tmp_path / "source", str(i).encode())
    assert len(calls) == 1
    assert store.usage() == sum(len(str(i)) for i in range(100))


def test_reuse_does_not_charge_quota_twice(project, tmp_path):
    store = ObjectStore(project.store, 4)
    assert put(store, tmp_path / "source", b"data") == put(store, tmp_path / "source", b"data")
    with pytest.raises(TimeMachineError, match="quota"):
        put(store, tmp_path / "source", b"more")
    assert store.usage() == 4


def test_unchanged_content_does_not_stage_another_object(project, tmp_path, monkeypatch):
    store = ObjectStore(project.store, 100)
    put(store, tmp_path / "source", b"unchanged")

    def forbidden(*args, **kwargs):
        raise AssertionError("Duplicate capture must not stage another object")

    monkeypatch.setattr("timemachine.objects.tempfile.mkstemp", forbidden)
    put(store, tmp_path / "source", b"unchanged")


def test_object_fifo_refused_without_blocking(project):
    from timemachine.errors import IntegrityError

    store = ObjectStore(project.store, 100)
    digest = "0" * 64
    os.mkfifo(store.path(digest))
    with pytest.raises(IntegrityError, match="regular"):
        store.verify(digest)


def test_preview_read_bound(project, tmp_path):
    from timemachine.errors import IntegrityError

    store = ObjectStore(project.store, 100)
    digest, _ = put(store, tmp_path / "source", b"123456")
    with pytest.raises(IntegrityError, match="limit"):
        store.read(digest, max_bytes=2)
