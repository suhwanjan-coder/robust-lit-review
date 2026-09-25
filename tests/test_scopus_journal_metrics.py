"""Scopus serial-title metrics come back NESTED; the client must read them there.

Regression: the client read top-level `citeScoreCurrentMetric` / `SJR`, which the
API does not send, so every journal got None and the CiteScore/quartile quality
gate silently filtered nothing. Shapes below were captured from the live API
(ISSN 01406736, 2026-09-25).
"""

from __future__ import annotations

import pytest

from litreview.clients.scopus import ScopusClient

REAL_SHAPE = {
    "serial-metadata-response": {
        "entry": [
            {
                "dc:title": "The Lancet",
                "citeScoreYearInfoList": {
                    "citeScoreCurrentMetric": "92.4",
                    "citeScoreCurrentMetricYear": "2025",
                },
                "SJRList": {"SJR": [
                    {"@year": "2023", "$": "12.0"},
                    {"@year": "2025", "$": "14.821"},
                ]},
                "SNIPList": {"SNIP": [{"@year": "2025", "$": "27.703"}]},
            }
        ]
    }
}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeHttp:
    def __init__(self, payload):
        self._payload = payload

    async def get(self, *_a, **_k):
        return _FakeResponse(self._payload)


def _client(payload) -> ScopusClient:
    c = ScopusClient("dummy-key")
    c._client = _FakeHttp(payload)
    return c


@pytest.mark.asyncio
async def test_metrics_read_from_nested_fields():
    m = await _client(REAL_SHAPE).get_journal_metrics("01406736")
    assert m["citescore"] == 92.4
    assert m["sjr"] == pytest.approx(14.821)  # newest year, not first item
    assert m["snip"] == pytest.approx(27.703)


@pytest.mark.asyncio
async def test_missing_metrics_stay_none_not_crash():
    payload = {"serial-metadata-response": {"entry": [{"dc:title": "Obscure J"}]}}
    m = await _client(payload).get_journal_metrics("00000000")
    assert m == {"citescore": None, "sjr": None, "snip": None}


@pytest.mark.asyncio
async def test_single_sjr_dict_instead_of_list():
    payload = {"serial-metadata-response": {"entry": [{
        "SJRList": {"SJR": {"@year": "2025", "$": "2.5"}},
    }]}}
    m = await _client(payload).get_journal_metrics("x")
    assert m["sjr"] == pytest.approx(2.5)
