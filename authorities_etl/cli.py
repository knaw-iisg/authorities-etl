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


def stream_records(
    records, out_path: Path, *, batch_size: int, checkpoint_path: Path | None, resuming: bool = False,
) -> tuple[int, int]:
    """Process records in bounded-memory batches, appending each batch's
    triples as N-Triples to ``out_path`` -- see biblio-etl's ``cli.py`` for
    why (full harvests held in one in-memory graph run into tens of GB)."""
    total_records = 0
    total_triples = 0
    batch = Graph()

    def flush(g: Graph, f) -> int:
        n = len(g)
        if n:
            f.write(g.serialize(format="nt"))
        return n

    mode = "a" if resuming else "w"
    with out_path.open(mode, encoding="utf-8") as f:
        for record in records:
            process_record(record, batch)
            total_records += 1
            if total_records % batch_size == 0:
                total_triples += flush(batch, f)
                batch = Graph()
                print(f"... {total_records} records, {total_triples} triples", file=sys.stderr)
        total_triples += flush(batch, f)

    if checkpoint_path and checkpoint_path.exists():
        checkpoint_path.unlink()

    return total_records, total_triples


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IISG authority-file ETL")
    parser.add_argument("--source", choices=["fixtures", "oai"], default="fixtures")
    parser.add_argument("--record-id", help="Only process the record whose OAI identifier ends with this id")
    parser.add_argument("--limit", type=int, help="Stop after this many records")
    parser.add_argument("--out", type=Path, help="Output file (Turtle by default, N-Triples with --stream)")
    parser.add_argument("--stream", action="store_true",
                         help="Bounded-memory mode for large harvests: write N-Triples incrementally "
                              "instead of building one in-memory graph. Requires --out.")
    parser.add_argument("--batch-size", type=int, default=500,
                         help="Records per flush in --stream mode (default: 500)")
    parser.add_argument("--resume-token", help="Resume a --source oai harvest from this OAI resumptionToken")
    args = parser.parse_args(argv)

    if args.source == "fixtures":
        records = _iter_fixture_records(args.record_id)
    else:
        checkpoint_path = args.out.with_suffix(args.out.suffix + ".checkpoint") if args.out else None

        def on_page(token: str | None) -> None:
            if checkpoint_path and token:
                checkpoint_path.write_text(token, encoding="utf-8")

        identifier = (
            f"oai:socialhistoryservices.org:iish.evergreen.authority:{args.record_id}"
            if args.record_id else None
        )
        records = harvest.harvest_records(identifier=identifier, resume_token=args.resume_token, on_page=on_page)

    if args.limit:
        records = itertools.islice(records, args.limit)

    if args.stream:
        if not args.out:
            parser.error("--stream requires --out")
        checkpoint_path = args.out.with_suffix(args.out.suffix + ".checkpoint") if args.source == "oai" else None
        total_records, total_triples = stream_records(
            records, args.out, batch_size=args.batch_size, checkpoint_path=checkpoint_path,
            resuming=bool(args.resume_token),
        )
        print(f"Wrote {total_triples} triples from {total_records} records to {args.out}", file=sys.stderr)
        return 0

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
