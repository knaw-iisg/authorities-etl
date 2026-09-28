"""Unit tests using small hand-built MARC-JSON records (independent of the
OAI fixtures)."""

from __future__ import annotations

from rdflib import Graph, URIRef
from rdflib.namespace import Namespace

from authorities_etl.pipeline import process_record

SDO = Namespace("https://schema.org/")


def _record(control_number: str, datafields: list[dict], datestamp: str = "2020-01-01T00:00:00Z") -> dict:
    return {
        "header": {
            "identifier": f"oai:socialhistoryservices.org:iish.evergreen.authority:{control_number}",
            "datestamp": datestamp,
        },
        "metadata": {
            "marc:record": {
                "marc:controlfield": [{"@tag": "001", "$text": control_number}],
                "marc:datafield": datafields,
            }
        },
    }


def test_record_with_no_heading_is_skipped():
    record = _record("1", [{"@tag": "040", "marc:subfield": {"@code": "a", "$text": "IISG"}}])
    g = Graph()
    item = process_record(record, g)
    assert item is None
    assert len(g) == 0


def test_period_heading_maps_to_period_namespace_defined_term():
    record = _record("2", [{"@tag": "148", "marc:subfield": {"@code": "a", "$text": "20th century"}}])
    g = Graph()
    item = process_record(record, g)
    assert item == URIRef("https://iisg.amsterdam/authority/period/2")
    assert (item, None, SDO.DefinedTerm) in g
    assert (item, SDO.name, None) in g


def test_organization_heading_with_viaf_and_alternate_name():
    record = _record("3", [
        {"@tag": "110", "marc:subfield": {"@code": "a", "$text": "Test Org"}},
        {"@tag": "035", "marc:subfield": {"@code": "a", "$text": "(VIAF)123456"}},
        {"@tag": "410", "marc:subfield": {"@code": "a", "$text": "Alt Org Name"}},
    ])
    g = Graph()
    item = process_record(record, g)
    assert item == URIRef("https://iisg.amsterdam/authority/organization/3")
    assert (item, None, SDO.Organization) in g
    assert (item, SDO.sameAs, URIRef("http://viaf.org/viaf/123456")) in g
    assert (item, SDO.alternateName, None) in g


def test_035_with_trailing_garbage_recovers_clean_id_instead_of_crashing():
    """Regression test: real record 2033927 has $a = '(VIAF)47048537 (' (a
    truncated source value with a trailing space and stray unmatched '(').
    This crashed a ~9-hour full harvest by minting an unserializable IRI --
    rdflib's N-Triples writer raises on an invalid URI rather than skipping
    it. Must recover the clean id, not raise and not silently mint garbage."""
    record = _record("2033927", [
        {"@tag": "100", "marc:subfield": {"@code": "a", "$text": "Test Person"}},
        {"@tag": "035", "marc:subfield": {"@code": "a", "$text": "(VIAF)47048537 ("}},
    ])
    g = Graph()
    item = process_record(record, g)
    assert (item, SDO.sameAs, URIRef("http://viaf.org/viaf/47048537")) in g
    # must actually be serializable -- the original failure was at serialize time
    g.serialize(format="nt")
