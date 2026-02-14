import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査サイト", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ スプレッドシートとの連携に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しています。Secretsの設定を確認してください。")
    st.warning(str(e))
    st.stop()

# --- 2. データ読み込み ---
all_data = list_ws.get_all_values()
if len(all_data) > 1:
    rows = all_data[1:] # 2行目以降のデータ
    proxies = [row[0] for row in proxy_ws.get_all_values()[1:] if row]

    st.sidebar.header("📊 現在の状況")
    st.sidebar.write(f"調査対象: {len(rows)} 件")
    st.sidebar.write(f"利用可能プロキシ: {len(proxies)} 件")

    # --- 3. 実行ボタン ---
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, row in enumerate(rows):
            target_id = row[0]
            row_num = i + 2
            status_text.text(f"調査中 ({i+1}/{len(rows)}): {target_id}")
            
            # ThreadsのURLをチェック
            url = f"https://www.threads.net/@{target_id}"
            try:
                # プロキシの設定（ある場合のみ）
                proxy_config = None
                if proxies:
                    p = proxies[i % len(proxies)]
                    proxy_config = {"http": f"http://{p}", "https": f"http://{p}"}
                
                res = requests.get(url, proxies=proxy_config, timeout=10)
                
                if res.status_code == 200:
                    result = "生存"
                elif res.status_code == 404:
                    result = "凍結/削除"
                else:
                    result = f"エラー({res.status_code})"
            except:
                result = "通信エラー"
            
            # シートに結果を書き込む
            list_ws.update_cell(row_num, 2, result)
            progress_bar.progress((i + 1) / len(rows))
            time.sleep(1) # 負荷をかけないための待機
            
        status_text.text("✅ 全ての調査が完了しました！シートを確認してください。")
        st.balloons()
else:
    st.info("スプレッドシートに調査対象のIDを入力してください。")
