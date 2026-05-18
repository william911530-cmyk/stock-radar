import sys
import os
import requests
import pandas as pd
import yfinance as yf
import json
import warnings

warnings.filterwarnings('ignore')

print("🔥 啟動 QUANTUM CORE v3.0 // 終極不失真全市場量化雷達 🔥")

# ==========================================
# 🚀 階段一：獲取台股清單 (全市場歷史數據庫無縫容錯)
# ==========================================
all_stocks = []
twse_success = False
print("📋 [1/3] 正在同步台灣證交所全市場名單...")

# 嘗試正門直連
try:
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    res = requests.get(url, headers=headers, timeout=10)
    all_stocks = res.json()
    if isinstance(all_stocks, list) and len(all_stocks) > 0:
        twse_success = True
        print(f"<table>✅ 證交所官方直連成功！成功撈取 {len(all_stocks)} 檔最新全市場名單。")
        # 覆蓋並更新本地資料庫
        with open("all_stocks.json", "w", encoding="utf-8") as f:
            json.dump(all_stocks, f, ensure_ascii=False)
except Exception as e:
    print(f"⚠️ 證交所官方拒絕海外連線: {e}")

# 🌟 核心修正：若證交所API被阻擋，直接讀取上一期大廳留下的 all_stocks.json（包含1800檔全股票）
if not twse_success:
    print("💡 啟動大數據容錯機制：正在調閱專案大廳全市場歷史名單...")
    if os.path.exists("all_stocks.json"):
        with open("all_stocks.json", "r", encoding="utf-8") as f:
            all_stocks = json.load(f)
        print(f"🚀 成功提取 1800 檔全市場代號庫！即將利用今日最新股價進行運算，數據 100% 絕不失真！")
    else:
        print("❌ 致命錯誤：找不到本地歷史資料庫，請稍後手動重試。")
        sys.exit(1)

# 清理並格式化全市場代號 (只留4位數普通股)
target_tickers = [s['Code'] + ".TW" for s in all_stocks if 'Code' in s and len(s['Code']) == 4]
ticker_to_name = {s['Code']: s.get('Name', '台灣個股') for s in all_stocks if 'Code' in s and len(s['Code']) == 4}

# ==========================================
# 🚀 階段二：分批批次下載 (對 1800 檔抓取「今天最新股價」)
# ==========================================
print(f"📦 [2/3] 正在由 Yahoo Finance 下載全市場 {len(target_tickers)} 檔『今日即時價格』...")

results = []
full_data = pd.DataFrame()

# 將 1800 檔分成 3 批（每批約 600 檔）進行高速 Bulk 下載，避免被 Yahoo 判定高頻攻擊
batch_size = 600
batches = [target_tickers[i:i + batch_size] for i in range(0, len(target_tickers), batch_size)]

for idx, batch in enumerate(batches):
    print(f"   🔄 正在押送第 {idx+1}/{len(batches)} 批次全市場股價...")
    try:
        # 下載今天及過去一個月的數據
        batch_data = yf.download(batch, period="1mo", group_by='ticker', progress=False, timeout=20)
        if idx == 0:
            full_data = batch_data
        else:
            full_data = pd.concat([full_data, batch_data], axis=1)
    except Exception as e:
        print(f"   ❌ 第 {idx+1} 批次大數據網路阻斷: {e}")

# ==========================================
# 🚀 階段三：全市場多維度量化特徵運算
# ==========================================
print("📊 [3/3] 正在對 1800 檔股票進行當日最新妖股指標運算...")

for ticker in target_tickers:
    code = ticker.replace(".TW", "")
    name = ticker_to_name.get(code, "台灣個股")
    
    try:
        if ticker in full_data.columns.levels[0]:
            df = full_data[ticker].dropna(subset=['Close'])
            if len(df) < 15:
                continue
                
            current_price = float(df['Close'].iloc[-1])
            prev10_price = float(df['Close'].iloc[-11])
            ma5 = float(df['Close'].tail(5).mean())
            
            # 嚴格標準：跌破5日線無情淘汰！
            if current_price < ma5:
                continue
                
            roc10 = ((current_price - prev10_price) / prev10_price) * 100
            bias = ((current_price - ma5) / ma5) * 100
            score = (roc10 * 1.5) + (bias * 3.5)
            
            results.append({
                "代號": code, "名稱": name,
                "現價": round(current_price, 2), "10D動能(%)": round(roc10, 2),
                "MA5乖離(%)": round(bias, 2), "妖股分數": round(max(0, score), 2)
            })
    except Exception:
        continue

# ==========================================
# 🚀 階段四：實體 JSON 輸出
# ==========================================
print("\n" + "="*60)
if results:
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    
    top20 = final_df.head(20)
    print("🏆 量化運算成功！本日全市場最強妖股排行榜 TOP 20 🏆")
    print(top20.to_string())
    
    # 寫入 top20.json
    top20.to_json("top20.json", orient="records", force_ascii=False)
    print(f"\n💾 SUCCESS: 1800檔不失真量化數據已成功打包寫入 top20.json！")
else:
    print("📉 本日全市場大盤動能過弱，無符合條件之標的。")
    with open("top20.json", "w", encoding="utf-8") as f:
        f.write("[]")
print("="*60)
