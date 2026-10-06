"""LibreOffice headless conversion helper.

``docx → pdf`` quality on desktop OS usually requires LibreOffice.
If ``soffice`` / ``libreoffice`` is missing, fail loud with a clear message.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from engines.exceptions import ConversionFailedError


def find_libreoffice() -> str | None:
    for candidate in ("soffice", "libreoffice", "soffice.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def convert_with_libreoffice(source_path: Path, destination_path: Path) -> Path:
    binary = find_libreoffice()
    if binary is None:
        raise ConversionFailedError(
            "LibreOffice is required for this conversion but was not found. "
            "Install LibreOffice and ensure `soffice` is on PATH."
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fileforge-lo-") as tmp:
        out_dir = Path(tmp)
        try:
            completed = subprocess.run(
                [
                    binary,
                    "--headless",
                    "--nologo",
                    "--nolockcheck",
                    "--nodefault",
                    "--nofirststartwizard",
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
