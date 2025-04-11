# Data Visualization Tool

使用 Python Dash 和 Dash Bootstrap Components 建構的多頁面資料視覺化應用程式。你可以上傳 CSV、Excel 或 JSON 檔案，並生成各種互動式（Plotly）和靜態（Seaborn/Matplotlib）圖表來探索資料，同時獲取程式碼，幫助你透過python學習程式語言。

## 主要功能

*   **資料上傳**: 支援 CSV、Excel (.xlsx, .xls) 和 JSON 檔案。
*   **資料預覽與總覽**: 提供資料表格預覽和各欄位的統計摘要（類型、缺失值、數值統計等）。
*   **日期格式轉換**: 將字串欄位轉換為日期時間格式，並自動提取年、月、星期等資訊。
*   **資料篩選**: 根據數值範圍、類別選擇或日期範圍篩選資料。
*   **圖表繪製**:
    *   **分布圖**: 直方圖、箱型圖、小提琴圖，可依類別分組。
    *   **關係圖**: 散佈圖，顯示兩個變數間的關係，可依類別分組並顯示趨勢線。
    *   **長條圖**: 顯示類別計數或數值變數的平均值，可分組或堆疊。
    *   **熱力圖**: 顯示數值變數間的相關係數矩陣，或兩個類別變數的交叉列表。
*   **動態與靜態圖表**: 提供 Plotly (動態) 和 Seaborn/Matplotlib (靜態) 兩種圖表選項。
*   **程式碼範例**: 自動生成繪製當前圖表的 Python 程式碼片段。
*   **Docker 支援**: 提供 Dockerfile，方便快速部署和分享。

## 專案結構

```
.
├── app.py              # Dash 應用程式主入口、佈局和路由
├── pages/              # 存放各個頁面模組 (.py)
│   ├── __init__.py
│   ├── data_upload.py
│   ├── distribution.py
│   ├── relationship.py
│   ├── bar_plot.py
│   └── heatmap.py
├── requirements.txt    # Python 依賴套件列表
├── Dockerfile          # 用於建構 Docker 映像的指令
├── .dockerignore       # 指定 Docker 建構時忽略的檔案
└── README.md           # 本說明文件
```

*   `app.py`: 初始化 Dash 應用，定義整體佈局（包含導覽列和頁面容器），並處理頁面路由。
*   `pages/`: 包含每個視覺化頁面的 Dash 佈局和回調邏輯。

## 安裝與使用

您可以選擇以下任一方式來執行此應用程式：

### 1. 本地執行 (Local Setup)

**前置需求**: 已安裝 Python 3.7+ 和 pip。

```bash
# 1.  複製 (Clone) 本專案
git clone <your-repository-url>
cd <repository-folder>

# 2. (建議) 建立並啟用虛擬環境
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 安裝依賴套件
pip install -r requirements.txt

# 4. 執行應用程式
python app.py

# 5. 在瀏覽器中開啟 http://127.0.0.1:8050/ 或 http://localhost:8050/
```

### 2. 使用 Docker 執行 (Simple Development Setup)

**前置需求**: 已安裝 Docker。

```bash
# 1. 克隆 (Clone) 此儲存庫 (如果尚未完成)
git clone <your-repository-url>
cd <repository-folder>

# 2. 建構 Docker 映像
#    (-t data-vis-tool 為映像命名，可自訂名稱)
docker build -t data-vis-tool .

# 3. 執行 Docker 容器
#    (-p 8050:8050 將本機的 8050 port 映射到容器的 8050 port)
docker run -p 8050:8050 data-vis-tool

# 4. 在瀏覽器中開啟 http://localhost:8050/
```

## 主要依賴套件

*   `dash`: 主要的 Web 應用框架。
*   `dash-bootstrap-components`: 提供 Bootstrap 樣式和元件。
*   `plotly`: 用於生成互動式圖表。
*   `pandas`: 用於資料處理和分析。
*   `numpy`: 基礎數值計算。
*   `matplotlib`: 用於生成靜態圖表。
*   `seaborn`: 基於 Matplotlib 的高階靜態圖表庫。
*   `openpyxl`: 讀取 Excel 檔案所需。

詳細列表請參見 `requirements.txt`。



Copyright (c) [2025] [Cheng-Lung Wang]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```