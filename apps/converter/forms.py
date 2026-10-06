"""Upload + target format form."""

from __future__ import annotations

from pathlib import Path

from django import forms
from django.conf import settings

from engines.registry import (
    ALLOWED_SOURCE_EXTENSIONS,
    accept_attribute,
    detect_format_from_filename,
    list_sources,
    supported_upload_message,
    targets_for,
)


def _extension_allowed(filename: str) -> bool:
    name = Path(filename).name.lower()
    if name.endswith(".tar.gz"):
        return "gz" in ALLOWED_SOURCE_EXTENSIONS or "tgz" in ALLOWED_SOURCE_EXTENSIONS
    suffix = Path(name).suffix.lstrip(".")
    return bool(suffix) and suffix in ALLOWED_SOURCE_EXTENSIONS


class MultipleFileInput(forms.ClearableFileInput):
    """Django 5 requires an explicit allow_multiple_selected flag."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Bind every uploaded file, not only the first."""

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return single_file_clean(data, initial)


class ConversionForm(forms.Form):
    source_file = MultipleFileField(
        label="Source file",
        widget=MultipleFileInput(
            attrs={
                "accept": accept_attribute(),
                "class": "absolute inset-0 z-20 h-full w-full cursor-pointer opacity-0",
                "aria-describedby": "file-name",
            }
        ),
    )
    target_format = forms.ChoiceField(
        label="Convert to",
        choices=(),
        widget=forms.Select(
            attrs={
                "class": "format-picker__native",
                "tabindex": "-1",
                "aria-hidden": "true",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default choices for empty GET: Markdown targets (most common entry).
        default_source = (
            "md" if "md" in list_sources() else (list_sources()[0] if list_sources() else "md")
        )
        source_hint = None
        files = self.files.getlist("source_file") if self.is_bound else []
        if files:
            source_hint = detect_format_from_filename(files[0].name)
        pairs = targets_for(source_hint or default_source)
        self.fields["target_format"].choices = [
            (pair.target, f"{pair.label}{' (best effort)' if pair.best_effort else ''}")
            for pair in pairs
        ]

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        files = uploaded if isinstance(uploaded, list) else [uploaded]
        if not files:
            raise forms.ValidationError("Choose at least one file to convert.")

        max_files = settings.CONVERSION_MAX_BATCH_FILES
        if len(files) > max_files:
            raise forms.ValidationError(
                f"Too many files. Maximum batch size is {max_files}."
            )

        max_bytes = settings.CONVERSION_MAX_UPLOAD_BYTES
        max_batch_bytes = settings.CONVERSION_MAX_BATCH_BYTES
        total_bytes = 0
        detected_sources: list[str] = []
        errors: list[str] = []

        for item in files:
            total_bytes += item.size
            if item.size > max_bytes:
                max_mb = max_bytes // (1024 * 1024)
                errors.append(f"{item.name} exceeds the {max_mb} MB upload limit.")
                continue
            if not _extension_allowed(item.name or ""):
                errors.append(f"{item.name}: {supported_upload_message()}")
                continue
            source = detect_format_from_filename(item.name)
            if source is None:
                errors.append(f"{item.name}: {supported_upload_message()}")
                continue
            detected_sources.append(source)

        if total_bytes > max_batch_bytes:
            max_mb = max_batch_bytes // (1024 * 1024)
            errors.append(f"Batch exceeds the {max_mb} MB total upload limit.")

        if errors:
            raise forms.ValidationError(errors)

        self.cleaned_data["detected_sources"] = detected_sources
        return files

    def clean(self):
        cleaned = super().clean()
        files = cleaned.get("source_file") or []
        if not isinstance(files, list):
            files = [files] if files else []

        detected_sources = cleaned.get("detected_sources") or []
        target = cleaned.get("target_format")
        if target and detected_sources:
            for source in detected_sources:
                allowed = {pair.target for pair in targets_for(source)}
                if target not in allowed:
                    self.add_error(
                        "target_format",
                        f"Cannot convert {source} to {target}.",
                    )
                    break

        cleaned["source_files"] = files
        cleaned["detected_source_format"] = detected_sources[0] if detected_sources else None
        return cleaned
