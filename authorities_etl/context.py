"""Small shared utilities for reading MARC subfields from the OAI/MARC-JSON
record shape (same shape biblio-etl uses)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote


def as_array(value: Any) -> list:
    """MARC subfields/datafields are a single dict when there's exactly one,
    or a list when there are several -- this normalizes both to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_code(subfield: dict) -> str | None:
    return subfield.get("@code")


def get_text(subfield: dict) -> str | None:
    text = subfield.get("$text")
    if text is None:
        return None
    return str(text)


def subfield_text(datafield: dict, code: str) -> str | None:
    """First subfield with the given code, or None."""
    for sub in as_array(datafield.get("marc:subfield")):
        if get_code(sub) == code:
            return get_text(sub)
    return None


def mint_id(local_id: str) -> str:
    """Percent-encode characters that aren't valid in an IRI path segment."""
    return quote(local_id, safe="")
