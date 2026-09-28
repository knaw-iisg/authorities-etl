"""Runs every static/authority/sourceData fixture through the full pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import XSD, Namespace

from authorities_etl.fixtures import load_fixture
from authorities_etl.pipeline import process_record

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "static" / "authority" / "sourceData"
SDO = Namespace("https://schema.org/")


def _fixture_paths():
    return sorted(FIXTURES_DIR.glob("*.json"))


@pytest.mark.parametrize("path", _fixture_paths(), ids=lambda p: p.stem)
def test_record_processes_without_error(path: Path):
    record = load_fixture(path)
    g = Graph()
    item = process_record(record, g)
    assert item is not None
    assert len(g) > 0


def test_place_heading_gets_type_specific_iri_and_place_type():
    """Regression check for the bug this port deliberately does not carry
    over: a 151 (geographic name) record must mint under place:, typed
    sdo:Place -- not a generic 'NotDeterminedYet' fallback."""
    record = load_fixture(FIXTURES_DIR / "229111.json")
    g = Graph()
    item = process_record(record, g)

    assert item == URIRef("https://iisg.amsterdam/authority/place/229111")
    assert (item, None, SDO.Place) in g
    assert (item, SDO.name, None) in g


def test_topic_with_alternate_names_and_dlc_sameas():
    record = load_fixture(FIXTURES_DIR / "980.json")
    g = Graph()
    item = process_record(record, g)

    assert item == URIRef("https://iisg.amsterdam/authority/topic/980")
    names = {str(o) for o in g.objects(item, SDO.name)}
    assert names == {"Petroleum industry"}
    alt_names = {str(o) for o in g.objects(item, SDO.alternateName)}
    assert alt_names == {"Petro-chemical industry", "Chemical industry"}
    same_as = list(g.objects(item, SDO.sameAs))
    assert same_as == [URIRef("http://id.loc.gov/authorities/subjects/85100430")]


def test_person_with_viaf_sameas():
    record = load_fixture(FIXTURES_DIR / "612.json")
    g = Graph()
    item = process_record(record, g)

    assert (item, SDO.sameAs, URIRef("http://viaf.org/viaf/292528802")) in g


def test_meeting_name_joins_subfields():
    record = load_fixture(FIXTURES_DIR / "169.json")
    g = Graph()
    item = process_record(record, g)

    names = {str(o) for o in g.objects(item, SDO.name)}
    assert len(names) == 1
    name = next(iter(names))
    assert "1 mei" in name and "1982" in name


def test_nde_ap_dataset_link_and_typed_sd_date_published():
    record = load_fixture(FIXTURES_DIR / "612.json")
    g = Graph()
    item = process_record(record, g)

    assert (item, SDO.isPartOf, URIRef("https://iisg.amsterdam/id/dataset/authorities")) in g
    dates = list(g.objects(item, SDO.sdDatePublished))
    assert dates
    assert dates[0].datatype == XSD.dateTime
