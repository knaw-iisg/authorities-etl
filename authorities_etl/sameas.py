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

Only the leading whitespace-free token of the post-``)`` value is used:
confirmed against a real record (id 2033927) whose $a was the truncated
``(VIAF)47048537 (`` -- a trailing space and stray unmatched ``(``, which
crashed a ~9-hour-in full harvest by producing an unserializable IRI
(rdflib's N-Triples writer raises on an invalid URI rather than skipping
it, so this took the whole run down, not just that one record). Real VIAF/
LC ids never contain whitespace, so splitting on it and keeping only the
first token recovers the clean id here and is a no-op for well-formed
values. Anything that still isn't URI-safe after that is skipped (with a
warning) rather than raising, so one more bad record can't repeat this.
"""

from __future__ import annotations

import sys

from rdflib import Graph, URIRef

from .context import as_array, get_code, get_text
from .prefixes import LOC_AUTHORITIES, SDO, VIAF

# Same character set rdflib's own N-Triples/Turtle serializers reject a URI
# for (see rdflib.term._invalid_uri_chars) -- checked directly here, rather
# than importing that private name, so a future rdflib internals change
# can't silently stop catching this.
_INVALID_URI_CHARS = '<>" {}|\\^`'


def _add_same_as(g: Graph, subject: URIRef, ns, value: str, record_id: str | None) -> None:
    candidate = ns[value]
    if any(c in candidate for c in _INVALID_URI_CHARS):
        print(f"skipping malformed sameAs value {value!r} on record {record_id!r}: {candidate!r}", file=sys.stderr)
        return
    g.add((subject, SDO.sameAs, candidate))


def apply_035(g: Graph, subject: URIRef, datafield: dict, record_id: str | None = None) -> None:
    for sub in as_array(datafield.get("marc:subfield")):
        if get_code(sub) != "a":
            continue
        text = get_text(sub)
        if not text or not text.startswith("(") or ")" not in text:
            continue
        source, _, value = text[1:].partition(")")
        value = value.strip().split()[0] if value.strip() else ""
        if not value:
            continue
        if source == "VIAF":
            _add_same_as(g, subject, VIAF, value, record_id)
        elif source == "DLC":
            _add_same_as(g, subject, LOC_AUTHORITIES, value, record_id)
