"""MARC datafield 035 ($a system control number) -> ``sdo:sameAs`` VIAF or
Library of Congress authorities, when the bracketed source is ``VIAF`` or
``DLC``.

A clean reimplementation, not a port, of the mapping this was investigated
from: that one always prepends a literal ``sh`` to the DLC id
(``.../subjects/sh{value}``), which double-prefixes any value that already
starts with ``sh``. This version uses the id after the ``)`` verbatim
instead, so it can't double-prefix.

Verified against one real record (980, `(DLC)85100430` -> a topic heading):
``id.loc.gov/authorities/subjects/85100430`` (no added prefix, what this
code produces) resolves to a real authority record; the "sh"-prepended
form resolves to something else entirely. That's one data point, not
proof the source `$a` value is always already complete -- LC's authority
numbers do use other letter prefixes for other record types (`n` for
names, etc.), which IISG's data may or may not already include. If a
future record's `sameAs` turns out not to resolve, this is the first place
to look.
"""

from __future__ import annotations

from rdflib import Graph, URIRef

from .context import as_array, get_code, get_text
from .prefixes import LOC_AUTHORITIES, SDO, VIAF


def apply_035(g: Graph, subject: URIRef, datafield: dict) -> None:
    for sub in as_array(datafield.get("marc:subfield")):
        if get_code(sub) != "a":
            continue
        text = get_text(sub)
        if not text or not text.startswith("(") or ")" not in text:
            continue
        source, _, value = text[1:].partition(")")
        value = value.strip()
        if not value:
            continue
        if source == "VIAF":
            g.add((subject, SDO.sameAs, VIAF[value]))
        elif source == "DLC":
            g.add((subject, SDO.sameAs, LOC_AUTHORITIES[value]))
