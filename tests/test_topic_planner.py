"""Tests for topic-specific taxonomy/section generation (replaces hardcoded HLH plan)."""

from __future__ import annotations

import json

from litreview.models import ArticleMetadata
from litreview.pipeline.enrichment import (
    HLH_SUBTOPIC_TAXONOMY,
    classify_article_subtopic,
    ensure_balanced_coverage,
)
from litreview.pipeline.section_dispatcher import (
    HLH_SECTIONS,
    dispatch_sections,
    generate_main_qmd,
)
from litreview.pipeline.topic_planner import (
    ReviewPlan,
    collect_taxonomy_result,
    generate_taxonomy_task,
)
from litreview.models import ReviewStatistics


def _article(title: str, abstract: str, doi: str) -> ArticleMetadata:
    return ArticleMetadata(title=title, abstract=abstract, doi=doi)


GLP1_ARTICLE = _article(
    "Semaglutide reduces hepatic fat in fatty liver disease: a randomized trial",
    "In this trial (n=320), semaglutide 2.4 mg weekly reduced liver fat content by 45% "
    "versus placebo (p<0.001) in patients with steatotic liver disease.",
    "10.1/glp1-masld",
)

HLH_ARTICLE = _article(
    "Perforin gene mutations in familial HLH",
    "PRF1 mutations were identified in 60% of familial hemophagocytic lymphohistiocytosis "
    "cases (n=45), with ferritin >10,000 ng/mL at diagnosis.",
    "10.1/hlh-genetics",
)

FAKE_PLAN_JSON = {
    "categories": [
        {"name": "epidemiology", "keywords": ["prevalence", "incidence"]},
        {"name": "pharmacotherapy", "keywords": ["semaglutide", "glp-1", "agonist"]},
        {"name": "prognosis", "keywords": ["outcome", "risk factor"]},
    ],
    "sections": [
        {
            "filename": "01-introduction.qmd",
            "heading": "# Introduction",
            "subtopics": ["epidemiology"],
            "word_target": "1,200-1,500",
            "writing_instructions": "Write about MASLD burden.",
        },
        {
            "filename": "02-methods.qmd",
            "heading": "# Methods",
            "subtopics": [],
            "word_target": "800-1,000",
            "writing_instructions": "Write the methods section.",
        },
        {
            "filename": "03-pharmacotherapy.qmd",
            "heading": "# Pharmacotherapy",
            "subtopics": ["pharmacotherapy"],
            "word_target": "1,500-1,800",
            "writing_instructions": "Write about GLP-1 receptor agonists for MASLD.",
        },
    ],
}


# --------------------------------------------------------------------------
# classify_article_subtopic / ensure_balanced_coverage: legacy default unchanged
# --------------------------------------------------------------------------

def test_classify_default_still_uses_hlh_taxonomy():
    # HLH article should hit HLH-specific categories with the default taxonomy
    cats = classify_article_subtopic(HLH_ARTICLE)
    assert "genetics" in cats


def test_classify_glp1_article_falls_to_general_under_hlh_taxonomy():
    # This is exactly the bug: a non-HLH article gets no meaningful category
    cats = classify_article_subtopic(GLP1_ARTICLE)
    assert cats == ["general"]


def test_classify_glp1_article_matches_under_dynamic_taxonomy():
    taxonomy = {c["name"]: c["keywords"] for c in FAKE_PLAN_JSON["categories"]}
    cats = classify_article_subtopic(GLP1_ARTICLE, taxonomy=taxonomy)
    assert "pharmacotherapy" in cats


def test_ensure_balanced_coverage_respects_dynamic_taxonomy():
    taxonomy = {c["name"]: c["keywords"] for c in FAKE_PLAN_JSON["categories"]}
    articles = [GLP1_ARTICLE] + [
        _article(f"Filler {i}", "no relevant keywords here", f"10.1/filler{i}")
        for i in range(5)
    ]
    selected = ensure_balanced_coverage(articles, target_count=3, taxonomy=taxonomy)
    assert GLP1_ARTICLE in selected


# --------------------------------------------------------------------------
# topic_planner: task generation + result collection
# --------------------------------------------------------------------------

