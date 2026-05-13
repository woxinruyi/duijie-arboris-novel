"""Utilities for content normalization and hashing."""
from __future__ import annotations

import hashlib
from typing import Optional


def normalize_content(text: Optional[str]) -> str:
    """Normalize text for hashing: normalize newlines, drop BOM, trim trailing whitespace."""
    if text is None:
        return ""
    # Remove BOM if present
    cleaned = text.replace("\ufeff", "")
    # Normalize CRLF to LF
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    # Trim trailing whitespace at the end
    return cleaned.rstrip()


def compute_content_hash(text: Optional[str]) -> str:
    """Compute a stable sha256 hash for normalized text."""
    normalized = normalize_content(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
