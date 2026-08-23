"""Topic-specific review plan generation.

The original pipeline shipped with a subtopic taxonomy and section structure
hardcoded for one topic (adult HLH — see enrichment.HLH_SUBTOPIC_TAXONOMY and
section_dispatcher.HLH_SECTIONS). That hardcoding meant `/lit-review` silently
produced a mismatched manuscript for any other topic: articles wouldn't match
any subtopic keyword, and section writing agents would be briefed with HLH-
specific instructions (gene names, drug names, criteria) regardless of the
actual topic.

This module replaces the hardcoded taxonomy/sections with a one-time LLM
planning call: given the topic and a sample of the actually-selected articles,
an agent proposes (a) a subtopic keyword taxonomy grounded in what the corpus
actually discusses, and (b) a section-by-section writing plan.

Usage from SKILL.md (Stage 3.5, before article selection):
1. Python:       task = generate_taxonomy_task(topic, articles, output_dir)
2. Claude Code:   dispatch Agent(prompt=task.prompt) — NOT haiku; this one call
                  shapes every later section, so use the session's default model.
3. Python:       plan = collect_taxonomy_result(output_dir)
4. Pass plan.taxonomy / plan.important_categories into
   enrichment.ensure_balanced_coverage() and plan.sections into
   section_dispatcher.dispatch_sections() / generate_main_qmd().
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from litreview.models import ArticleMetadata
from litreview.pipeline.section_dispatcher import SectionSpec
from litreview.utils.llm import SubagentTask, parse_json_result

logger = logging.getLogger(__name__)

TAXONOMY_OUTPUT_FILENAME = "topic_plan.json"

PLANNING_SYSTEM = """You are a systematic-review methodologist designing the structure \
of a literature review manuscript for a specific topic, grounded in a sample of the \
articles that were actually found for it."""

PLANNING_PROMPT_TEMPLATE = """Topic: {topic}

Below are titles and abstracts from a sample of the articles retrieved for this topic \
(article count: {sample_size} of {total_count} selected).

{article_sample}

Design a review plan for this specific topic and corpus. Return ONLY this JSON \
structure (no markdown, no explanation):

{{
  "categories": [
    {{
      "name": "<short_snake_case_id, e.g. 'pharmacotherapy'>",
      "keywords": ["<5-10 lowercase keyword/phrase stems that would appear in this \
topic's abstracts if an article belongs to this category, e.g. 'glp-1', 'semaglutide', \
'agonist'>"]
    }}
    // 6-10 categories total, covering: epidemiology/burden, mechanism/pathophysiology,
    // diagnosis/staging (if applicable), the main treatment/intervention modalities for
    // THIS topic (split into multiple categories if there are several distinct
    // modalities — do not reuse HLH's categories unless the topic is HLH), and
    // prognosis/outcomes. Add topic-specific categories the corpus actually supports
    // (e.g. comorbidities, special populations) instead of forcing articles into a
    // generic bucket. Keywords must be grounded in terms you actually saw in the
    // abstracts above, not generic guesses.
  ],
  "sections": [
    {{
      "filename": "01-introduction.qmd",
      "heading": "# Introduction",
      "subtopics": ["<category names from above that feed this section>"],
      "word_target": "1,200-1,500",
      "writing_instructions": "<Specific instructions for this section: what it must \
cover for THIS topic, in the same level of concrete detail as a domain expert would \
give — name the actual disease entities, drug classes, mechanisms, or criteria \
relevant to THIS topic. Do not write generic placeholder instructions.>"
    }}
    // Always include, in order: 01-introduction.qmd, 02-methods.qmd (subtopics: [],
    // methodological — search strategy, PRISMA flow, inclusion/exclusion criteria),
    // then 3-6 body sections tailored to this topic's actual categories above
    // (numbered 03, 04, 05... .qmd), then a final NN-discussion.qmd (subtopics:
    // whichever categories best support synthesis + prognosis/outcomes).
    // Total 5-9 sections. Word targets should sum to roughly 6,000-9,000 words.
  ]
}}"""


@dataclass
class ReviewPlan:
    """Topic-specific taxonomy + section structure, replacing the hardcoded HLH ones."""

    topic: str
    taxonomy: dict[str, list[str]] = field(default_factory=dict)
    sections: list[SectionSpec] = field(default_factory=list)

    @property
    def important_categories(self) -> list[str]:
        """All category names, for enrichment.ensure_balanced_coverage()."""
        return list(self.taxonomy.keys())


def _sample_articles_for_prompt(articles: list[ArticleMetadata], max_sample: int = 20) -> tuple[list[ArticleMetadata], str]:
    """Pick a representative sample and render it as title/abstract blocks."""
    sample = articles[:max_sample]
    blocks = []
    for i, a in enumerate(sample, 1):
        abstract = (a.abstract or "")[:400]
        blocks.append(f"{i}. {a.title}\n   {abstract}")
    return sample, "\n\n".join(blocks)


def generate_taxonomy_task(
    topic: str,
    articles: list[ArticleMetadata],
    output_dir: Path,
    max_sample: int = 20,
) -> SubagentTask:
    """Generate the single planning task for the topic-specific review plan.

    Dispatch as Agent(prompt=task.prompt) — deliberately NOT model="haiku": this
    one call determines every category and section instruction downstream, so it
    should use the session's default (stronger) model, unlike the high-volume
    per-article haiku tasks elsewhere in the pipeline.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / TAXONOMY_OUTPUT_FILENAME

    sample, article_sample = _sample_articles_for_prompt(articles, max_sample)
    prompt = (
        f"{PLANNING_SYSTEM}\n\n"
        f"{PLANNING_PROMPT_TEMPLATE.format(
            topic=topic,
            sample_size=len(sample),
            total_count=len(articles),
            article_sample=article_sample,
        )}\n\n"
        f"Write the JSON result to: {output_path}"
    )

    return SubagentTask(
        task_id="topic_plan",
        description=f"Plan review structure: {topic[:40]}",
        prompt=prompt,
        output_path=output_path,
        model="sonnet",
    )


def collect_taxonomy_result(topic: str, output_dir: Path) -> ReviewPlan | None:
    """Parse the planning agent's result into a ReviewPlan.

    Returns None if the agent's output is missing or malformed — callers should
    fall back to the legacy HLH taxonomy/sections in that case (see
    enrichment.HLH_SUBTOPIC_TAXONOMY / section_dispatcher.HLH_SECTIONS) and warn
    the user, per SKILL.md's "never fail silently" rule.
    """
    output_path = output_dir / TAXONOMY_OUTPUT_FILENAME
    raw = parse_json_result(output_path)
    if not raw:
        return None

    try:
        taxonomy = {
            cat["name"]: [str(k).lower() for k in cat["keywords"]]
            for cat in raw["categories"]
        }
        sections = [
            SectionSpec(
                filename=s["filename"],
                heading=s["heading"],
                subtopics=s.get("subtopics", []),
                word_target=s.get("word_target", "1,000-1,200"),
                writing_instructions=s["writing_instructions"],
            )
            for s in raw["sections"]
        ]
    except (KeyError, TypeError) as e:
        logger.warning(f"Malformed topic plan at {output_path}: {e}")
        return None

    if not taxonomy or not sections:
        logger.warning(f"Empty taxonomy or sections in topic plan at {output_path}")
        return None

    logger.info(
        f"Topic plan for '{topic}': {len(taxonomy)} categories, {len(sections)} sections"
    )
    return ReviewPlan(topic=topic, taxonomy=taxonomy, sections=sections)
