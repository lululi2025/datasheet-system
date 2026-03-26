# CLAUDE.md — Project Context

> Last updated: 2026-03-26 (session 2)

## Project Overview

EnGenius Technologies 產品 Datasheet PDF 自動生成系統。從 Google Sheets 讀取產品規格，搭配 Google Drive 圖片，生成專業 PDF datasheet。目前已部署到 Vercel，同事可透過 URL 預覽並存成 PDF。

## Tech Stack

- **Backend**: Flask (Python 3.12 on Vercel, 3.14 local venv)
- **Templating**: Jinja2 HTML → 瀏覽器列印存 PDF
- **Data Models**: Pydantic
- **Data Source**: Google Sheets CSV export（不需 API key）
- **Local PDF**: WeasyPrint（僅本地開發用，Vercel 上無法使用）
- **Deployment**: Vercel（GitHub integration，push 自動部署）

## Directory Structure

```
app.py              # Flask 主應用
config.py           # 系統設定（目錄、品牌色、字體）
models/             # Pydantic 資料模型（ProductBase, CameraProduct）
services/
  sheets_reader.py  # Google Sheets CSV 讀取模組
  data_loader.py    # 資料載入（JSON 或 Sheets）
  pdf_generator.py  # HTML 渲染（圖片用 URL 路徑）
  version_manager.py # 版本管理（本地用）
templates/
  datasheet/        # Datasheet HTML 版型（cameras.html）
  web/              # Web UI（dashboard, product, layout）
static/
  images/           # 產品圖片（ECC100_product.png, ECC100_hardware.png）
  logo/             # EnGenius cloud icon
data/               # 本地 JSON 測試資料（ECC100.json）
Template PDF/       # 設計師原始 PDF 範本（供比對用，不進 git）
```

## Key Config

- **Google Sheet ID**: `1jQUW9vvqzWEx-pMfPtSxUhf-Ov81cQzzSx16-YX1wqU`
- **Detail Specs GID**: `180970413`
- **Web Overview GID**: `2086236498`
- **Brand colors**: primary blue `#03a9f4`, dark `#231f20`, gray `#6f6f6f`
- **Font**: Roboto (300, 400, 500)
- **Page size**: US Letter (612x792pt)

## Deployment

```bash
# 本地開發
.venv/bin/python app.py          # http://localhost:5000

# 部署（push 到 GitHub 自動觸發）
git push origin main

# 手動部署
vercel deploy --prod --yes
```

- **Production URL**: https://datasheet-system.vercel.app
- **GitHub Repo**: https://github.com/lululi2025/datasheet-system (private)

## Current Status

### ✅ Completed

- ECC100 Camera datasheet 版型（3頁：封面、規格表、硬體概覽）
- Google Sheets 讀取模組（Detail Specs + Web Overview 兩個 tab）
- Flask Web UI（Dashboard + Product 頁面 + HTML Preview）
- Save as PDF 功能（product 頁面按鈕，透過隱藏 iframe 觸發列印）
- Vercel 部署 + GitHub auto-deploy
- Version management 模組（本地用）

### ⚠️ Pending / Known Issues

- **Features parsing 可能有問題** — Google Sheets 的 Key Feature Lists 是單一 cell 內 `\n* ` 分隔，已寫好解析邏輯但尚未完整驗證
- **Google Drive 圖片串接** — 決定用 Google Drive API + API Key 自動抓圖。需要到 Google Cloud Console 建專案、啟用 Drive API、建立 API Key。圖片命名規則：`{型號}_product.png`（產品照）、`{型號}_hardware.png`（硬體圖）
- **PDF 輸出方式待改** — 目前用瀏覽器列印存 PDF，但跟 HTML 預覽有差異（邊距、背景色、分頁）。計畫改用 **html2pdf.js**（客戶端截圖式，視覺完全一致，免費，不需換平台）
- **其他產品線模板** — 目前只有 Camera，還需要 Switch、Access Point 等
- **Vercel 上無法 server-side 生成 PDF** — WeasyPrint 需要原生 C 函式庫，Vercel 不支援

## 替代方案筆記

當初評估過的其他做法，未來可考慮：

- **Playwright** — 可以 server-side 生成 PDF，但打包後 >250MB 超過 Vercel 限制
- **WeasyPrint on Docker** — 可用但需要換平台（如 Railway, Fly.io, Cloud Run）
- **reportlab / fpdf2** — 純 Python 可在 Vercel 跑，但需完全重寫版型（非 HTML/CSS）
- **Client-side JS PDF**（html2pdf.js, jsPDF）— 不需後端，但排版精確度較差
- **外部 PDF API**（如 PDFShift, DocRaptor）— 最精確，但有成本
- **換部署平台** — Railway / Fly.io / Google Cloud Run 支援 Docker，可跑 WeasyPrint 或 Playwright

## Common Pitfalls

- **WeasyPrint 在 macOS 需要 Homebrew Python** — 系統 Python 3.9 因 SIP 限制無法載入 `libgobject`，必須用 `.venv/bin/python`（Homebrew Python 3.14）
- **Git commit author 要對應 GitHub 帳號** — 否則 Vercel GitHub integration 會 block deployment。用 `194753981+lululi2025@users.noreply.github.com`
- **Template 命名是 category 的小寫** — `CameraProduct.category = "Cameras"` → template 檔名是 `cameras.html`（注意複數）
- **Google Sheets features 在單一 cell** — 不是多行，是一個 cell 裡用 `\n* ` 分隔，解析時要 split
- **專案路徑有空格** — `/Users/lulu/AI Project/Datasheet System/`，指令要加引號
- **Google Drive MCP 工具只能搜資料夾和 Google Docs** — 無法搜尋/讀取圖片檔（PNG/JPG），需用 Drive API 或請使用者提供分享連結
- **Vercel deploy blocked by unknown committer** — Git commit email 必須對應 GitHub 帳號，用 `194753981+lululi2025@users.noreply.github.com`；或用 `vercel deploy --prod --yes` CLI 直接部署繞過

## Google Drive 圖片資料夾結構

```
Datasheet 素材（共用 Drive）/
  01. Cloud/
    05.Camera/
      ECC100/          ← folder ID: 1Qje0iighD8jaGRkv6Qe4iAEIiwY1nNp4
        ECC100_product.png
        ECC100_hardware.png
      ECC120/          ← folder ID: 1SWB05G3btQ6TtHqxhCAb11ow-9RxmqWq
      ECC500/
```

- 固定圖片（logo、icon）→ 放 `static/logo/`，模板直接引用
- 產品圖片 → 從 Google Drive 動態載入，命名規則 `{型號}_product.png` / `{型號}_hardware.png`
