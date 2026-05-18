import sys
import os
import pandas as pd
import yfinance as yf
import json
import warnings

warnings.filterwarnings('ignore')

print("🔥 啟動 QUANTUM CORE v6.0 // 返璞歸真・絕對穩定版 🔥")

# ==========================================
# 1. 讀取你放在大廳的 1800 檔名單
# ==========================================
if not os.path.exists("all_stocks.json"):
    print("❌ 致命錯誤：找不到 all_stocks.json，請確認已上傳。")
    sys.exit(1)

with open("all_stocks.json", "r", encoding="utf-8") as f:
    all_stocks = json.load(f)

target_tickers = [s['Code'] + ".TW" for s in all_stocks if 'Code' in s and len(s['Code']) == 4]
ticker_to_name = {s['Code']: s.get('Name', '台灣個股') for s in all_stocks if 'Code' in s and len(s['Code']) == 4}

print(f"📋 成功載入 {len(target_tickers)} 檔全市場股票代號。")

# ==========================================
# 2. 最傳統、最穩定的單檔迴圈抓取 (不用 download，不怕 bug)
# ==========================================
print("📦 開始逐檔向 Yahoo Finance 獲取股價 (預估耗時 5~10 分鐘，請耐心等候)...")

results = []
count = 0

for ticker in target_tickers:
    code = ticker.replace(".TW", "")
    name = ticker_to_name.get(code, "台灣個股")
    count += 1
    
    # 每 100 檔回報一次進度，讓你知道程式還活著
    if count % 100 == 0:
        print(f"   🔄 進度回報：已穩健掃描 {count} / {len(target_tickers)} 檔...")
        
    try:
        # 🌟 核心關鍵：回歸最原始的 Ticker 寫法，跟你其他正常的程式一樣！
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if df.empty or len(df) < 15:
            continue
            
        current_price = float(df['Close'].iloc[-1])
        prev10_price = float(df['Close'].iloc[-11])
        ma5 = float(df['Close'].tail(5).mean())
        
        # 未站上5日線者淘汰
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
        # 如果單一股票發生錯誤（如下市或查無資料），直接安靜跳過
        continue

# ==========================================
# 3. 實體輸出
# ==========================================
print("\n" + "="*60)
if results:
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    
    top20 = final_df.head(20)
    print("🏆 量化運算成功！本日全市場最強妖股排行榜 TOP 20 🏆")
    print(top20.to_string())
    
    top20.to_json("top20.json", orient="records", force_ascii=False)
    print(f"\n💾 SUCCESS: 資料已成功寫入 top20.json！")
else:
    print("📉 大盤弱勢，無符合標的。")
    with open("top20.json", "w", encoding="utf-8") as f:
        f.write("[]")
print("="*60)
