"""Upload + target format form."""

from __future__ import annotations

from django import forms
from django.conf import settings

from engines.registry import detect_format_from_filename, list_sources, targets_for


class ConversionForm(forms.Form):
    source_file = forms.FileField(
        label="Source file",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".md,.markdown,.docx,.pdf",
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
        default_source = "md" if "md" in list_sources() else (list_sources()[0] if list_sources() else "md")
        source_hint = None
        if self.is_bound and self.files.get("source_file"):
            source_hint = detect_format_from_filename(self.files["source_file"].name)
        pairs = targets_for(source_hint or default_source)
        self.fields["target_format"].choices = [
            (pair.target, f"{pair.label}{' (best effort)' if pair.best_effort else ''}")
            for pair in pairs
        ]

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        if uploaded.size > settings.CONVERSION_MAX_UPLOAD_BYTES:
            max_mb = settings.CONVERSION_MAX_UPLOAD_BYTES // (1024 * 1024)
            raise forms.ValidationError(f"File exceeds the {max_mb} MB upload limit.")

        source = detect_format_from_filename(uploaded.name)
        if source is None:
            raise forms.ValidationError(
                "Unsupported file type. Currently accepts Markdown (.md), DOCX, or PDF."
            )
        self.cleaned_data["detected_source_format"] = source
        return uploaded

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get("detected_source_format")
        target = cleaned.get("target_format")
        if source and target:
            allowed = {pair.target for pair in targets_for(source)}
            if target not in allowed:
                self.add_error(
                    "target_format",
                    f"Cannot convert {source} to {target}.",
                )
        return cleaned
