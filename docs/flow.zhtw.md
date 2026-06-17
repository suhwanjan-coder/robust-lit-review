# 執行流程圖（繁體中文）

這套系統是「兩層」協作:

- **引擎層(細線)** — Python 套件 `litreview`,做確定性的資料工程(檢索、去重、品質過濾、DOI 驗證、統計、BibTeX)。對應 `lit-review review` CLI。
- **智慧層(粗線)** — Claude Code skill + 子代理,做需要判斷力的學術寫作(抽臨床數據、平行寫章節、PRISMA 稽核、投稿信、渲染)。只有 `/lit-review` 斜線指令會啟動。

```mermaid
flowchart TD
    A["輸入主題<br/>topic + 關鍵詞"] --> B["① 產生檢索式<br/>廣式 + 收斂式 Boolean query"]

    B --> C{{"② 平行檢索<br/>asyncio 同時打"}}
    C --> C1["Scopus<br/>需機構訂閱"]
    C --> C2["PubMed<br/>免費（要填金鑰）"]
    C --> C3["Embase<br/>需機構訂閱"]
    C1 --> D["③ 去重<br/>DOI 為主鍵 / 標題比對"]
    C2 --> D
    C3 --> D

    D --> E["④ 期刊品質過濾<br/>CiteScore / SJR 分位 Q1-Q2<br/>指標來自 Scimago / OpenAlex"]
    E --> F["⑤ DOI 驗證 + OA 補強<br/>Unpaywall 逐篇驗證"]
    F --> G["⑥ 平衡選文<br/>按子主題挑出目標篇數"]

    G --> H["⑦ 匯出 Zotero<br/>+ BibTeX + 統計 + PRISMA 數字"]

    H -. "CLI 路徑到此為止" .-> Z1["產出：references.bib<br/>+ .qmd 骨架 + 統計"]

    H ==> I["⑥' Haiku 抽臨床數據<br/>劑量 / p值 / 樣本數"]
    I ==> J["⑧ 平行寫作<br/>8 個子代理同時寫 8 章節"]
    J ==> K{"⑨ PRISMA 27 項稽核"}
    K -- "有缺項" --> L["派修補代理補寫"]
    L --> K
    K -- "全過" --> M["⑩ 投稿信 + Quarto 渲染"]
    M --> Z2["產出：PDF + DOCX + 投稿信<br/>（push 後 GitHub 自動 Release）"]

    subgraph LEGEND ["圖例"]
        direction LR
        P1["細線 = CLI 引擎層（純資料）"]
        P2["粗線 = 斜線指令才有的智慧層（Claude 子代理）"]
    end
```

## 兩種啟動方式

| 方式 | 跑到哪 | 產出 |
|---|---|---|
| `lit-review review "主題"`（CLI） | ①–⑦（只有引擎層） | `references.bib` + `.qmd` 骨架 + 統計 |
| `/lit-review "主題"`（Claude Code 斜線指令） | ①–⑩（引擎 + 智慧層全跑） | 可投稿的 PDF / DOCX + 投稿信 |
