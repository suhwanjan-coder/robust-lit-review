"""Tests for the silent off-VPN abstract-entitlement guard.

The failure being guarded: Elsevier's Abstract Retrieval API answers HTTP 200
with an empty dc:description when the caller is off the institution network,
instead of 401/403. Verified 2026-09-08 by A/B test (same 3 records: 0/0/0 chars
off-VPN vs 1976/1829/2057 chars on-VPN, both HTTP 200).
"""

from __future__ import annotations

from litreview.pipeline.enrichment import (
    AbstractFetchReport,
    format_abstract_fetch_warning,
)


def test_no_warning_when_scopus_returns_text():
    report = AbstractFetchReport(scopus_attempted=10, scopus_with_text=9, scopus_empty_200=1)
    assert report.scopus_likely_blocked is False
    assert format_abstract_fetch_warning(report) is None


def test_warning_when_all_scopus_responses_are_empty_200():
    report = AbstractFetchReport(scopus_attempted=12, scopus_with_text=0, scopus_empty_200=12)
    assert report.scopus_likely_blocked is True
    msg = format_abstract_fetch_warning(report)
    assert msg is not None
    assert "VPN" in msg
    assert "401/403" in msg  # explains why nothing errored


def test_small_sample_of_empties_is_not_treated_as_signal():
    # A couple of genuinely abstract-less records is normal, not an entitlement problem.
    report = AbstractFetchReport(scopus_attempted=2, scopus_with_text=0, scopus_empty_200=2)
    assert report.scopus_likely_blocked is False
    assert format_abstract_fetch_warning(report) is None


def test_no_warning_when_scopus_was_never_attempted():
    # PubMed-only run must not produce a spurious Scopus VPN warning.
    report = AbstractFetchReport(pubmed_attempted=30, pubmed_with_text=28)
    assert report.scopus_likely_blocked is False
    assert format_abstract_fetch_warning(report) is None


def test_transport_failures_alone_do_not_trigger_the_vpn_warning():
    # Attempts that never got a 200 (network/timeout) are a different problem;
    # claiming "you are off VPN" there would be a misdiagnosis.
    report = AbstractFetchReport(scopus_attempted=8, scopus_with_text=0, scopus_empty_200=0)
    assert report.scopus_likely_blocked is False
    assert format_abstract_fetch_warning(report) is None
