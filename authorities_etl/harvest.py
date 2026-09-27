"""OAI-PMH harvesting of IISG's MARC authority records, producing the same
nested-dict JSON shape used by ``static/authority/sourceData/*.json``
fixtures (so this module and those fixtures are interchangeable inputs to
``pipeline.process_record``)."""

from __future__ import annotations

from collections.abc import Iterator

import requests
import xmltodict

ENDPOINT = "https://api.socialhistoryservices.org/solr/all/oai"
METADATA_PREFIX = "marcxml"
DEFAULT_SET = "iish.evergreen.authority"

_NAMESPACES = {
    "http://www.openarchives.org/OAI/2.0/": None,
    "http://www.loc.gov/MARC21/slim": "marc",
}


def _parse(xml_bytes: bytes) -> dict:
    return xmltodict.parse(
        xml_bytes,
        process_namespaces=True,
        namespaces=_NAMESPACES,
        attr_prefix="@",
        cdata_key="$text",
    )


def harvest_records(
    *,
    endpoint: str = ENDPOINT,
    metadata_prefix: str = METADATA_PREFIX,
    set_spec: str | None = DEFAULT_SET,
    identifier: str | None = None,
    session: requests.Session | None = None,
    timeout: float = 60,
) -> Iterator[dict]:
    http = session or requests.Session()

    if identifier is not None:
        params = {"verb": "GetRecord", "identifier": identifier, "metadataPrefix": metadata_prefix}
        resp = http.get(endpoint, params=params, timeout=timeout)
        resp.raise_for_status()
        doc = _parse(resp.content)
        record = doc.get("OAI-PMH", {}).get("GetRecord", {}).get("record")
        if record:
            yield _to_source_shape(record)
        return

    params = {"verb": "ListRecords", "metadataPrefix": metadata_prefix}
    if set_spec:
        params["set"] = set_spec

    resumption_token = None
    while True:
        request_params = {"verb": "ListRecords", "resumptionToken": resumption_token} if resumption_token else params

        resp = http.get(endpoint, params=request_params, timeout=timeout)
        resp.raise_for_status()
        doc = _parse(resp.content)
        list_records = doc.get("OAI-PMH", {}).get("ListRecords", {})
        if not list_records:
            return

        records = list_records.get("record", [])
        if isinstance(records, dict):
            records = [records]
        for record in records:
            yield _to_source_shape(record)

        token = list_records.get("resumptionToken")
        token_text = token.get("$text") if isinstance(token, dict) else token
        if not token_text:
            return
        resumption_token = token_text


def _to_source_shape(record: dict) -> dict:
    return {
        "header": record.get("header", {}),
        "metadata": record.get("metadata", {}),
    }
