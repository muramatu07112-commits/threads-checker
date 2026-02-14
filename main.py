import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
import time

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (最もエラーが起きない直接指定方式) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから直接辞書として読み込みます（修復コードは不要になりました）
    sa_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    st.success("✅ Googleスプレッドシートへの接続に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しました。")
    st.warning(f"理由: {str(e)}")
    st.stop()

# --- 2. 調査実行セクション ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            # 残り時間の計算
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.5
            rem_sec = int((len(targets) - (i + 1)) * avg)
            m, s = divmod(rem_sec, 60)
            
            time_text.info(f"⏳ 予想残り時間: 約 {m}分 {s}秒")
            target_id = row[0]
            status_text.text(f"調査中: {target_id}")
            
            # 生存確認
            try:
                res = requests.get(f"https://www.threads.net/@{target_id}", timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "通信エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
            
        time_text.empty()
        status_text.success("✅ 調査が完了しました！シートを確認してください。")
        st.balloons()
else:
    st.info("スプレッドシートにIDを入力してください。")
