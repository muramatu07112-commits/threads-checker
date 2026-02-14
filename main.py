import streamlit as st
import gspread
import requests
import time
import re
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (外科手術式・自動修復) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sa_info = dict(st.secrets["gcp_service_account"])
    
    # 【ここが重要】鍵を一度完全にバラバラにし、英数字だけを抽出して1から作り直します
    raw_key = sa_info["private_key"]
    # 1. 鍵のヘッダー/フッター以外の「中身の英数字」だけを抜き取る
    core_content = "".join(re.findall(r'[a-zA-Z0-9+/=]', raw_key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")))
    # 2. Googleが100%受理する形式に再構成する
    sa_info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{core_content}\n-----END PRIVATE KEY-----\n"

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    st.success("✅ ついに成功しました！Googleに接続完了です。")
except Exception as e:
    st.error("❌ 接続エラーが発生しました。理由：")
    st.warning(str(e))
    st.stop()

# --- 2. 実行ボタン表示 ---
if st.button("🚀 凍結確認を開始"):
    all_data = list_ws.get_all_values()
    if len(all_data) > 1:
        targets = all_data[1:]
        progress_bar = st.progress(0)
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            # 残り時間の計算
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.2
            rem = int((len(targets) - (i + 1)) * avg)
            time_text.info(f"⏳ 予想残り時間: 約 {rem // 60}分 {rem % 60}秒")
            
            # 生存確認実行
            try:
                res = requests.get(f"https://www.threads.net/@{row[0]}", timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
            
        time_text.empty()
        st.success("✅ 調査完了！シートを確認してください。")
        st.balloons()