def test_generate_taxonomy_task_writes_prompt_with_topic_and_output_path(tmp_path):
    task = generate_taxonomy_task("GLP-1 agonists for MASLD", [GLP1_ARTICLE], tmp_path)
    assert "GLP-1 agonists for MASLD" in task.prompt
    assert str(task.output_path) in task.prompt
    assert task.model == "sonnet"  # NOT haiku — this call shapes every section


def test_collect_taxonomy_result_parses_agent_output(tmp_path):
    (tmp_path / "topic_plan.json").write_text(json.dumps(FAKE_PLAN_JSON), encoding="utf-8")
    plan = collect_taxonomy_result("GLP-1 agonists for MASLD", tmp_path)
    assert plan is not None
    assert set(plan.taxonomy.keys()) == {"epidemiology", "pharmacotherapy", "prognosis"}
    assert plan.important_categories == ["epidemiology", "pharmacotherapy", "prognosis"]
    assert [s.filename for s in plan.sections] == [
        "01-introduction.qmd", "02-methods.qmd", "03-pharmacotherapy.qmd",
    ]


def test_collect_taxonomy_result_missing_file_returns_none(tmp_path):
    assert collect_taxonomy_result("x", tmp_path) is None


def test_collect_taxonomy_result_malformed_returns_none(tmp_path):
    (tmp_path / "topic_plan.json").write_text(json.dumps({"categories": []}), encoding="utf-8")
    assert collect_taxonomy_result("x", tmp_path) is None


# --------------------------------------------------------------------------
# dispatch_sections / generate_main_qmd: dynamic plan wiring end-to-end
# --------------------------------------------------------------------------

def _stats() -> ReviewStatistics:
    return ReviewStatistics(
        total_articles_found=10, articles_after_dedup=10, articles_after_quality_filter=10,
        articles_with_valid_doi=10, articles_included=1, journals_represented=1,
        date_range="2020-2026", avg_citation_count=0,
    )


def test_dispatch_sections_defaults_to_hlh_plan(tmp_path):
    dispatched = dispatch_sections([HLH_ARTICLE], _stats(), tmp_path)
    assert set(dispatched.keys()) == {s.filename for s in HLH_SECTIONS}


def test_dispatch_sections_uses_dynamic_plan_and_matches_topic_articles(tmp_path):
    taxonomy = {c["name"]: c["keywords"] for c in FAKE_PLAN_JSON["categories"]}
    from litreview.pipeline.section_dispatcher import SectionSpec
    dyn_sections = [
        SectionSpec(**{k: v for k, v in s.items()}) for s in FAKE_PLAN_JSON["sections"]
    ]

    dispatched = dispatch_sections(
        [GLP1_ARTICLE], _stats(), tmp_path, sections=dyn_sections, taxonomy=taxonomy,
    )
    assert set(dispatched.keys()) == {"01-introduction.qmd", "02-methods.qmd", "03-pharmacotherapy.qmd"}
    # The GLP-1 article must land in the pharmacotherapy section, not be dropped/mismatched
    assert dispatched["03-pharmacotherapy.qmd"]["article_count"] == 1
    assert "Semaglutide" in dispatched["03-pharmacotherapy.qmd"]["article_context"]


def test_generate_main_qmd_include_list_matches_dynamic_sections(tmp_path):
    from litreview.pipeline.section_dispatcher import SectionSpec
    dyn_sections = [
        SectionSpec(**{k: v for k, v in s.items()}) for s in FAKE_PLAN_JSON["sections"]
    ]
    qmd = generate_main_qmd("GLP-1 agonists for MASLD", _stats(), tmp_path, sections=dyn_sections)
    assert "{{< include sections/03-pharmacotherapy.qmd >}}" in qmd
    assert "05-etiology" not in qmd  # legacy HLH filename must not leak in
    assert "08-discussion" not in qmd


def test_generate_main_qmd_defaults_to_hlh_sections(tmp_path):
    qmd = generate_main_qmd("adult HLH", _stats(), tmp_path)
    assert "{{< include sections/08-discussion.qmd >}}" in qmd
