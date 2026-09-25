# _HANDOFF.md — robust-lit-review

**2026-09-25 18:39 · ACHIH-MAIN (local) · Claude Code** — rolling single file, newest entry first (keep last 3).
Written for a cold start in a **cloud session** (no access to the local machine, `.env`, or local drives).

## Entry 2（最新）— 2026-09-25 晚：雲端可行性實測＋Python 3.11 相容修正（ACHIH-MAIN，Claude Code）

**目前狀態**：本機 working tree 有 **2 個未 commit 的修改**（等阿志核准才 commit/push，push 到 main 需 bypass，已有 PR 保護）：
`src/litreview/pipeline/topic_planner.py`、`src/litreview/pipeline/llm_extraction.py`。本機 `pytest tests/` 47 passed。

**做了什麼／怎麼驗證**：
- 修正 f-string 大括號內跨行呼叫 `.format(...)`——3.12 以前是 SyntaxError，但 `pyproject.toml` 宣告 `requires-python >=3.11`。本機只有 3.14 所以一直沒發現，是雲端 session（較舊 Python）跑 `pytest` 才撞到（`topic_planner.py:136`）。`llm_extraction.py` 是上游原有的同款寫法。改成先 `body = TEMPLATE.format(...)` 再組 f-string。
- 驗證方式：AST 掃描全 repo（src/tests/scripts）找「f-string 大括號內含換行／同種外層引號」，修前對舊版 `topic_planner.py` 命中 1（掃描器有效），修後全 repo 0 命中。**尚未在真正的 3.11 直譯器上跑過**（本機無 3.11；`py -3.11` 的 rc=0 是管線吃掉錯誤碼的假訊號，不算數）。要確認需在雲端 session 重跑 `python3 -m pytest tests/ -q`。
- 雲端實測（session「Connectivity smoke test」，環境 Default，網路 Trusted）：eutils.ncbi、api.unpaywall.org、doi.org、api.crossref.org、api.elsevier.com **全被出口代理擋（CONNECT 403）**，只有 PyPI 通。`UNPAYWALL_EMAIL` 已讀到。雲端無 Quarto、無 lualatex。

**重要檔案**：`C:\Users\suhwa\dev\robust-lit-review\src\litreview\pipeline\{topic_planner,llm_extraction,enrichment,prisma_audit,section_dispatcher}.py`；`.claude/skills/lit-review/SKILL.md`。

**決策與理由**：
- 阿志問「雲端還是留本機」——建議**留本機**跑真實文獻回顧：本機有 Scopus＋PubMed key、掛台大 VPN 才有 Scopus 真摘要、Quarto＋TinyTeX 已裝。雲端價值只是 Cloud credits（2026/11/05 15:59 到期）。
- 雲端環境設定：Environment variables 那格**明寫「能使用該環境的人都看得到，勿放機密」**，只放了 `UNPAYWALL_EMAIL`（非機密）；**不要在雲端設 Scopus key**（雲端非台大網段，摘要本來就是空的）。「API credentials」機制是代理注入 header、session 看不到值，與本專案「程式自己讀環境變數」的做法不相容，除非改程式，不值得。

**失敗過／不要重試**：只在 Python 3.14 驗證相容性；把 API key 貼進 Environment variables；以為 Trusted 網路能連 PubMed／Elsevier（實測不能）。

**下一步（具體）**：
1. 若阿志同意：commit＋push 那兩個 f-string 修正，再開雲端 session 跑 `python3 -m pytest tests/ -q` 確認 3.11 通過。
2. 雲端要跑文獻回顧，需把 Network access 改 **Custom**，加：`eutils.ncbi.nlm.nih.gov`、`api.unpaywall.org`、`doi.org`、`api.crossref.org`、`api.elsevier.com`（或選 Full）；但即使放行，Scopus 摘要在雲端仍是空的，且 render 要回本機。**阿志目前決定先不改**，等真有題目要在雲端跑再開。
3. 不連外就能做的雲端工作（適合消耗 credits）：檢查 `llm_prisma_judge.py`（Stage 7 Method B）是否有同款寫死 HLH 問題、補測試、重構。

**擱置／未決**：Embase key；修正是否回報上游 htlin222；雲端 Network access 是否放行；雲端 session「0925 ro-lit-review 轉雲端」停在 Waiting on permission、「Connectivity smoke test」已完成可忽略。

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
