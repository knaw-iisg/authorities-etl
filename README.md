# authorities-etl

Maps IISG's MARC authority records (persons, organizations, events, places,
topics, periods, forms, uniform titles) to RDF. Investigated via
[rlzijdeman/auth2sdo-py](https://github.com/rlzijdeman/auth2sdo-py) (a prior
faithful port of an existing XSLT, plus a full 615K-record harvest
characterizing the data), but built fresh here with no code or structural
dependency on that XSLT or its port -- see the field-mapping table below for
where this deliberately differs.

**Why this repo matters for the other three:** biblio-etl, archive-etl and
findingaid-etl all mint locally-scoped authority IRIs
(`https://iisg.amsterdam/authority/person/<id>`, `.../organization/<id>`,
`.../place/<id>`, `.../topic/<id>`, `.../period/<id>`, `.../form/<id>`,
`.../title/<id>`, `.../event/<id>`) with no name or `sameAs` of their own --
this pipeline mints IRIs under those *exact same* namespaces from the
authority records those ids actually refer to. Merge the graphs and those
previously-bare IRIs get real names, alternate names, and VIAF/LoC links.

## Public instance

This pipeline's output is merged with six others into a single public
knowledge graph, browsable at **https://kb.zijdeman.nl** and queryable
directly at **https://sparql.zijdeman.nl** (or via QLever's own query UI
at **https://kg.zijdeman.nl**) -- see
[iisg-kb-viewer](https://github.com/knaw-iisg/iisg-kb-viewer) and
[triplestore](https://github.com/knaw-iisg/triplestore).

## Field mapping

| MARC tag(s) | RDF |
|---|---|
| `001` | forms the record's URI, together with the heading type below |
| `035 $a` | `sdo:sameAs` to VIAF or `id.loc.gov`, when the source is `VIAF`/`DLC` |
| `100` | `sdo:Person`, minted under `person:` |
| `110` | `sdo:Organization`, minted under `organization:` |
| `111 $a $d $c` | `sdo:Event`, minted under `event:` (subfields joined) |
| `130` | `sdo:CreativeWorkSeries`, minted under `title:` |
| `148` | `sdo:DefinedTerm`, minted under `period:` |
| `150` | `sdo:DefinedTerm`, minted under `topic:` |
| `151` | `sdo:Place`, minted under `place:` |
| `155` | `sdo:DefinedTerm`, minted under `form:` |
| `4XX`/`5XX` family (400/410/411/430/448/450/451/455, 500/510/511/530/548/550/551/555) | `sdo:alternateName` |
| `040`, `901`, others | not mapped |

**Deliberate differences from the XSLT this was investigated via** (see
`heading.py`/`sameas.py` docstrings for the full reasoning):
- **Every heading tag mints under its own type-specific namespace.** The
  original only special-cases 100/110/111 for URI-typing; every other
  heading (148/150/151/155, and 130 -- which the original doesn't map at
  all) falls back to a generic `.../NotDeterminedYet/<id>` IRI, confirmed
  against a live 151 (place) record. Using the same `topic:`/`period:`/
  `place:`/`form:`/`title:` namespaces biblio-etl already mints IRIs under
  is the whole point of this repo -- see above.
- **035 DLC `sameAs` doesn't auto-prepend `sh`.** The original always adds
  a literal `sh` to the id after `)`, which double-prefixes a value that
  already has one. This version uses the id verbatim. Spot-checked against
  one real record (see `sameas.py`) where the un-prefixed form resolves and
  the auto-prefixed form doesn't -- not proof this is always right, flagged
  as worth re-checking if a future `sameAs` doesn't resolve.

`sdo:name` is not language-tagged: authority headings carry no reliable
per-record language indicator.

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"
```

## Run

```bash
# All sample records under static/authority/sourceData/:
python -m authorities_etl.cli --source fixtures --out authorities.ttl

# Live OAI-PMH (set=iish.evergreen.authority), one record by control number:
python -m authorities_etl.cli --source oai --record-id 980
```

## Test

```bash
.venv/bin/pytest
```
