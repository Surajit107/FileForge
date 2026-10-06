"""LibreOffice headless conversion helper.

Office → PDF pairs (docx / xlsx / csv / pptx) require LibreOffice. The Docker
image installs Writer, Calc, and Impress for server deploys; local Windows is
expected to fail these pairs unless LibreOffice is installed separately.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from engines.exceptions import ConversionFailedError

_WINDOWS_CANDIDATES = (
    Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
)

_UNIX_CANDIDATES = (
    Path("/usr/bin/soffice"),
    Path("/usr/bin/libreoffice"),
    Path("/usr/lib/libreoffice/program/soffice"),
    Path("/opt/libreoffice/program/soffice"),
)


def find_libreoffice() -> str | None:
    """Return an executable path for LibreOffice, or None if missing."""
    for candidate in ("soffice", "libreoffice", "soffice.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    extra = os.environ.get("LIBREOFFICE_PATH", "").strip()
    if extra:
        path = Path(extra)
        if path.is_file():
            return str(path)

    search = _WINDOWS_CANDIDATES if os.name == "nt" else _UNIX_CANDIDATES
    for path in search:
        if path.is_file():
            return str(path)
    return None


def convert_with_libreoffice(source_path: Path, destination_path: Path) -> Path:
    binary = find_libreoffice()
    if binary is None:
        raise ConversionFailedError(
            "LibreOffice is required for this conversion but was not found. "
            "Install LibreOffice and ensure `soffice` is on PATH, or set "
            "LIBREOFFICE_PATH to the soffice binary."
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fileforge-lo-") as tmp:
        root = Path(tmp)
        out_dir = root / "out"
        profile_dir = root / "profile"
        out_dir.mkdir()
        profile_dir.mkdir()
        # Isolated profile avoids lock/home-permission failures in Docker.
        profile_uri = profile_dir.resolve().as_uri()

        try:
            completed = subprocess.run(
                [
                    binary,
                    "--headless",
                    "--nologo",
                    "--nolockcheck",
                    "--nodefault",
                    "--nofirststartwizard",
                    f"-env:UserInstallation={profile_uri}",
                    "--convert-to",
                    destination_path.suffix.lstrip("."),
                    "--outdir",
                    str(out_dir),
                    str(source_path.resolve()),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
                env={
                    **os.environ,
                    "HOME": str(root),
                    "SAL_USE_VCLPLUGIN": "svp",
                },
            )
        except subprocess.TimeoutExpired as exc:
            raise ConversionFailedError("LibreOffice conversion timed out.") from exc
        except OSError as exc:
            raise ConversionFailedError(f"LibreOffice failed to start: {exc}") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise ConversionFailedError(
                f"LibreOffice conversion failed (exit {completed.returncode})"
                + (f": {detail}" if detail else ".")
            )

        produced = out_dir / f"{source_path.stem}{destination_path.suffix}"
        if not produced.exists():
            matches = list(out_dir.glob(f"*{destination_path.suffix}"))
            if not matches:
                raise ConversionFailedError("LibreOffice produced no output file.")
            produced = matches[0]

        destination_path.write_bytes(produced.read_bytes())
    return destination_path
