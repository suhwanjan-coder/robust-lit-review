# 📌 專案書籤(NOTES.zhtw.md)

> 給未來的自己 / 下次開新對話用。叫 Claude「看一下 NOTES.zhtw.md」就能接上進度。
> 最後更新:2026-06-18

---

## 這個 repo 是什麼

`robust-lit-review` — 自動化系統性文獻回顧 pipeline。一個指令從「主題」產出
可投稿的完整稿件(敘事綜合分析、臨床數據、PRISMA 2020、AMA 引用)。
中文總覽見 `README.zhtw.md`,完整說明見 `README.md`。

- **目前開發分支**:`claude/magical-turing-breym3`
- ⚠️ 注意:這個分支跟之前的 GLP-1 那次(分支 `claude/forked-repo-usage-6ocbbw`)是
  **不同的工作線**,內容不一樣。這份書籤記的是「本分支」的東西。

---

## 🗂️ 這個分支現在有什麼成品

| 位置 | 是什麼 | 狀態 |
|------|--------|------|
| `output/4plus2r/` | **「4+2R 代謝飲食法」claim-appraisal**(本分支主秀,README 的 hero) | 雙語(專業/民眾版)、9 個 PICO 子問題、真實 PRISMA 計數、OpenEvidence 交叉比對、信度面板(Fleiss kappa)。已上 Cloudflare Pages |
| `output-dlbcl/` | 瀰漫性大 B 細胞淋巴瘤(DLBCL)系統性回顧 | 有 `literature_review.pdf` / `.docx` 成品 |
| `output-mm/` | 多發性骨髓瘤(MM)系統性回顧 | 有 `literature_review.pdf` / `.docx` 成品 |
| `output/literature_review.*` 與 `output/sections/` | HLH(噬血細胞症候群)回顧 | ⚠️ **這是 fork 來源醫師的原作,別動它** |

---

## 💡 新手核心觀念

> **PR 看「食譜改了哪」;成品(PDF / 網頁)要另外「煮」出來。**

想看成品的三種方式:
1. **直接點開** repo 裡的 `.pdf` / `.docx`(`output-dlbcl/`、`output-mm/`)
2. **網頁版** → 4+2R 那份可部署成網站(目前用 Cloudflare Pages)
3. **自己電腦煮** → 跑 `quarto render`(見下方待辦)

---

## 📋 待辦選項(都還沒決定,不急)

- [ ] **要不要也把 4plus2r 或其他份做成 GitHub Pages 網頁?**(一句話就能設定)
- [ ] **教在自己電腦跑 `quarto render` 自己生 PDF**
- [ ] **接真實資料** → 在 `.env` 填免費的 PubMed / NCBI 金鑰(見 `.env.example`)
- [ ] **加長 / 加章節** demo 內容
- [ ] 確認本分支與 GLP-1 分支要不要合併或各自獨立

---

## 💻 怎麼把檔案抓到自己電腦

```bash
# 複製整個 repo
git clone https://github.com/suhwanjan-coder/robust-lit-review.git
cd robust-lit-review

# 切到這個工作分支
git checkout claude/magical-turing-breym3

# 成品 PDF/Word 就在:
#   output-dlbcl/literature_review.pdf
#   output-mm/literature_review.pdf
```

想自己重新「煮」PDF(需先裝 Quarto + LaTeX):

```bash
cd output-mm        # 或 output-dlbcl
quarto render literature_review.qmd
```

---

## 🔖 回來時跟 Claude 說的話(範例)

- 「看一下 NOTES.zhtw.md」→ 接上進度
- 「幫我把 4plus2r 設定成 GitHub Pages」→ 變成可點連結的網站
- 「教我在自己電腦跑 quarto render」
- 「幫我把 DLBCL 那份加一個章節」

慢慢消化,有需要再喊我 👋
