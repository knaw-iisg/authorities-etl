"""Command-line entry point: ``python -m authorities_etl.cli``."""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

from rdflib import Graph

from . import harvest
from .fixtures import load_fixture
from .pipeline import process_record
from .prefixes import DEFAULT_GRAPH, NAMESPACE_BINDINGS

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "static" / "authority" / "sourceData"


def _iter_fixture_records(record_id: str | None):
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        record = load_fixture(path)
        identifier = record.get("header", {}).get("identifier") or ""
        if record_id and not identifier.endswith(record_id):
            continue
        yield record


def build_graph(records) -> Graph:
    g = Graph(identifier=DEFAULT_GRAPH)
    for prefix, ns in NAMESPACE_BINDINGS.items():
        g.bind(prefix, ns)
    for record in records:
        process_record(record, g)
    return g


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IISG authority-file ETL")
    parser.add_argument("--source", choices=["fixtures", "oai"], default="fixtures")
    parser.add_argument("--record-id", help="Only process the record whose OAI identifier ends with this id")
    parser.add_argument("--limit", type=int, help="Stop after this many records")
    parser.add_argument("--out", type=Path, help="Write Turtle to this file instead of stdout")
    args = parser.parse_args(argv)

    if args.source == "fixtures":
        records = _iter_fixture_records(args.record_id)
    else:
        identifier = (
            f"oai:socialhistoryservices.org:iish.evergreen.authority:{args.record_id}"
            if args.record_id else None
        )
        records = harvest.harvest_records(identifier=identifier)

    if args.limit:
        records = itertools.islice(records, args.limit)

    g = build_graph(records)

    turtle = g.serialize(format="turtle")
    if args.out:
        args.out.write_text(turtle, encoding="utf-8")
        print(f"Wrote {len(g)} triples to {args.out}", file=sys.stderr)
    else:
        print(turtle)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
