import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_check_uses_rust_normalize_and_validate():
    result = subprocess.run(
        ["make", "-n", "check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "normalize" in result.stdout
    assert "validate" in result.stdout
