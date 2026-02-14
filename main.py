import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査プロキシ版", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（自動洗浄機能） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sa_info = dict(st.secrets["gcp_service_account"])
    key = sa_info["private_key"].replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    key = "".join(key.split())
    sa_info["private_key"] = "-----BEGIN PRIVATE KEY-----\n" + key + "\n-----END PRIVATE KEY-----\n"

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ システム接続完了")
except Exception as e:
    st.error(f"❌ 接続エラー: {str(e)}")
    st.stop()

# --- 2. データ準備 ---
all_rows = list_ws.get_all_values()
proxy_list = [r[0] for r in proxy_ws.get_all_values()[1:] if r]

if len(all_rows) > 1:
    targets = all_rows[1:]
    total_count = len(targets)
    
    st.sidebar.header("📊 調査ステータス")
    st.sidebar.write(f"調査対象: {total_count} 件")
    st.sidebar.write(f"プロキシ: {len(proxy_list)} 件")

    if st.button("🚀 調査を開始（残り時間表示付き）"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty() # 残り時間表示用の枠
        
        start_time = time.time() # 修正：開始時刻を記録
        
        for i, row in enumerate(targets):
            target_id = row[0]
            
            # 【残り時間の計算】
            elapsed_time = time.time() - start_time
            avg_time_per_item = elapsed_time / (i + 1) if i > 0 else 1.5 # 1件あたりの平均時間
            remaining_items = total_count - (i + 1)
            remaining_seconds = int(remaining_items * avg_time_per_item)
            
            # 分：秒に変換して表示
            mins, secs = divmod(remaining_seconds, 60)
            time_text.info(f"⏳ 予想残り時間: 約 {mins}分 {secs}秒")
            status_text.text(f"調査中 ({i+1}/{total_count}): {target_id}")
            
            # --- プロキシ設定 & リンク確認実行 ---
            proxy_config = None
            if proxy_list:
                p = proxy_list[i % len(proxy_list)]
                proxy_config = {"http": f"http://{p}", "https": f"http://{p}"}
            
            url = f"https://www.threads.net/@{target_id}"
            try:
                # リンクへアクセスして200系なら生存と判断
                res = requests.get(url, proxies=proxy_config, timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "通信エラー"
            
            # スプレッドシート更新
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / total_count)
            time.sleep(1) # ブロック回避のための待機
            
        time_text.empty()
        status_text.success(f"✅ 全 {total_count} 件の調査が完了しました！")
        st.balloons()
else:
    st.info("スプレッドシートに調査対象のIDを入力してください。")
