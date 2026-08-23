"""PRISMA 2020 self-audit and manuscript repair system.

Checks each of the 27 PRISMA items against the actual manuscript content,
identifies gaps, and generates targeted fix instructions for writing agents.

Usage in the pipeline:
1. After all sections are written, run audit()
2. If gaps found, dispatch repair agents for specific sections
3. Re-audit until all items pass
4. Generate the final checklist with pass/fail status
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AuditItem:
    """A single PRISMA checklist item with audit result."""

    number: str  # e.g., "1", "13a"
    section: str  # e.g., "Title", "Synthesis methods"
    description: str  # The checklist requirement
    required_in: list[str]  # Which section files should contain this
    check_keywords: list[str]  # Keywords to search for
    status: str = "unchecked"  # "pass", "fail", "partial", "n/a"
    evidence: str = ""  # Where/how it was found
    fix_instruction: str = ""  # What the repair agent should do


# All 27 PRISMA 2020 items with audit rules.
#
# `required_in` holds ROLE names, not literal filenames — the original version
# of this file hardcoded the author's own HLH section filenames
# (03-pathogenesis.qmd, 08-discussion.qmd, etc.), so the audit silently found
# nothing for any other topic's differently-named sections. Roles are resolved
# to actual filenames by audit_manuscript()'s `role_files` argument; see
# LEGACY_ROLE_FILES below for the mapping default (backward-compatible with
# the original HLH example) and topic_planner.ReviewPlan for how a dynamic
# plan's sections should be mapped instead.
#
# Roles: "main" (assembled manuscript), "abstract", "introduction", "methods",
# "body" (all topic-specific content sections), "discussion", "checklist".
PRISMA_ITEMS: list[AuditItem] = [
    # TITLE
    AuditItem("1", "Title", "Identify the report as a systematic review",
              ["main"], ["systematic review", "systematic literature review"]),

    # ABSTRACT
    AuditItem("2", "Abstract", "Structured summary with background, methods, results, conclusions",
              ["abstract"], ["background", "method", "result", "conclusion"]),

    # INTRODUCTION
    AuditItem("3", "Rationale", "Describe the rationale for the review in context of existing knowledge",
              ["introduction"], ["rationale", "gap", "needed", "importance", "significance"]),
    AuditItem("4", "Objectives", "Provide explicit statement of objectives or questions",
              ["introduction"], ["objective", "aim", "purpose", "question"]),

    # METHODS
    AuditItem("5", "Eligibility criteria", "Specify inclusion and exclusion criteria",
              ["methods"], ["inclusion criteria", "exclusion criteria", "eligible", "excluded"]),
    AuditItem("6", "Information sources", "Specify all databases and sources searched",
              ["methods"], ["scopus", "pubmed", "embase", "database"]),
    AuditItem("7", "Search strategy", "Present full search strategies for all databases",
              ["methods"], ["search strateg", "boolean", "mesh", "keyword", "search term"]),
    AuditItem("8", "Selection process", "Specify methods to decide study inclusion",
              ["methods"], ["screening", "selection", "reviewer", "title and abstract"]),
    AuditItem("9", "Data collection", "Specify methods to collect data from reports",
              ["methods"], ["data extraction", "data collection", "extraction form", "standardized"]),
    AuditItem("10a", "Data items - Outcomes", "List and define all outcomes sought",
              ["methods"], ["outcome", "endpoint", "variable"]),
    AuditItem("10b", "Data items - Variables", "List and define all other variables sought",
              ["methods"], ["variable", "study design", "sample size", "demographics"]),
    AuditItem("11", "Risk of bias", "Specify methods to assess risk of bias",
              ["methods"], ["risk of bias", "quality assessment", "bias", "newcastle-ottawa", "amstar", "quadas"]),
    AuditItem("12", "Effect measures", "Specify effect measures used in synthesis",
              ["methods"], ["effect measure", "narrative synthesis", "thematic", "qualitative synthesis"]),
    AuditItem("13a", "Synthesis - Eligibility", "Describe which studies eligible for each synthesis",
              ["methods"], ["eligible", "synthesis", "thematic"]),
    AuditItem("13b", "Synthesis - Data prep", "Describe data preparation methods",
              ["methods"], ["data preparation", "data extraction", "standardized form"]),
    AuditItem("13c", "Synthesis - Display", "Describe tabulation or visual display methods",
              ["methods"], ["table", "figure", "flow diagram", "prisma", "visual"]),
    AuditItem("13d", "Synthesis - Methods", "Describe synthesis methods and rationale",
              ["methods"], ["narrative synthesis", "thematic", "qualitative", "synthesis approach"]),
    AuditItem("13e", "Synthesis - Heterogeneity", "Describe methods to explore heterogeneity",
              ["methods"], ["heterogeneity", "subgroup", "thematic group", "domain"]),
    AuditItem("13f", "Synthesis - Sensitivity", "Describe any sensitivity analyses",
              ["methods"], ["sensitivity", "robustness"]),
    AuditItem("14", "Reporting bias", "Describe methods to assess reporting bias",
              ["methods", "discussion"], ["reporting bias", "publication bias", "missing results"]),
    AuditItem("15", "Certainty assessment", "Describe methods to assess certainty of evidence",
              ["methods"], ["certainty", "grade", "quality of evidence", "confidence"]),

    # RESULTS
    AuditItem("16a", "Study selection - Flow", "Describe search/selection results with flow diagram",
              ["methods"], ["prisma", "flow diagram", "figure", "identified", "included", "excluded"]),
    AuditItem("16b", "Study selection - Exclusions", "Cite excluded studies and explain why",
              ["methods"], ["excluded", "exclusion", "reason", "citescore", "case report"]),
    AuditItem("17", "Study characteristics", "Cite each included study and present characteristics",
              ["body"], ["@"]),  # Check for citations
    AuditItem("18", "Risk of bias in studies", "Present risk of bias assessments",
              ["methods", "discussion"], ["risk of bias", "quality", "limitation"]),
    AuditItem("19", "Individual results", "Present summary statistics and effect estimates",
              ["body"], ["%", "p =", "p <", "hazard ratio", "odds ratio", "confidence interval", "n ="]),
    AuditItem("20a", "Synthesis summary", "Summarize characteristics of contributing studies per synthesis",
              ["body"], ["studies", "articles", "review", "trial"]),
    AuditItem("20b", "Synthesis results", "Present statistical synthesis results",
              ["body"], ["%", "p ", "response rate", "survival", "mortality", "sensitivity", "specificity"]),

    # DISCUSSION
    AuditItem("23a", "Interpretation", "General interpretation in context of other evidence",
              ["discussion"], ["interpretation", "context", "finding", "synthesis", "advance"]),
    AuditItem("23b", "Evidence limitations", "Discuss limitations of the evidence",
              ["discussion"], ["limitation", "bias", "heterogeneity", "quality"]),
    AuditItem("23c", "Review limitations", "Discuss limitations of the review processes",
              ["discussion"], ["limitation", "weakness", "restrict"]),
    AuditItem("23d", "Implications", "Discuss implications for practice, policy, future research",
              ["discussion"], ["implication", "future", "recommend", "clinical practice", "direction"]),

    # OTHER
    AuditItem("24a", "Registration", "Provide registration info or state not registered",
              ["checklist"], ["registr", "prospero", "not registered"]),
    AuditItem("25", "Support", "Describe funding sources",
              ["checklist"], ["funding", "support", "financial", "no external"]),
    AuditItem("26", "Competing interests", "Declare competing interests",
              ["checklist"], ["competing interest", "conflict of interest", "no competing"]),
    AuditItem("27", "Data availability", "Report public availability of data and code",
              ["checklist"], ["available", "github", "repository", "code", "data"]),
]

# Default role->filename mapping: the original HLH example's fixed layout.
# Backward-compatible fallback for audit_manuscript() when no dynamic
# role_files is supplied.
LEGACY_ROLE_FILES: dict[str, list[str]] = {
    "main": ["literature_review.qmd"],
    "abstract": ["00-abstract.qmd"],
    "introduction": ["01-introduction.qmd"],
    "methods": ["02-methods.qmd"],
    "body": ["03-pathogenesis.qmd", "04-diagnosis.qmd", "05-etiology.qmd", "06-treatment.qmd", "07-covid.qmd"],
    "discussion": ["08-discussion.qmd"],
    "checklist": ["09-prisma-checklist.qmd"],
}


def audit_manuscript(
    sections_dir: Path,
    role_files: dict[str, list[str]] | None = None,
) -> list[AuditItem]:
    """Audit the manuscript against all 27 PRISMA 2020 items.

    Reads section files and checks for required content using keyword matching.
    Returns the list of items with pass/fail status and fix instructions.

    *role_files* maps role name ("methods", "body", "discussion", etc. — see
    PRISMA_ITEMS' docstring) to the actual filename(s) playing that role for
    this manuscript. Defaults to LEGACY_ROLE_FILES (the original HLH example's
    fixed layout). For a topic-specific plan, build it from the plan's
    sections, e.g.:
        role_files = {
            "main": ["literature_review.qmd"], "abstract": ["00-abstract.qmd"],
            "introduction": [plan.sections[0].filename],
            "methods": [plan.sections[1].filename],
            "body": [s.filename for s in plan.sections[2:-1]],
            "discussion": [plan.sections[-1].filename],
            "checklist": ["checklist.qmd"],
        }
    """
    if role_files is None:
        role_files = LEGACY_ROLE_FILES

    # Read all section files
    file_contents: dict[str, str] = {}
    for qmd_file in sections_dir.glob("*.qmd"):
        file_contents[qmd_file.name] = qmd_file.read_text(encoding="utf-8").lower()

    # Also check the main QMD, wherever role_files says it lives
    for main_filename in role_files.get("main", []):
        main_qmd = sections_dir.parent / main_filename
        if main_qmd.exists():
            file_contents[main_filename] = main_qmd.read_text(encoding="utf-8").lower()

    results = []
    for item in PRISMA_ITEMS:
        item = AuditItem(
            number=item.number,
            section=item.section,
            description=item.description,
            required_in=item.required_in,
            check_keywords=item.check_keywords,
        )

        # Resolve this item's roles to actual filenames
        resolved_files = [
            filename for role in item.required_in for filename in role_files.get(role, [])
        ]

        # Check if keywords are found in the required files
        found_in = []
        missing_in = []
        keyword_hits = 0

        for filename in resolved_files:
            content = file_contents.get(filename, "")
            if not content:
                missing_in.append(filename)
                continue

            hits = sum(1 for kw in item.check_keywords if kw.lower() in content)
            if hits > 0:
                found_in.append(f"{filename} ({hits}/{len(item.check_keywords)} keywords)")
                keyword_hits += hits
            else:
                missing_in.append(filename)

        # Determine status
        total_keywords = len(item.check_keywords)
        if not resolved_files or keyword_hits == 0:
            if item.number in ("13f", "20c", "20d"):
                item.status = "n/a"
                item.evidence = "Narrative synthesis — sensitivity analysis not applicable"
            else:
                item.status = "fail"
                item.evidence = f"No keywords found in: {', '.join(resolved_files) or '(no files for role: ' + ', '.join(item.required_in) + ')'}"
        elif keyword_hits >= total_keywords * 0.5:
            item.status = "pass"
            item.evidence = "; ".join(found_in)
        else:
            item.status = "partial"
            item.evidence = f"Found in: {'; '.join(found_in)}. Missing in: {', '.join(missing_in)}"

        # Generate fix instructions for failed/partial items
        if item.status in ("fail", "partial"):
            item.fix_instruction = _generate_fix_instruction(item)

        results.append(item)

    return results


def _generate_fix_instruction(item: AuditItem) -> str:
    """Generate a targeted fix instruction for a failed PRISMA item."""
    fix_map = {
        "1": "Add 'systematic review' to the document title in the YAML frontmatter.",
        "2": "Ensure the abstract contains labeled sections: **Background:**, **Methods:**, **Results:**, **Conclusions:**.",
        "3": "Add 1-2 paragraphs in the Introduction explaining WHY this review is needed — what gap exists in current knowledge.",
        "4": "Add a numbered list of specific objectives at the end of the Introduction section.",
        "5": "Add explicit 'Inclusion Criteria' and 'Exclusion Criteria' subsections in Methods with specific thresholds.",
        "6": "Name all databases searched (Scopus, PubMed, Embase) and the date range in the Search Strategy subsection.",
        "7": "Present the complete Boolean search string used for each database.",
        "8": "Describe how studies were screened: number of reviewers, independence, any automation tools used.",
        "9": "Describe the data extraction process: standardized forms, variables collected, how disagreements were resolved.",
        "10a": "List the specific outcomes extracted from each study (e.g., survival rates, response rates, diagnostic accuracy).",
        "10b": "List all other variables extracted: study design, sample size, patient demographics, follow-up duration.",
        "11": "Describe the tools used to assess study quality (e.g., Newcastle-Ottawa Scale, AMSTAR-2, Cochrane ROB, QUADAS-2).",
        "12": "State that narrative thematic synthesis was used because meta-analysis was not feasible due to study heterogeneity.",
        "13a": "Describe how studies were grouped into thematic categories for synthesis.",
        "13b": "Describe any data transformations or preparations performed before synthesis.",
        "13c": "Reference the PRISMA flow diagram (Figure 1) and any summary tables used.",
        "13d": "Explain the narrative synthesis approach: thematic grouping by domain, cross-study comparison.",
        "13e": "Describe how heterogeneity was explored through thematic subgrouping.",
        "13f": "State that sensitivity analyses were not conducted as this is a narrative synthesis, or add one.",
        "14": "Add a sentence in Methods or Discussion acknowledging potential publication bias and how it was considered.",
        "15": "Describe how the certainty/quality of the evidence body was assessed (e.g., GRADE framework).",
        "16a": "Ensure the PRISMA flow diagram is included with numbers at each stage.",
        "16b": "Add a sentence listing the categories of excluded studies with counts.",
        "17": "Ensure every included study is cited at least once with [@key] syntax in the Results sections.",
        "18": "Add a summary of risk of bias findings, even if brief, in the Methods or Discussion.",
        "19": "Include specific quantitative data from studies: sample sizes, p-values, effect sizes, percentages.",
        "20a": "Add a brief summary of study characteristics at the start of each thematic synthesis section.",
        "20b": "Include statistical results from individual studies when synthesizing findings.",
        "23a": "Add a paragraph interpreting findings in the context of the broader literature.",
        "23b": "Add a subsection discussing limitations of the included evidence (study designs, populations, biases).",
        "23c": "Add a subsection discussing limitations of the review process (search scope, language restriction, etc.).",
        "23d": "Add implications for clinical practice and specific future research priorities.",
        "24a": "State whether the review was registered (e.g., PROSPERO) or explicitly state it was not registered.",
        "25": "State funding sources or declare 'No external funding received.'",
        "26": "Declare competing interests or state 'The authors declare no competing interests.'",
        "27": "State that code and data are available at the GitHub repository URL.",
    }
    return fix_map.get(item.number, f"Address PRISMA item {item.number}: {item.description}")


def format_audit_report(items: list[AuditItem]) -> str:
    """Format the audit results as a readable report."""
    passed = sum(1 for i in items if i.status == "pass")
    failed = sum(1 for i in items if i.status == "fail")
    partial = sum(1 for i in items if i.status == "partial")
    na = sum(1 for i in items if i.status == "n/a")
    total = len(items)

    lines = [
        "## PRISMA 2020 Audit Report",
        "",
        f"**Score: {passed}/{total} passed** ({failed} failed, {partial} partial, {na} N/A)",
        "",
    ]

    if failed + partial == 0:
        lines.append("All PRISMA 2020 items are addressed. The manuscript is ready for submission.")
        lines.append("")
    else:
        lines.append("### Items Requiring Attention")
        lines.append("")
        lines.append("| Item | Section | Status | Fix Required |")
        lines.append("|------|---------|--------|-------------|")
        for item in items:
            if item.status in ("fail", "partial"):
                status_icon = "FAIL" if item.status == "fail" else "PARTIAL"
                lines.append(f"| {item.number} | {item.section} | {status_icon} | {item.fix_instruction} |")
        lines.append("")

    lines.append("### Full Audit Results")
    lines.append("")
    lines.append("| Item | Section | Status | Evidence |")
    lines.append("|------|---------|--------|---------|")
    for item in items:
        status_icon = {"pass": "PASS", "fail": "FAIL", "partial": "PARTIAL", "n/a": "N/A", "unchecked": "?"}[item.status]
        evidence = item.evidence[:80] + "..." if len(item.evidence) > 80 else item.evidence
        lines.append(f"| {item.number} | {item.section} | {status_icon} | {evidence} |")

    return "\n".join(lines)


def generate_repair_prompts(
    items: list[AuditItem],
    role_files: dict[str, list[str]] | None = None,
) -> dict[str, str]:
    """Generate repair prompts for each section file that has failed items.

    *role_files* must match what was passed to audit_manuscript() — see its
    docstring. Defaults to LEGACY_ROLE_FILES.

    Returns a dict mapping section filename to the repair prompt for the writing agent.
    """
    if role_files is None:
        role_files = LEGACY_ROLE_FILES

    repairs: dict[str, list[str]] = {}

    for item in items:
        if item.status not in ("fail", "partial"):
            continue
        for role in item.required_in:
            for filename in role_files.get(role, []):
                repairs.setdefault(filename, []).append(
                    f"- PRISMA Item {item.number} ({item.section}): {item.fix_instruction}"
                )

    prompts = {}
    for filename, fixes in repairs.items():
        prompt = (
            f"The PRISMA 2020 audit found gaps in {filename}. "
            f"Read the current file and ADD the missing content. "
            f"Do NOT rewrite the entire section — only add what is missing.\n\n"
            f"Required fixes:\n" + "\n".join(fixes) + "\n\n"
            f"Rules:\n"
            f"- Insert new paragraphs or sentences at appropriate locations\n"
            f"- Preserve all existing content and citations\n"
            f"- Use [@key] citation syntax where applicable\n"
            f"- Write formal academic prose\n"
            f"- Do NOT add YAML frontmatter\n"
        )
        prompts[filename] = prompt

    return prompts
