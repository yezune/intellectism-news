import subprocess
import sys


def test_python_version():
    assert sys.version_info[:2] == (3, 14)


def test_rust_version():
    out = subprocess.check_output(["rustc", "--version"], text=True)
    assert "1.98.0" in out
