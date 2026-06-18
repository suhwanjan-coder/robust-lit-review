# 專案進度書籤（繁中）

> 給未來的自己 / 下次開啟專案時看的「我們做到哪了」備忘。
> 最後更新：2026-06-18

---

## 這個 repo 是什麼
- Fork 自 `htlin222/robust-lit-review`：自動化系統性文獻回顧流程（搜尋 Scopus/PubMed/Embase → 期刊品質過濾 → DOI 驗證 → 產出 Quarto/PDF/DOCX）。
- 開發分支：**`claude/forked-repo-usage-6ocbbw`**
- 彙整於 **PR #1**：<https://github.com/suhwanjan-coder/robust-lit-review/pull/1>

---

## 已完成
- 做了一份 **GLP-1 受體促效劑用於肥胖治療** 的範例文獻回顧（demo）。
  - 位置：`output/glp1-obesity/`
  - 內容：封面頁、結構化摘要、PRISMA 流程圖（圖1）、5 大子主題章節、安全性、結論與限制。
  - 特色：**全繁體中文**（已修掉 Quarto 自動產生的簡體「小节/目录」）、引用自動編號、參考文獻附真實 DOI。
  - 資料來源：PubMed 真實檢索（2026-06，20 篇 Q1 文獻）。精確數字均自原文摘要核對，其餘為方向性陳述。
- 已在雲端環境驗證可渲染：裝好 Quarto + xelatex + Noto CJK 字型 + xeCJK，PDF/DOCX 皆正常產出。
- `.gitignore` 已修正：`output*/**/*` 遞迴忽略渲染產物（PDF/DOCX/tex/aux/log），只把源碼（`.qmd/.bib/.dot/.png`）進版控。

### `output/glp1-obesity/` 檔案
| 檔案 | 說明 | 進版控 |
|---|---|---|
| `literature_review.qmd` | 稿件源碼 | ✅ |
| `references.bib` | 參考文獻（含驗證 DOI） | ✅ |
| `prisma-flow.dot` | PRISMA 圖源碼（graphviz） | ✅ |
| `prisma-flow.png` | PRISMA 圖 | ✅ |
| `literature_review.pdf` / `.docx` | 成品（被忽略，需自行 render 或用先前傳的檔） | ❌ |

---

## ⚠️ 重要：別動到別人的作品
- `output/literature_review.*`、`output/sections/`、`output/prisma-flow-diagram/`、`output/cover_letter.qmd`
  是 **fork 來源那位醫師的 HLH（噬血細胞淋巴組織球增多症）系統性回顧**，請勿覆蓋。

---

## 重要觀念（新手筆記）
- **PR 頁面只顯示程式碼差異（食譜），不會顯示漂亮的 PDF/網頁（做好的菜）。** 成品要另外「渲染(render)」出來。
- 在 GitHub 上看成品的三種方式：
  1. **Releases**：PR 合併進 `main` 後，`render-release.yml` 會自動產出可下載的 PDF/Word（目前只 render 根目錄的 HLH 那份）。
  2. **commit PDF**：可用 GitHub 內建 PDF 預覽（但目前 PDF 被 gitignore）。
  3. **GitHub Pages**：把文件 render 成 HTML 發佈成網站 URL（`suhwanjan-coder.github.io/...`），點開即看 —— 這是「把 repo 變網頁」的做法，**尚未設定**。

---

## 待辦 / 下次可以做（都還沒決定，不急）
- [ ] 想要**網頁版** → 設定 GitHub Pages（render qmd → HTML → 發佈）。
- [ ] 想在**自己電腦跑** → 安裝 Quarto，`cd output/glp1-obesity && quarto render literature_review.qmd`。
- [ ] 想接**真實資料** → 在 `.env` 填 PubMed（免費）金鑰；之後若有學校 Elsevier 通道再接 Scopus/Embase。
- [ ] 想把 demo **加長/加章節**。
- [ ] 想讓 `render-release.yml` 也涵蓋 `output/glp1-obesity/`（目前只處理根目錄）。

---

## 怎麼在自己電腦取得這些檔案
```bash
# 第一次：clone 下來並切到開發分支
cd ~/Desktop
git clone https://github.com/suhwanjan-coder/robust-lit-review.git
cd robust-lit-review
git checkout claude/forked-repo-usage-6ocbbw

# 之後：更新
git pull origin claude/forked-repo-usage-6ocbbw
```
> 注意：git 抓下來只有源碼，**沒有 PDF/Word**（被忽略）。要成品就自己 `quarto render`，或用對話中傳的檔案。
