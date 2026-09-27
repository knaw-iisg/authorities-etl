"""NDE Schema.org Application Profile enrichment: ``sdo:sdDatePublished``
(typed ``xsd:dateTime``) and ``sdo:isPartOf`` a dataset node, applied to
every record. Same pattern as the sibling repos' ``nde_ap.py`` modules.

``sdo:name`` is left without a language tag: MARC authority headings carry
no reliable per-record language indicator (unlike biblio's 008 or even
archive/findingaid's 041/langmaterial), so there's nothing to tag from.
"""

from __future__ import annotations

from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import XSD

from .prefixes import DATASET, SDO

DATASET_IRI = DATASET["authorities"]


def _emit_dataset_description(g: Graph) -> None:
    if (DATASET_IRI, RDF.type, SDO.Dataset) in g:
        return
    g.add((DATASET_IRI, RDF.type, SDO.Dataset))
    g.add((DATASET_IRI, SDO.name, Literal("IISG Autoriteitsbestand", lang="nl")))
    g.add((DATASET_IRI, SDO.name, Literal("IISH Authority File", lang="en")))
    g.add((DATASET_IRI, SDO.description, Literal(
        "Persoons-, organisatie-, evenement- en trefwoordauthorities van het "
        "Internationaal Instituut voor Sociale Geschiedenis (IISG).", lang="nl",
    )))
    # TODO(IISG): sdo:license, sdo:includedInDataCatalog, sdo:accessRights --
    # same open question as the sibling repos' dataset nodes.


def enrich(item: URIRef, record: dict, g: Graph, *, dataset_iri: URIRef = DATASET_IRI) -> None:
    datestamp = record.get("header", {}).get("datestamp")
    if datestamp:
        g.add((item, SDO.sdDatePublished, Literal(str(datestamp), datatype=XSD.dateTime)))

    g.add((item, SDO.isPartOf, dataset_iri))
    _emit_dataset_description(g)
