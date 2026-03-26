# Datasheet PDF 自動生成系統 — 架構規劃

## 系統總覽

```
Google Sheets (規格資料)  ──┐
Google Drive  (產品圖/說明圖) ──┤──→ Flask Web App ──→ HTML 模板 ──→ WeasyPrint ──→ PDF
Logo 圖檔 (本地/Drive)     ──┘         │                                        │
                                       │                                        ▼
                                  版本管理系統                           output/{model}/
                                  versions.json                    DS_{model}_v{x.y}.pdf
```

## 技術堆疊

| 層級 | 工具 | 說明 |
|------|------|------|
| 資料來源 | Google Sheets CSV export | 免 API key，用公開連結即可讀取 |
| 圖片來源 | Google Drive | 透過 file ID 下載，快取到本地 |
| 後端 | Python + Flask | 跟名片系統一致 |
| 資料驗證 | Pydantic | 確保規格資料完整性 |
| 模板引擎 | Jinja2 HTML + CSS | 條件渲染、迴圈、動態頁數 |
| PDF 引擎 | WeasyPrint（可切換 Playwright） | 切換只需改幾行程式碼 |
| 前端 | Jinja2 Templates + CSS | 操作介面 |
| 部署 | 本機 prototype → Vercel | 先驗證再部署 |

## 一、Google Sheets 規格表設計

### 建議結構（一個 Sheet = 一個產品線）

每個產品線一個 tab，**橫向展開**：

```
| 欄位名稱          | ECW260        | ECW270        | ECW280        |
|-------------------|---------------|---------------|---------------|
| product_name      | ECW260        | ECW270        | ECW280        |
| category          | Outdoor AP    | Outdoor AP    | Outdoor AP    |
| subtitle          | Outdoor Wi-Fi 6 AP | ...      | ...           |
| feature_1         | Dual concurrent... | ...      | ...           |
| feature_2         | Supports up to...  | ...      | ...           |
| ...               |               |               |               |
| standard_1        | IEEE 802.11ax | ...           | ...           |
| antenna_type      | External SMA  | ...           | ...           |
| product_image_id  | (Google Drive file ID) | ...  | ...           |
| hardware_image_id | (Google Drive file ID) | ...  | ...           |
| antenna_img_1_id  | (Google Drive file ID) | ...  | ...           |
```

**為什麼橫向？**
- 新增產品 = 新增一欄（不用動到結構）
- 同產品線可以一眼比較規格差異
- 跟名片系統的「一列一人」邏輯相似但更適合多欄位的規格表

### Google Sheet 需要的 Tabs

| Tab 名稱 | 內容 |
|----------|------|
| Indoor_AP | ECW515 等室內 AP |
| Outdoor_AP | ECW260 等室外 AP |
| Switches | ECS2530FP 等交換器 |
| Cameras | ECC100 等攝影機 |
| Gateways | ESG610 等路由器 |
| _config | 全域設定：公司名、logo Drive ID、footer 文字等 |

## 二、Google Drive 圖片資料夾結構

建議在 Google Drive 建立以下結構：

```
Datasheet_Assets/
├── Logo/
│   └── engenius_logo.png
├── Indoor_AP/
│   ├── ECW515_product.png        ← 產品照（封面用）
│   ├── ECW515_hardware.png       ← 硬體總覽圖
│   ├── ECW515_antenna_24g_h.png  ← 天線圖（依需求）
│   ├── ECW515_antenna_24g_e.png
│   ├── ECW515_antenna_5g_h.png
│   └── ECW515_antenna_5g_e.png
├── Outdoor_AP/
│   ├── ECW260_product.png
│   └── ...
├── Switches/
├── Cameras/
└── Gateways/
```

**圖片在 Google Sheet 中的引用方式**：在對應欄位填入 Google Drive file ID 或完整分享連結，系統會自動解析並下載。

## 三、HTML 模板架構

每個產品線一套模板，但共用 base layout：

```
templates/
├── base.html            ← 共用：頁首/頁尾/CSS/logo
├── indoor_ap.html       ← 繼承 base，Indoor AP 專用版面
├── outdoor_ap.html
├── switch.html
├── camera.html
├── gateway.html
└── components/
    ├── cover_page.html   ← 封面（特色要點 + 產品圖）
    ├── spec_table.html   ← 規格表（自動分欄、跨頁）
    ├── antenna_page.html ← 天線圖頁（2x2 格子）
    └── hardware_page.html← 硬體總覽頁
```

### CSS 排版策略

```css
/* 兩欄封面 - 用 float 即可 */
.cover-left  { float: left; width: 48%; }
.cover-right { float: right; width: 48%; }

/* 規格表 - 原生 table，自動跨頁 */
table.spec-table { width: 100%; border-collapse: collapse; }

/* 自動分頁控制 */
.page-break { break-before: page; }
.keep-together { break-inside: avoid; }

/* WeasyPrint 分頁媒體 */
@page { size: letter; margin: 0.5in; }
```

## 四、版本管理系統

### 版本規則

| 情境 | 版本變化 | 範例 |
|------|---------|------|
| 首次生成 | v1.0 | → DS_ECW260_v1.0.pdf |
| 修改規格/圖片後重新生成 | minor +1 | v1.0 → v1.1 |
| 重大改版（手動指定） | major +1 | v1.5 → v2.0 |

### 版本記錄檔 `versions.json`

```json
{
  "ECW260": {
    "current_version": "1.1",
    "history": [
      {
        "version": "1.0",
        "date": "2026-03-20",
        "generated_by": "lulu",
        "changes": "Initial release",
        "file": "output/ECW260/DS_ECW260_v1.0.pdf"
      },
      {
        "version": "1.1",
        "date": "2026-03-25",
        "changes": "Updated antenna specs",
        "file": "output/ECW260/DS_ECW260_v1.1.pdf"
      }
    ]
  }
}
```

