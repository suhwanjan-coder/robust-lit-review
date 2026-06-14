# 快速上手（繁體中文）

這份是「在自己電腦上把 Robust Literature Review Pipeline 跑起來」的最短路徑。
完整功能說明請看 [README.md](README.md) / [README.zhtw.md](README.zhtw.md)。

---

## 0. 你會用到的東西

- **Python 3.11 以上**
- **[uv](https://docs.astral.sh/uv/)**（套件管理工具，安裝快）
- 至少一把搜尋資料庫的 API 金鑰（見下方「金鑰怎麼選」）

---

## 1. Clone 並安裝

```bash
git clone https://github.com/suhwanjan-coder/robust-lit-review.git
cd robust-lit-review

uv venv && source .venv/bin/activate
uv pip install -e "."
```

裝完後確認 CLI 可用：

```bash
lit-review --help
```

應該會看到 `review` / `validate` / `build-site` / `check-config` 四個指令。

---

## 2. 設定金鑰（`.env`）

```bash
cp .env.example .env
# 用編輯器打開 .env，填入下面任一組金鑰
```

`.env` 欄位：

```
SCOPUS_API_KEY=          # Elsevier/Scopus（學校訂閱後最完整）
PUBMED_API_KEY=          # NCBI（免費）
EMBASE_API_KEY=          # Elsevier/Embase（與 Scopus 同一把，需機構訂閱）
UNPAYWALL_EMAIL=         # 只要填 email（免費）
ZOTERO_API_KEY=          # 書目匯出（免費，選用）
ZOTERO_LIBRARY_TYPE=     # user 或 group
ZOTERO_LIBRARY_ID=
ZOTERO_COLLECTION_KEY=
```

填好後檢查：

```bash
lit-review check-config
```

---

## 金鑰怎麼選（哪些要錢）

| 服務 | 費用 | 申請 | 備註 |
|---|---|---|---|
| **PubMed** | 免費 | [NCBI API Key](https://www.ncbi.nlm.nih.gov/account/) | 金鑰只是把速率拉高；**但本專案目前要填了才會啟用 PubMed 來源** |
| **Unpaywall** | 免費 | [unpaywall.org](https://unpaywall.org/products/api) | 填 email 即可 |
| **Zotero** | 免費 | [Zotero 設定](https://www.zotero.org/settings/keys) | 選用，做書目匯出才需要 |
| **Scopus** | 機構訂閱 | [Elsevier Developer](https://dev.elsevier.com/) | 學校註冊後通常就有 Elsevier 通道；涵蓋管理／政策／健康經濟期刊 |
| **Embase** | 機構訂閱 | 同 Scopus 金鑰 | 商業臨床資料庫 |

> 另外要記得：真正執行 `/lit-review`、`/claim-appraise` 時，撰寫與稽核是靠 **Claude 子代理**，會消耗你的 Claude 用量（透過 Claude Code 訂閱／Anthropic API 計費），不在上表內。

### ⚠️ 重要：PubMed 也要填金鑰才會啟用

程式是「有金鑰才啟用該來源」。雖然 NCBI PubMed 本身免金鑰也能查，但**本專案在沒填 `PUBMED_API_KEY` 時不會把 PubMed 納入搜尋**。所以「最低成本可用配置」是：

> 去 NCBI 免費申請一把 PubMed 金鑰 → 填進 `.env` → 即可跑一條完全免費的文獻回顧線。Scopus／Embase 留空不會當機，學校給了 Elsevier 通道再補上。

---

## 3. 第一次試跑

```bash
# 小規模試跑（先確認流程順）
lit-review review "your research topic" --target 10 --min-citescore 3.0

# 正式規模
lit-review review "your research topic" --target 50 --min-quartile Q1
```

常用參數：

| 參數 | 預設 | 說明 |
|---|---|---|
| `--target` | 50 | 目標納入文章數 |
| `--min-quartile` | Q1 | 最低 SJR 分位（Q1/Q2/Q3/Q4） |
| `--min-citescore` | 3.0 | CiteScore 後備門檻 |
| `--max-results` / `-n` | 100 | 每個資料庫最多抓幾筆 |
| `--no-render` | — | 只產生 `.qmd`／`.bib`，先不渲染 PDF |
| `--output` / `-o` | output | 輸出資料夾 |

產出會在 `output/`：`literature_review.qmd`、`references.bib`、各章節 `sections/`，
渲染後還有 PDF／DOCX（需要安裝 [Quarto](https://quarto.org/)）。

---

## 4. 用斜線指令（Claude Code）

在 clone 下來的資料夾裡開 **Claude Code**，技能已內建於 `.claude/skills/`：

| 指令 | 用途 |
|---|---|
| `/brainstorm-topic` | 先腦力激盪、精煉檢索詞 |
| `/lit-review "主題"` | 完整：搜尋 → 過濾 → 撰寫 → PRISMA 稽核 → 渲染 |
| `/lit-review --hitl "主題"` | 同上，含 9 個人工確認檢查點 |
| `/claim-appraise "某主張"` | 評析一個現實主張，產出 GRADE 裁決網站 |

---

## 其他指令

```bash
# 驗證既有 BibTeX 裡的所有 DOI
lit-review validate output/references.bib

# 把 appraisal.json 渲染成裁決網站
lit-review build-site <path>
```

---

## 跟上游同步

本 repo 是 `htlin222/robust-lit-review` 的 fork。要拉原作者最新更新：

```bash
git remote add upstream https://github.com/htlin222/robust-lit-review.git   # 只需一次
git fetch upstream main
git checkout main && git merge --ff-only upstream/main
git push origin main
```
