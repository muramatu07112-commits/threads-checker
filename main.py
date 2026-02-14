import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査サイト", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (最も壊れにくい直接読み込み形式) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # 秘密（Secrets）の情報をそのままGoogleに渡します
    sa_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ スプレッドシートとの連携に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しています。")
    st.warning(f"理由: {str(e)}")
    st.stop()

# --- 2. データ読み込み ---
all_data = list_ws.get_all_values()
if len(all_data) > 1:
    rows = all_data[1:]
    proxies = [row[0] for row in proxy_ws.get_all_values()[1:] if row]

    st.sidebar.header("📊 現在の状況")
    st.sidebar.write(f"調査対象: {len(rows)} 件")

    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        for i, row in enumerate(rows):
            target_id = row[0]
            url = f"https://www.threads.net/@{target_id}"
            try:
                res = requests.get(url, timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(rows))
            time.sleep(1)
            
        st.success("✅ 全ての調査が完了しました！")
        st.balloons()
else:
    st.info("調査リストにIDを入力してください。")