### 輸出資料夾結構

```
output/
├── ECW260/
│   ├── DS_ECW260_v1.0.pdf    ← 舊版保留不覆蓋
│   ├── DS_ECW260_v1.1.pdf    ← 最新版
│   └── DS_ECW260_v1.1.html   ← 保留 HTML 供除錯
├── ECW515/
│   └── ...
└── versions.json
```

## 五、Web 操作介面

### 主要頁面

**1. Dashboard（首頁）**
- 顯示所有產品線和型號
- 每個型號顯示：目前版本、最後更新日期、狀態（同步/有變更）
- 「全部重新整理」按鈕：從 Google Sheets 拉最新資料

**2. 單一產品頁**
- 預覽目前規格資料（從 Sheets 即時拉取）
- 預覽目前圖片（從 Drive 即時拉取）
- 「生成 PDF」按鈕
- 變更備注輸入框（記錄這次改了什麼）
- 歷史版本列表 + 下載連結

**3. 批次生成**
- 勾選多個產品，一次生成全部 PDF
- 適用於模板改版時全線重新生成

### 操作流程

```
同事修改 Google Sheet 規格
        ↓
打開 Web App → Dashboard
        ↓
看到該產品顯示「有變更」（對比上次快取）
        ↓
點進產品頁 → 確認資料正確
        ↓
填寫變更備注 → 點擊「生成 PDF」
        ↓
系統自動：拉資料 → 下載圖片 → 套模板 → 生成 PDF → 版本 +1
        ↓
PDF 可預覽 / 下載
```

## 六、你沒提到但應該納入的考量

### 1. 變更偵測
- 每次從 Google Sheets 拉取資料後，與上次快取的版本做 diff
- 在 Dashboard 標示哪些產品有規格變更、哪些圖片有更新
- 避免「不知道該重新生成哪些 PDF」的問題

### 2. PDF 內嵌版本資訊
- 每頁 footer 自動印上：`Version {x.y}  {日期}`（你現有模板已經有這個，例如 ESG610 的 `Version 1.5  07192024`）
- 確保列印出來的紙本也能辨識版本

### 3. 資料驗證與錯誤提示
- 用 Pydantic 驗證 Google Sheets 拉下來的資料
- 缺少必填欄位、圖片 ID 無效、格式錯誤 → 在介面上明確提示，不要生成有缺漏的 PDF

### 4. 圖片快取
- 從 Google Drive 下載的圖片快取在本地/伺服器
- 只在圖片有更新時重新下載，避免每次生成都等很久

### 5. PDF 存放位置
- Prototype 階段：存在本機 `output/` 資料夾
- 部署後：可存到 Google Drive 指定資料夾，方便團隊共用下載
- 或用 Vercel Blob Storage

### 6. 模板預覽
- 生成 PDF 前，先在瀏覽器預覽 HTML 版本
- 確認排版沒問題再正式生成，省去反覆生成的時間

## 七、開發階段規劃

### Phase 1：核心 Prototype（本機）
1. 建立 Google Sheet 規格表結構（先做一個產品線，例如 Outdoor AP）
2. 寫 Google Sheets CSV 讀取模組
3. 建立 HTML/CSS 模板（對照現有 PDF 刻出一樣的版面）
4. WeasyPrint PDF 生成
5. 版本管理系統
6. Flask Web 介面（選產品 → 預覽 → 生成）

### Phase 2：完整功能
7. 所有 5 個產品線的模板
8. Google Drive 圖片下載與快取
9. 變更偵測（diff）
10. 批次生成功能

### Phase 3：部署
11. 部署到 Vercel
12. 密碼保護（跟名片系統一樣）
13. PDF 輸出到 Google Drive（可選）

## 八、專案檔案結構

```
Datasheet-System/
├── app.py                    ← Flask 主程式
├── config.py                 ← Google Sheet ID、Drive 資料夾 ID 等設定
├── requirements.txt
├── vercel.json               ← 部署設定（Phase 3）
│
├── services/
│   ├── sheets_reader.py      ← Google Sheets CSV 讀取與解析
│   ├── drive_downloader.py   ← Google Drive 圖片下載與快取
│   ├── pdf_generator.py      ← WeasyPrint PDF 生成（可切換 Playwright）
│   └── version_manager.py    ← 版本管理邏輯
│
├── models/
│   ├── base.py               ← 共用欄位（product_name, category 等）
│   ├── ap.py                 ← AP 專用 Pydantic model
│   ├── switch.py
│   ├── camera.py
│   └── gateway.py
│
├── templates/
│   ├── web/                  ← Flask 網頁介面模板
│   │   ├── dashboard.html
│   │   └── product.html
│   ├── datasheet/            ← PDF 用的 HTML 模板
│   │   ├── base.html
│   │   ├── outdoor_ap.html
│   │   ├── indoor_ap.html
│   │   ├── switch.html
│   │   ├── camera.html
│   │   └── gateway.html
│   └── components/
│       ├── cover.html
│       ├── spec_table.html
│       ├── antenna.html
│       └── hardware.html
│
├── static/
│   ├── css/
│   ├── logo/
│   └── fonts/
│
├── cache/                    ← Google Drive 圖片快取
│   └── images/
│
├── output/                   ← 生成的 PDF（按型號分資料夾）
│   ├── ECW260/
│   ├── ECW515/
│   └── versions.json
│
└── Template PDF/             ← 你提供的原始模板（參考用）
```
