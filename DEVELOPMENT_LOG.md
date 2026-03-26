# Development Log — Datasheet PDF Auto-Generation System

> 完整開發歷程記錄，供團隊成員或未來 AI session 參考

## Phase 0：需求與準備

**提供的素材：**
- 5 份設計師做好的 PDF datasheet 範本（`Template PDF/`）
  - `DS_Cloud_ECC100_v1.1.pdf`（Camera）
  - `DS_Cloud_ECW515_v1.2.pdf`、`DS_Cloud_ECW260_v1.1.pdf`（Access Point）
  - `DS_Cloud_ECS2530FP_v1.0.pdf`（Switch）
  - `DS_Cloud_ESG610_v1.5.pdf`（Gateway）
- Google Sheets 規格表（8 個 tab，上百個產品規格）
- Google Drive 圖片資料夾
- 兩個參考系統（舊版 datasheet 系統 + 名片系統）

**目標：**
- 不要每次改規格就請設計師重做 PDF
- 同事可以自己操作、預覽、存 PDF
- 規格從 Google Sheets 自動讀取，改了就反映

## Phase 1：技術選型

| 決策 | 選項 | 最終選擇 | 原因 |
|------|------|---------|------|
| PDF 引擎 | Playwright vs WeasyPrint | WeasyPrint | Playwright >250MB 超過 Vercel 限制，兩者切換成本低 |
| 版型方式 | HTML/CSS vs reportlab | HTML/CSS + Jinja2 | 好維護、好調整、可直接預覽 |
| 部署平台 | Vercel vs Railway vs Fly.io | Vercel | 免費、GitHub auto-deploy、最簡單 |
| 資料來源 | Google Sheets API vs CSV export | CSV export | 不需 API key，直接用公開連結 |
| 排版方式 | Flexbox/Grid vs 絕對定位 | 混合使用 | 封面用絕對定位精準控制，規格表用 table 動態排列 |

## Phase 2：逆向工程 PDF 範本

用 PyMuPDF 拆解設計師的 PDF，提取：
- 精確座標位置（每個元素的 x, y, width, height）
- 字體（Roboto Light 300 / Regular 400 / Medium 500）
- 顏色（primary blue `#03a9f4`、dark `#231f20`、gray `#6f6f6f`）
- 頁面尺寸（US Letter 612x792pt）
- 版面結構（3 頁：封面 → 規格表 → 硬體概覽）

從 PDF 擷取素材：
- `engenius_cloud_icon.png` — Cloud "G" icon（426x418）
- `ECC100_product.png` — 產品照（616x442）
- `ECC100_hardware.png` — 硬體概覽圖（1207x1199）

## Phase 3：建立 HTML 模板

以 ECC100 Camera 為 prototype，用 HTML/CSS 重建 PDF 版型（cameras.html，3 頁）：
- Page 1：封面（Cloud icon、產品名、Overview、Features、產品照）
- Page 2：規格表（雙欄自動分配）
- Page 3：硬體概覽（標註圖 + Footer）

經過 5 輪微調：
1. Features 背景色從藍色 → 淺灰 `#f0f0f0`（比對原始 PDF）
2. 加上 "Features & Benefits" 標題
3. Cloud icon 跟文字重疊 → 改用絕對定位
4. Overview 文字太擠 → 縮小字體 12pt→11pt
5. 產品圖片位置偏高 → 調整 top 310pt→330pt

## Phase 4：建立資料層

**本地測試資料：**
- 手動從 PDF 抄錄 ECC100 規格 → `data/ECC100.json`
- Pydantic 模型驗證（`ProductBase` → `CameraProduct`）

**Google Sheets 串接：**
- 找出需要的兩個 tab：Detail Specs（GID: 180970413）、Web Overview（GID: 2086236498）
- `sheets_reader.py`：CSV export URL 讀取，不需 API key
- `data_loader.py`：自動判斷用 JSON 還是 Sheets

## Phase 5：建立 Web UI

Flask App routes：
- `/` — Dashboard，所有產品列表
- `/product/<model>` — 產品詳情 + Save as PDF 按鈕
- `/preview/<model>` — 完整 HTML datasheet 預覽
- `/generate/<model>` — POST 生成 PDF（本地用）
- `/download/<model>/<v>` — 下載歷史版本

## Phase 6：部署到 Vercel

1. 建 GitHub repo（private）
2. 設定 `vercel.json`（Python runtime + routes）
3. 遇到 deploy blocked → 修正 git email 對應 GitHub 帳號
4. 成功部署 → `https://datasheet-system.vercel.app`

## Phase 7：修 Bug & 優化（目前進度）

| 項目 | 狀態 |
|------|------|
| UTF-8 亂碼（°, ″ 等符號） | ✅ 已修 |
| Features parsing（單一 cell 解析） | ⚠️ 待驗證 |
| Google Drive 圖片串接 | ⚠️ 決定用 Drive API + API Key，待設定 |
| PDF ≠ HTML 預覽 | ⚠️ 計畫改用 html2pdf.js |

## 待做（依優先順序）

1. Google Drive API Key → 自動抓產品圖片
2. html2pdf.js → PDF 跟預覽完全一致
3. 驗證 features parsing → 確認 Google Sheets 資料正確
4. 其他產品線模板 → Switch、Access Point、Gateway

## 方案比較參考

### PDF 生成方式

| 方案 | 跟預覽一致？ | 文字可選取？ | 成本 | 可在 Vercel？ |
|------|------------|------------|------|-------------|
| html2pdf.js | ✅ | ❌ | 免費 | ✅ |
| 修好列印 CSS | ⚠️ 接近 | ✅ | 免費 | ✅ |
| PDFShift / DocRaptor | ✅ | ✅ | 💰 有免費額度 | ✅ |
| Playwright | ✅ | ✅ | 免費 | ❌ >250MB |
| WeasyPrint on Docker | ✅ | ✅ | 免費 | ❌ 需換平台 |

### 圖片串接方式

| 方案 | 自動化？ | 需要什麼 |
|------|---------|---------|
| Google Drive API + API Key | ✅ 全自動 | Google Cloud Console 建 API Key |
| Google Sheet 加圖片 URL 欄 | ⚠️ 半自動 | 手動貼連結 |
| 手動下載放 static/ | ❌ | 每次手動操作 |

### 部署平台

| 平台 | PDF server-side？ | Docker？ | 免費方案 | Auto-deploy？ |
|------|------------------|---------|---------|-------------|
| Vercel（目前） | ❌ | ❌ | ✅ | ✅ GitHub |
| Railway | ✅ | ✅ | ✅ $5/月額度 | ✅ GitHub |
| Fly.io | ✅ | ✅ | ✅ 有限 | ✅ |
| Google Cloud Run | ✅ | ✅ | ✅ 有免費額度 | ⚠️ 需設定 |
