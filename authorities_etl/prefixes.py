"""Namespace/prefix declarations.

The authority/person/organization/event/place/topic/period/form/title
namespaces are the **exact same ones biblio-etl already mints** IRIs under
(e.g. `person:176035` from a MARC 100 $0 `(NL-AMISG)176035` reference in a
biblio record). That's the whole point of this pipeline: biblio-etl,
archive-etl and findingaid-etl all mint locally-scoped authority IRIs with
no name or sameAs of their own -- this pipeline is what actually populates
those same IRIs with real data, closing that gap when the graphs are merged.
"""

from rdflib import Namespace

BASE = "https://iisg.amsterdam/"
AUTHORITY = BASE + "authority/"
ID = BASE + "id/"

PERSON = Namespace(AUTHORITY + "person/")
ORGANIZATION = Namespace(AUTHORITY + "organization/")
EVENT = Namespace(AUTHORITY + "event/")
PLACE = Namespace(AUTHORITY + "place/")
TOPIC = Namespace(AUTHORITY + "topic/")
PERIOD = Namespace(AUTHORITY + "period/")
FORM = Namespace(AUTHORITY + "form/")
TITLE = Namespace(AUTHORITY + "title/")

DATASET = Namespace(ID + "dataset/")

SDO = Namespace("https://schema.org/")
VIAF = Namespace("http://viaf.org/viaf/")
LOC_AUTHORITIES = Namespace("http://id.loc.gov/authorities/subjects/")

DEFAULT_GRAPH = "https://iisg.amsterdam/graph/authority"

NAMESPACE_BINDINGS = {
    "person": PERSON,
    "organization": ORGANIZATION,
    "event": EVENT,
    "place": PLACE,
    "topic": TOPIC,
    "period": PERIOD,
    "form": FORM,
    "title": TITLE,
    "dataset": DATASET,
    "sdo": SDO,
    "viaf": VIAF,
    "loc": LOC_AUTHORITIES,
}
