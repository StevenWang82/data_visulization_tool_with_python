import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

from pages import data_upload, distribution, relationship, bar_plot, heatmap # 匯入所有頁面模組

# 使用 LUX Bootstrap 主題初始化 Dash 應用程式
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.LUX])
server = app.server # 為了部署，公開 server 變數

# 使用 dbc.NavbarSimple 建立更現代化的導覽列
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink('資料上傳', href='/', active="exact")),
        dbc.NavItem(dbc.NavLink('分布圖', href='/distribution', active="exact")),
        dbc.NavItem(dbc.NavLink('關聯分析', href='/relationship', active="exact")),
        dbc.NavItem(dbc.NavLink('長條圖', href='/bar', active="exact")),
        dbc.NavItem(dbc.NavLink('熱力圖', href='/heatmap', active="exact")),
    ],
    brand="資料視覺化工具", # 在導覽列中加入品牌名稱
    brand_href="/",
    color="primary", # 設定導覽列顏色
    dark=True, # 使用深色主題文字
    sticky="top", # 將導覽列固定在頂部
    className="mb-4", # 新增底部邊距
)

# 使用函式和 Bootstrap 容器定義主應用程式佈局
def serve_layout():
    return html.Div([ # 使用 html.Div 作為最外層容器
        dcc.Location(id='url', refresh=False), # 用於追蹤 URL 變化的元件
        dcc.Store(id='stored-data'), # 用於跨頁面儲存資料的 Store 元件
        navbar, # 將導覽列放在頂部
        dbc.Container([ # 使用標準容器來容納頁面內容，提供左右邊距
            html.Div(id='page-content', className="mt-4") # 內容將根據 URL 載入此處，並增加頂部邊距
        ], fluid=False) # 使用非流體容器，讓內容居中顯示
    ])

app.layout = serve_layout # 指派佈局函式

# 在應用程式初始化後，僅註冊一次來自 data_upload 頁面的回調函式
# 這假設 data_upload.py 有一個 register_callbacks(app) 函式
# 確保 data_upload.py 不在頂層直接匯入 'app'
# 以免造成循環匯入。如果發生這種情況，您可能需要不同的模式
# 從匯入的頁面模組註冊回調函式
# 此模式假設每個頁面模組都有一個 'register_callbacks(app)' 函式
# 如果它定義了需要 app 實例的回調函式。
# 如果頁面只有佈局而沒有需要 'app' 的回調函式，則不需要此步驟。

for page_module in [data_upload, distribution, relationship, bar_plot, heatmap]: # 註冊所有匯入的模組
    try:
        page_module.register_callbacks(app)
        print(f"Successfully registered callbacks from {page_module.__name__}.")
    except AttributeError:
        print(f"Warning: 'register_callbacks' function not found in {page_module.__name__}.")
    except Exception as e:
        print(f"Error registering callbacks for {page_module.__name__}: {e}")


# 根據 URL 渲染頁面內容的回調函式
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # 從預先匯入的模組根據路徑名稱傳回佈局
    if pathname == '/distribution':
        return distribution.layout
    elif pathname == '/relationship':
        return relationship.layout
    elif pathname == '/bar':
        return bar_plot.layout
    elif pathname == '/heatmap':
        return heatmap.layout
    elif pathname == '/' or pathname == '/data_upload': # 處理根路徑和明確路徑
        return data_upload.layout
    else:
        return html.Div("404 Page not found")


if __name__ == '__main__':
    # 注意：在生產環境中 debug=True 應設為 False
    app.run(debug=True)
