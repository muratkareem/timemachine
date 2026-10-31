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
