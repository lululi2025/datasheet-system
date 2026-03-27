# CLAUDE.md — Project Context

> Last updated: 2026-03-27 (session 4)

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

- **Brand colors**: primary blue `#03a9f4`, dark `#231f20`, gray `#6f6f6f`
- **Font**: Roboto (300, 400, 500)
- **Page size**: US Letter (612x792pt)

### 多產品線 Google Sheets（每條產品線一個獨立試算表）

| 產品線 | Sheet ID | Category |
|--------|----------|----------|
| Cloud Camera | `1jQUW9vvqzWEx-pMfPtSxUhf-Ov81cQzzSx16-YX1wqU` | Cameras |
| Cloud AP | `1WFQHS8LnjzIrAJa-Fih3qWCFICagbCQE9jML-ziwUwM` | APs |
| Cloud Switch | `1FkKUH-heE2VwlBsHo1XdPqW1MsQCT27JmFWlVV-Mwjk` | Switches |

每個 Sheet 都有 `Detail Specs` + `Web Overview` 兩個 tab，GID 設定在 `config.py` 的 `PRODUCT_LINES`。

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
- **多產品線支援** — Camera / AP / Switch 三條產品線，前台 Dashboard 有分頁籤
- Google Sheets 讀取模組（每條產品線獨立 Sheet，各有 Detail Specs + Web Overview tab）
- **Switch/AP 解析修正** — 不同 Sheet 格式（category headers、features 用 `- ` 或純文字、欄位名稱差異）
- Flask Web UI（Dashboard + Product 頁面 + HTML Preview）
- Save as PDF 功能（product 頁面按鈕，透過隱藏 iframe 觸發列印）
- Vercel 部署 + GitHub auto-deploy
- Version management 模組（本地用）
- Google Drive API 串接（Service Account，從共用 Drive 讀取產品圖片）
- 產品圖片自動裁切透明邊距（Pillow getbbox）
- QR Code 動態生成（連結到官網產品頁）
- 規格表自動分頁（內容超過一頁時自動換頁）
- PDF 模板色值提取與校正（PyMuPDF + Pillow 像素取樣）
- UTF-8 encoding 修正（Google Sheets CSV 的 `°` `″` 亂碼）

### ⚠️ Pending / Known Issues

- **PDF ≠ HTML 預覽** — 瀏覽器列印會加邊距、吃掉背景色，計畫改用 html2pdf.js 或外部 PDF API
- **Google Drive 圖片未完成** — 需要 Service Account key 或 API Key 才能自動抓圖，目前僅 ECC100/ECC120 有設定 folder ID
- **所有產品線共用 cameras.html 模板** — 目前 fallback 到 cameras.html，尚未為 Switch/AP 建立專用模板
- **Vercel 上無法 server-side 生成 PDF** — WeasyPrint 需要原生 C 函式庫，Vercel 不支援

## 替代方案筆記

當初評估過的其他做法，未來可考慮：

- **Playwright** — 可以 server-side 生成 PDF，但打包後 >250MB 超過 Vercel 限制
- **WeasyPrint on Docker** — 可用但需要換平台（如 Railway, Fly.io, Cloud Run）
- **reportlab / fpdf2** — 純 Python 可在 Vercel 跑，但需完全重寫版型（非 HTML/CSS）
- **Client-side JS PDF**（html2pdf.js, jsPDF）— 不需後端，但排版精確度較差
- **外部 PDF API**（如 PDFShift, DocRaptor）— 最精確，但有成本
- **換部署平台** — Railway / Fly.io / Google Cloud Run 支援 Docker，可跑 WeasyPrint 或 Playwright

## PDF 模板比對方法論

1. **提取精確數值** — 用 PyMuPDF + Pillow 掃描 PDF 像素，`pixel / dpi * 72 = pt`
2. **顏色用像素取樣** — 不能猜，必須從 PDF 取得精確 RGB hex
3. **圖片只設一個維度** — `<img>` 只設 width 或 height，另一個 auto，避免變形
4. **透明邊距先裁掉** — Logo/icon 有透明邊距會導致對齊偏移，用 `Pillow getbbox()` 裁切
5. **從 PDF 提取 logo** — 尺寸顏色 100% 正確，優於用戶另外提供或 CSS 縮放
6. **不確定時先提方案** — 列出 2-3 個選項（含優缺點）讓用戶選，不要猜測執行

### 已驗證的參考色值
| 元素 | Hex |
|---|---|
| 藍色 top bar | `#02a8f4` |
| 規格分類標題背景 | `#6d7781` |
| Features 區塊底色 | `#ebf8fe` |
| Footer 底色 | `#eff0f2` |
| 規格分隔線 | `#bcbec0` |

## Common Pitfalls

- **不要猜顏色** — 必須用 PyMuPDF 像素取樣，之前猜 `#231f20`（黑）實際是 `#6d7781`（灰藍）
- **圖片不要同時設 width + height** — 會造成變形（cloud icon 踩過），只設一個維度
- **Logo 透明邊距會導致對齊偏移** — 必須先裁掉透明邊距再對齊
- **不要改動已經正確的元素** — 調 padding 時不小心改了 header logo 位置，多做少錯
- **底部沒有藍條** — PDF 標注的 42px 是底部邊距，不是藍條
- **QR code 白底要超出 QR 本身** — 參考 PDF 是白色方塊（~4pt padding）內嵌 QR
- **WeasyPrint 在 macOS 需要 Homebrew Python** — 必須用 `.venv/bin/python`（Homebrew Python 3.14）
- **Git commit author 要對應 GitHub 帳號** — 用 `194753981+lululi2025@users.noreply.github.com`
- **Template 命名是 category 的小寫** — `CameraProduct.category = "Cameras"` → `cameras.html`
- **Google Sheets features 格式不統一** — Camera 用 `* `、Switch 用 `- `、AP 純文字換行，解析時都要處理
- **不同 Sheet 的欄位名稱不同** — Camera 有 "Model Description"，Switch/AP 用 "Excerpt"；Overview 欄位名也不同
- **Switch Sheet 的 category header 是空值行** — 不像 Camera 有明確的 category 名稱，Switch 用空值行當分隔線
- **專案路徑有空格** — `/Users/lulu/AI Project/Datasheet System/`，指令要加引號
- **Google Drive MCP 工具只能搜資料夾和 Google Docs** — 圖片檔需用 Drive API
- **Vercel deploy blocked by unknown committer** — 用 `vercel deploy --prod --yes` CLI 繞過

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
