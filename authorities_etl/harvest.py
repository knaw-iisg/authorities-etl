"""OAI-PMH harvesting of IISG's MARC authority records, producing the same
nested-dict JSON shape used by ``static/authority/sourceData/*.json``
fixtures (so this module and those fixtures are interchangeable inputs to
``pipeline.process_record``)."""

from __future__ import annotations

import time
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

_MAX_RETRIES = 5
_RETRY_BACKOFF_SECONDS = 3


def _parse(xml_bytes: bytes) -> dict:
    return xmltodict.parse(
        xml_bytes,
        process_namespaces=True,
        namespaces=_NAMESPACES,
        attr_prefix="@",
        cdata_key="$text",
    )


def _get_with_retry(http: requests.Session, endpoint: str, params: dict, timeout: float) -> requests.Response:
    """A full harvest makes thousands of requests over tens of minutes;
    transient connection drops are expected, not exceptional (observed
    directly against this same endpoint during development)."""
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = http.get(endpoint, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise last_error


def harvest_records(
    *,
    endpoint: str = ENDPOINT,
    metadata_prefix: str = METADATA_PREFIX,
    set_spec: str | None = DEFAULT_SET,
    identifier: str | None = None,
    session: requests.Session | None = None,
    timeout: float = 60,
    resume_token: str | None = None,
    on_page: callable = None,
) -> Iterator[dict]:
    """``resume_token`` restarts a previously interrupted ``ListRecords``
    harvest from that resumption token. ``on_page(resumption_token)`` is
    called after each page if given, so a caller can persist a checkpoint.
    """
    http = session or requests.Session()

    if identifier is not None:
        params = {"verb": "GetRecord", "identifier": identifier, "metadataPrefix": metadata_prefix}
        resp = _get_with_retry(http, endpoint, params, timeout)
        doc = _parse(resp.content)
        record = doc.get("OAI-PMH", {}).get("GetRecord", {}).get("record")
        if record:
            yield _to_source_shape(record)
        return

    initial_params = {"verb": "ListRecords", "metadataPrefix": metadata_prefix}
    if set_spec:
        initial_params["set"] = set_spec

    resumption_token = resume_token
    while True:
        request_params = {"verb": "ListRecords", "resumptionToken": resumption_token} if resumption_token else initial_params

        resp = _get_with_retry(http, endpoint, request_params, timeout)
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
        if on_page is not None:
            on_page(token_text)
        if not token_text:
            return
        resumption_token = token_text


def _to_source_shape(record: dict) -> dict:
    return {
        "header": record.get("header", {}),
        "metadata": record.get("metadata", {}),
    }
