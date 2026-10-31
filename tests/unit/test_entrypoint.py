import sys

import pytest


def test_unsupported_platform_exits_before_loading_posix_services(monkeypatch, capsys):
    from timemachine.entrypoint import main

    monkeypatch.setattr(sys, "platform", "win32")
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "Native Windows recovery has not been validated" in capsys.readouterr().err


def test_version_module_entrypoint():
    import subprocess

    from timemachine import __version__

    result = subprocess.run([sys.executable, "-m", "timemachine", "--version"], capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().strip() == __version__
