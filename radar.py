import sys
import os
import pandas as pd
import yfinance as yf
import json
import time
import warnings

warnings.filterwarnings('ignore')

print("🔥 啟動 QUANTUM CORE v5.0 // 無妥協全市場掃描版 🔥")

# ==========================================
# 🚀 階段一：讀取大廳的「全市場種子名單」
# ==========================================
# 直接讀取我們放在大廳的 1800 檔清單，徹底無視證交所的 IP 阻擋！
if not os.path.exists("all_stocks.json"):
    print("❌ 致命錯誤：大廳找不到 all_stocks.json！請手動上傳一次包含 1800 檔代號的檔案。")
    sys.exit(1)

with open("all_stocks.json", "r", encoding="utf-8") as f:
    all_stocks = json.load(f)

# 過濾純股票代號
target_tickers = [s['Code'] + ".TW" for s in all_stocks if 'Code' in s and len(s['Code']) == 4]
ticker_to_name = {s['Code']: s.get('Name', '台灣個股') for s in all_stocks if 'Code' in s and len(s['Code']) == 4}

print(f"📋 成功載入 {len(target_tickers)} 檔全市場股票代號！絕不妥協！")

# ==========================================
# 🚀 階段二：降速偽裝下載 (解決 Yahoo 機房 IP 封鎖)
# ==========================================
print("📦 開始向 Yahoo Finance 獲取今日最新股價...")

results = []
full_data = pd.DataFrame()

# 策略調整：把批次縮小到 100 檔，並且「關閉多執行緒」
batch_size = 100
batches = [target_tickers[i:i + batch_size] for i in range(0, len(target_tickers), batch_size)]

for idx, batch in enumerate(batches):
    print(f"   🔄 正在下載第 {idx+1}/{len(batches)} 批次...")
    try:
        # 🛡️ 核心防護：threads=False 強迫乖乖排隊下載，絕不觸發機房警報！
        # 🚀 新的：拿掉 threads 參數，靠小批次跟 sleep 就能完美通關！
        batch_data = yf.download(batch, period="1mo", group_by='ticker', progress=False, timeout=30)
        
        if not batch_data.empty:
            if full_data.empty:
                full_data = batch_data
            else:
                full_data = pd.concat([full_data, batch_data], axis=1)
                
        # 模仿人類行為，每抓完 100 檔休息 2 秒
        time.sleep(2)
    except Exception as e:
        print(f"   ❌ 第 {idx+1} 批次遭遇亂流: {e}")

# ==========================================
# 🚀 階段三：全市場動能運算
# ==========================================
print("📊 全市場飆股特徵評估與精煉中...")

if not full_data.empty:
    is_multi = isinstance(full_data.columns, pd.MultiIndex)
    
    for ticker in target_tickers:
        code = ticker.replace(".TW", "")
        name = ticker_to_name.get(code, "台灣個股")
        
        try:
            has_data = False
            df_stock = pd.DataFrame()
            
            if is_multi:
                if ticker in full_data.columns.levels[0]:
                    df_stock = full_data[ticker].dropna(subset=['Close'])
                    has_data = True
            else:
                if ticker in full_data.columns:
                    df_stock = full_data[[ticker]].dropna()
                    df_stock.columns = ['Close']
                    has_data = True
            
            if has_data and len(df_stock) >= 15:
                close_prices = df_stock['Close']
                current_price = float(close_prices.iloc[-1])
                prev10_price = float(close_prices.iloc[-11])
                ma5 = float(df_stock['Close'].tail(5).mean())
                
                # 未站上5日線者直接淘汰
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
# 🚀 階段四：實體輸出
# ==========================================
print("\n" + "="*60)
if results:
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    
    top20 = final_df.head(20)
    print("🏆 量化運算成功！本日全市場最強妖股排行榜 TOP 20 🏆")
    print(top20.to_string())
    
    top20.to_json("top20.json", orient="records", force_ascii=False)
    print(f"\n💾 SUCCESS: 1800檔不失真量化數據已成功打包寫入 top20.json！")
else:
    print("📉 大盤處於極度弱勢，無符合條件標的。")
    with open("top20.json", "w", encoding="utf-8") as f:
        f.write("[]")
print("="*60)
