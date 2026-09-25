# _HANDOFF.md — robust-lit-review

**2026-09-25 18:39 · ACHIH-MAIN (local) · Claude Code** — rolling single file, newest entry first (keep last 3).
Written for a cold start in a **cloud session** (no access to the local machine, `.env`, or local drives).

## Entry 1 — 2026-09-25: moving to cloud

**1. Goal / scope.** Fork of `htlin222/robust-lit-review` (topic → PRISMA systematic-review manuscript).
Run `/lit-review "<topic>"` in a Claude Code session opened in this repo. Repo is public; local `main` == `origin/main`.

**2. Important paths (repo-relative).**
`src/litreview/pipeline/` (`topic_planner.py`, `section_dispatcher.py`, `prisma_audit.py`, `enrichment.py`) ·
`.claude/skills/lit-review/SKILL.md` (the skill; read Stage 3.5 and Stage 7) · `tests/` ·
`output-mm/`, `output-dlbcl/`, `output-glp1masld/` = committed worked examples.
**`output/` is the upstream author's committed HLH example — never write new runs there.** Use `output-<topic>/`.

**3. Done (verified).** Six upstream bugs fixed and pushed. `pytest tests/` → 47 passed.
(a) PubMed empty `api_key` → NCBI 400. (b) SKILL.md hardcoded author's Mac paths.
(c) Stage 6 subtopic taxonomy + section plan were hardcoded to the author's HLH review → any other topic fell into "general" and got HLH writing briefs; now generated per topic by `topic_planner.py` (Stage 3.5).
(d) `prisma_audit.py` had the same hardcoding → role-based `role_files`.
(e) `generate_main_qmd()`: abstract inside YAML broke on `**Bold:**`; section headings were never inserted.
(f) Silent Scopus failure guard: `AbstractFetchReport` / `verify_scopus_abstract_access()` (see item 7).
End-to-end proof: `output-glp1masld/` (GLP-1 × MASLD; 33-page PDF + DOCX; PRISMA audit 14/36 → 32/36, 0 fail; 45/45 citation keys resolve in `references.bib`).

**4. Decisions.** Topic-plan agent uses a mid-tier model, not the cheapest (it steers every section). Legacy HLH tables kept as fallback (`HLH_SUBTOPIC_TAXONOMY`, `HLH_SECTIONS`). No upstream PR opened (owner has not asked).

**5. Do NOT retry.** Writing test runs into `output/`. Putting the abstract in the YAML `abstract:` block. Trusting `check-config` OK as proof Scopus works (it only checks a non-empty key).

**6. Commands that work.**
`uv venv && uv pip install -e ".[dev]"` · `.venv\Scripts\python.exe -m pytest tests/ -q` · `lit-review check-config`.
Search + dedup + validate half: `LitReviewPipeline` in `pipeline/orchestrator.py`. Writing half is agent-orchestrated by the skill, not the CLI (the CLI `review` command does NOT write the manuscript).

**7. Flaky / dangerous — READ THIS FOR CLOUD.**
- **Scopus abstracts need the institution's network (VPN).** Off-network the Abstract Retrieval API returns **HTTP 200 with empty text** (measured: 0 chars off-VPN vs ~2000 chars on-VPN, same records). No error is raised. Cloud egress is not on that network → expect empty Scopus abstracts; only PubMed abstracts will be real. The guard logs a loud warning when this happens. Scopus *search* (titles/DOIs) still works anywhere.
- **API keys are not in the repo and must be set in the cloud environment**: `SCOPUS_API_KEY`, `PUBMED_API_KEY`, `UNPAYWALL_EMAIL`. Never write values into commits, tests, or logs. `.env` is gitignored (verified: 0 hits for key values in tracked files and full history).
- PDF/DOCX render needs Quarto + a TeX distribution (TinyTeX). Not guaranteed in cloud; if missing, produce `.qmd` + `.bib` and render locally.
- Passing `taxonomy=`/`sections=`/`role_files=` is required for non-HLH topics; omitting them silently falls back to HLH.

**8. Next action.** Pick the real topic, then follow SKILL.md Stage 1→9 with `output-<topic>/`. For a Scopus-full run (real abstracts), do the search+abstract stage locally on VPN, commit `validated_pool.json`, then continue writing in cloud.

**9. Owner preferences.** Ask before adding unrequested features; commit/push only on explicit instruction; deletions only when told; results must come from real runs, not "config shows OK".

**10. Deferred / stays local.** Embase key (not obtained; often not in institutional entitlement). Whether to send the fixes upstream. `llm_prisma_judge.py` (Stage 7 Method B) not checked for the same hardcoding. Local-only by nature: VPN-dependent Scopus abstract fetching, the local handover ledger, the local LLM host, NotebookLM login.
