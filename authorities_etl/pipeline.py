"""Per-record OAI/MARC-JSON -> RDF pipeline."""

from __future__ import annotations

from rdflib import RDF, Graph, Literal, URIRef

from . import nde_ap
from .alternate_name import ALTERNATE_NAME_TAGS
from .context import as_array, get_code, get_text, mint_id
from .heading import HEADING_TAGS, find_heading, heading_name
from .prefixes import SDO
from .sameas import apply_035

_OAI_ID_PREFIX = "oai:socialhistoryservices.org:iish.evergreen.authority:"


def _control_number(marc_record: dict) -> str | None:
    for controlfield in as_array(marc_record.get("marc:controlfield")):
        if controlfield.get("@tag") == "001":
            text = controlfield.get("$text")
            return str(text) if text is not None else None
    return None


def process_record(record: dict, g: Graph) -> URIRef | None:
    """Process a single OAI-harvested MARC authority record (already
    parsed into the ``marc:record``-style JSON shape used by
    ``static/authority/sourceData/*.json``, the same shape biblio-etl uses)
    into ``g``. Returns the minted subject IRI, or ``None`` if the record
    has no usable 1XX main heading (~9% of IISG's authority set -- see
    README) or control number.
    """
    marc_record = record.get("metadata", {}).get("marc:record", {})
    datafields = as_array(marc_record.get("marc:datafield"))

    heading = find_heading(datafields)
    control_number = _control_number(marc_record)
    if heading is None or not control_number:
        return None

    namespace, rdf_type = HEADING_TAGS[heading.get("@tag")]
    subject = namespace[mint_id(control_number)]

    g.add((subject, RDF.type, rdf_type))
    name = heading_name(heading)
    if name:
        g.add((subject, SDO.name, Literal(name)))

    for datafield in datafields:
        tag = datafield.get("@tag")
        if tag == "035":
            apply_035(g, subject, datafield)
        elif tag in ALTERNATE_NAME_TAGS:
            for sub in as_array(datafield.get("marc:subfield")):
                if get_code(sub) != "a":
                    continue
                text = get_text(sub)
                if text:
                    g.add((subject, SDO.alternateName, Literal(text)))

    nde_ap.enrich(subject, record, g)

    return subject
