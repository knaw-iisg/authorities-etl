"""The record's single "1XX" main heading: determines both the entity's
type and which authority namespace its IRI is minted under.

Unlike the original XSLT this was investigated from (which only recognises
100/110/111 for URI-typing purposes -- every other heading, including place
authorities, falls back to a generic ``.../authority/NotDeterminedYet/<id>``
IRI, confirmed against a live 151 record), every heading tag here maps to
the *same* type-specific namespace biblio-etl's own field handlers already
mint IRIs under (``f148.py``->period, ``f150.py``->topic, ``f151.py``->place,
``f155.py``->form, ``f130.py``->title), so records minted here actually
populate the IRIs the other three repos already reference.
"""

from __future__ import annotations

from rdflib import Namespace, URIRef

from .context import subfield_text
from .prefixes import EVENT, FORM, ORGANIZATION, PERIOD, PERSON, PLACE, SDO, TITLE, TOPIC

# tag -> (namespace, rdf:type)
HEADING_TAGS: dict[str, tuple[Namespace, URIRef]] = {
    "100": (PERSON, SDO.Person),
    "110": (ORGANIZATION, SDO.Organization),
    "111": (EVENT, SDO.Event),
    "130": (TITLE, SDO.CreativeWorkSeries),
    "148": (PERIOD, SDO.DefinedTerm),
    "150": (TOPIC, SDO.DefinedTerm),
    "151": (PLACE, SDO.Place),
    "155": (FORM, SDO.DefinedTerm),
}


def find_heading(datafields: list[dict]) -> dict | None:
    """The record's main heading datafield (there is exactly one 1XX field
    per well-formed MARC authority record)."""
    for datafield in datafields:
        if datafield.get("@tag") in HEADING_TAGS:
            return datafield
    return None


def heading_name(datafield: dict) -> str | None:
    tag = datafield.get("@tag")
    if tag == "111":
        # Meeting name: heading ($a) + qualifying date ($d) + location ($c).
        parts = [subfield_text(datafield, code) for code in ("a", "d", "c")]
        name = " ".join(p for p in parts if p)
        return name or None
    return subfield_text(datafield, "a")
