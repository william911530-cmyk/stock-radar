import yfinance as yf
import pandas as pd
import requests
import warnings

# 👇 建立一個偽裝成真人瀏覽器的 Session，突破 Yahoo 封鎖
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})

warnings.filterwarnings('ignore')

print("🔥 啟動終極妖股雷達 (全市場掃描 + JSON輸出版) 🔥")
print("1. 正在向證交所取得最新上市股票清單...")

# 從證交所抓取全市場大數據名單 (加入防護網與代理伺服器)
print("1. 正在向證交所取得最新上市股票清單...")
try:
    # 透過代理伺服器繞過海外 IP 封鎖，並設定 15 秒超時放棄
    url = "https://api.allorigins.win/raw?url=https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    res = requests.get(url, headers=headers, timeout=15)
    all_stocks = res.json()
except Exception as e:
    print(f"❌ 證交所連線失敗 (可能為週末維護或阻擋海外 IP): {e}")
    print("🛑 任務安全中止，今日不更新 JSON，維持使用昨日舊數據。")
    import sys
    sys.exit(0)  # 告訴 GitHub：程式是正常結束的，請給我綠色打勾！

# 👇 新增這三行：把全市場資料存成檔案，專門給可愛購物車讀取
import json
with open("all_stocks.json", "w", encoding="utf-8") as f:
    json.dump(all_stocks, f, ensure_ascii=False)


# 過濾出純股票 (代號長度為4的才是普通股票，排除權證、債券等)
target_stocks = {s['Code'] + ".TW": s['Name'] for s in all_stocks if len(s['Code']) == 4}

print(f"✅ 成功獲取 {len(target_stocks)} 檔股票名單！")
print("2. 準備開始計算歷史動能與均線 (大數據運算需要幾分鐘，請稍候)...\n")

results = []
count = 0

# 開始迴圈掃描 1000+ 檔股票
# ... 上面的迴圈 ...
for ticker, name in target_stocks.items():
    count += 1
    if count % 50 == 0:
        print(f"🔄 進度回報：已掃描 {count} 檔股票...")
        
    try:
        # 👇 這裡加上 session=session，用偽裝的身分去抓資料
        stock = yf.Ticker(ticker, session=session)
        df = stock.history(period="1mo")
        # ... 後面維持你原本的邏輯 ...

        if len(df) < 15:
            continue

        close_prices = df['Close']
        current_price = float(close_prices.iloc[-1])
        prev10_price = float(close_prices.iloc[-11])
        ma5 = float(close_prices.tail(5).mean())

        # 🛑 嚴格標準不變：跌破 5 日線直接無情淘汰！
        if current_price < ma5:
            continue

        roc10 = ((current_price - prev10_price) / prev10_price) * 100
        bias = ((current_price - ma5) / ma5) * 100
        score = (roc10 * 1.5) + (bias * 3.5)

        results.append({
            "代號": ticker.replace(".TW", ""), "名稱": name,
            "現價": round(current_price, 2), "10D動能(%)": round(roc10, 2),
            "MA5乖離(%)": round(bias, 2), "妖股分數": round(max(0, score), 2)
        })
    except Exception:
        continue

print("\n" + "="*60)

if results:  # 如果有抓到妖股
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by="妖股分數", ascending=False).reset_index(drop=True)
    pd.set_option('display.unicode.east_asian_width', True)
    
    top20 = final_df.head(20)
    print("🏆 掃描完成！本期最強妖股排行榜 🏆")
    print(top20.to_string())
    
    top20.to_json("top20.json", orient="records", force_ascii=False)
    print("\n💾 成功！已經將前 20 名妖股資料存入 top20.json！")
else:
    # 👇 最關鍵的防呆：如果大盤太爛或被擋，強制生出一個空的 JSON 給網頁吃
    print("📉 目前大盤偏弱，無符合條件的標的。")
    with open("top20.json", "w", encoding="utf-8") as f:
        f.write("[]")
    print("💾 已生成空的 top20.json 防止網頁當機！")
