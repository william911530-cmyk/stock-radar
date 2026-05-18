import sys
import os
import pandas as pd
import yfinance as yf
import json
import time
import warnings

warnings.filterwarnings('ignore')

print("🔥 啟動 QUANTUM CORE v7.0 // 全自動防呆・全域報錯版 🔥")

# ==========================================
# 🚀 階段一：獲取台股清單 (三重防護，保證不當機)
# ==========================================
all_stocks = []
print("📋 [1/3] 正在取得全市場股票名單...")

# 防護一：嘗試直接連線台灣證交所 (你在 VS Code 本地端執行時會走這條路)
try:
    import requests
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
        all_stocks = res.json()
        print(f"✅ 防護一成功：從證交所官方取得 {len(all_stocks)} 檔股票名單！")
        # 順手存一份 JSON，讓 GitHub 以後可以用
        with open("all_stocks.json", "w", encoding="utf-8") as f:
            json.dump(all_stocks, f, ensure_ascii=False)
except Exception as e:
    print(f"⚠️ 防護一失敗 (證交所連線異常): {e}")

# 防護二：讀取本地端的 all_stocks.json (當在 GitHub 雲端被擋時，會走這條路)
if not all_stocks:
    if os.path.exists("all_stocks.json"):
        try:
            with open("all_stocks.json", "r", encoding="utf-8") as f:
                all_stocks = json.load(f)
            print(f"✅ 防護二成功：從大廳歷史檔案讀取 {len(all_stocks)} 檔股票名單！")
        except Exception as e:
            print(f"⚠️ 防護二失敗 (讀取 JSON 異常): {e}")
    else:
        print("⚠️ 防護二失敗：找不到 all_stocks.json 備用檔案。")

# 防護三：終極硬體備援 (如果前兩招都失敗，強制載入內建清單)
if not all_stocks:
    print("🚨 啟動防護三：使用內建核心飆股名單 (確保程式絕對不會死)！")
    all_stocks = [{"Code": "2330", "Name": "台積電"}, {"Code": "2317", "Name": "鴻海"}, {"Code": "2454", "Name": "聯發科"}, {"Code": "3008", "Name": "大立光"}, {"Code": "2382", "Name": "廣達"}]

# 過濾出純股票 (4碼)
target_tickers = [s['Code'] + ".TW" for s in all_stocks if 'Code' in s and len(s['Code']) == 4]
ticker_to_name = {s['Code']: s.get('Name', '未知') for s in all_stocks if 'Code' in s and len(s['Code']) == 4}

print(f"🎯 最終確認：即將掃描 {len(target_tickers)} 檔股票。")

# ==========================================
# 🚀 階段二：逐檔掃描與【錯誤回報系統】
# ==========================================
print("📦 [2/3] 開始向 Yahoo Finance 獲取股價 (單檔穩健模式，預估耗時 5~10 分鐘)...")

results = []
error_log = [] # 準備一本小本子，記錄所有錯誤

for i, ticker in enumerate(target_tickers):
    code = ticker.replace(".TW", "")
    name = ticker_to_name.get(code, "未知")
    
    # 每 100 檔回報一次進度
    if (i + 1) % 100 == 0:
        print(f"   🔄 進度回報：已掃描 {i + 1} / {len(target_tickers)} 檔...")
        
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if df.empty or len(df) < 15:
            error_log.append(f"[{code} {name}] 無法取得足夠 K 線資料 (可能下市或剛上市)")
            continue
            
        current_price = float(df['Close'].iloc[-1])
        prev10_price = float(df['Close'].iloc[-11])
        ma5 = float(df['Close'].tail(5).mean())
        
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
        
    except Exception as e:
        # 如果發生任何不可預期的錯誤，寫進筆記本，然後繼續跑下一檔！絕不當機！
        error_log.append(f"[{code} {name}] 發生錯誤: {str(e)}")
        continue

# ==========================================
# 🚀 階段三：實體輸出與報告
# ==========================================
print("\n" + "="*60)
print(f"⚠️ 掃描完畢！共有 {len(error_log)} 檔股票遭遇抓取問題 (已被系統安全過濾)。")

# 印出前 5 筆錯誤讓主人過目
if error_log:
    print("🔍 錯誤筆記本 (前 5 筆範例):")
    for err in error_log[:5]:
        print(f"   - {err}")
print("="*60)

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
