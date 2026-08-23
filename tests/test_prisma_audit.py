"""Tests for role-based PRISMA audit filename resolution (replaces hardcoded HLH filenames)."""

from __future__ import annotations

from litreview.pipeline.prisma_audit import (
    LEGACY_ROLE_FILES,
    audit_manuscript,
    generate_repair_prompts,
)


def _write(tmp_path, name: str, text: str):
    (tmp_path / name).write_text(text, encoding="utf-8")


def test_audit_legacy_default_finds_hlh_filenames(tmp_path):
    sections = tmp_path / "sections"
    sections.mkdir()
    _write(sections, "00-abstract.qmd", "Background: HLH. Methods: search. Results: findings. Conclusions: done.")
    _write(sections, "01-introduction.qmd", "This review addresses a significant gap. Objective: to review HLH.")
    _write(sections, "02-methods.qmd", "We searched Scopus, PubMed, and Embase using a search strategy.")
    _write(sections, "08-discussion.qmd", "Interpretation of findings in context. Limitations include bias.")

    results = audit_manuscript(sections)  # no role_files -> LEGACY_ROLE_FILES
    by_number = {r.number: r for r in results}
    assert by_number["2"].status == "pass"  # abstract keywords present
    assert by_number["6"].status == "pass"  # methods: scopus/pubmed/embase present


def test_audit_missing_files_reports_evidence_with_real_filenames_not_role_names(tmp_path):
    sections = tmp_path / "sections"
    sections.mkdir()
    results = audit_manuscript(sections)  # nothing written -> everything fails
    item2 = next(r for r in results if r.number == "2")
    assert item2.status == "fail"
    assert "00-abstract.qmd" in item2.evidence  # resolved filename, not the role "abstract"
    assert "role:" not in item2.evidence or "abstract" not in item2.evidence.split("role:")[0]


def test_audit_dynamic_role_files_finds_topic_specific_filenames(tmp_path):
    sections = tmp_path / "sections"
    sections.mkdir()
    _write(sections, "01-introduction.qmd", "This review addresses a significant gap. Objective: to review MASLD.")
    _write(sections, "02-methods.qmd", "We searched PubMed using a search strategy and database.")
    _write(sections, "03-pharmacotherapy.qmd", "Semaglutide reduced fibrosis [@Smith2026Semaglutide], p < 0.001, 45% response.")
    _write(sections, "04-discussion.qmd", "Interpretation of findings in context. Limitations include search scope.")

    role_files = {
        "main": ["main.qmd"],
        "abstract": ["00-abstract.qmd"],
        "introduction": ["01-introduction.qmd"],
        "methods": ["02-methods.qmd"],
        "body": ["03-pharmacotherapy.qmd"],
        "discussion": ["04-discussion.qmd"],
        "checklist": ["checklist.qmd"],
    }
    results = audit_manuscript(sections, role_files=role_files)
    by_number = {r.number: r for r in results}

    assert by_number["4"].status in ("pass", "partial")  # objectives keyword found via "introduction" role, not "fail"
    assert by_number["6"].status == "pass"  # information sources, found via "methods" role
    assert by_number["17"].status == "pass"  # citations, found via "body" role -> 03-pharmacotherapy.qmd
    assert by_number["19"].status in ("pass", "partial")  # quantitative results found via "body" role, not "fail"
    assert by_number["23a"].status in ("pass", "partial")  # interpretation found via "discussion" role, not "fail"


def test_audit_dynamic_role_files_does_not_fall_back_to_legacy_hlh_filenames(tmp_path):
    # A pharmacotherapy section under a NON-legacy filename must not be silently
    # ignored just because it doesn't match the hardcoded HLH names.
    sections = tmp_path / "sections"
    sections.mkdir()
    _write(sections, "03-pharmacotherapy.qmd", "Semaglutide reduced fibrosis [@Smith2026Semaglutide].")

    # Using LEGACY_ROLE_FILES (default) should find nothing for "body" role,
    # since 03-pharmacotherapy.qmd isn't one of the legacy body filenames —
    # this demonstrates exactly the bug that made role_files necessary.
    legacy_results = audit_manuscript(sections)
    assert next(r for r in legacy_results if r.number == "17").status == "fail"

    dynamic_results = audit_manuscript(
        sections, role_files={**LEGACY_ROLE_FILES, "body": ["03-pharmacotherapy.qmd"]}
    )
    assert next(r for r in dynamic_results if r.number == "17").status == "pass"


def test_generate_repair_prompts_uses_resolved_filenames_as_keys(tmp_path):
    sections = tmp_path / "sections"
    sections.mkdir()
    results = audit_manuscript(sections)  # everything fails -> plenty of repairs
    role_files = {**LEGACY_ROLE_FILES, "body": ["05-custom-body.qmd"]}
    repairs = generate_repair_prompts(results, role_files=role_files)
    # Item 17 (Study characteristics) requires the "body" role -> should key by
    # the actual resolved filename, not the literal word "body"
    assert "05-custom-body.qmd" in repairs
    assert "body" not in repairs
