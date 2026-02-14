import streamlit as st
import gspread
import requests
import time
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（JSON丸ごと読み込み版） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    if "json_text" not in st.secrets:
        st.error("設定エラー: Secretsに 'json_text' が見つかりません。")
        st.stop()
    
    # 文字列として保存されたJSONを解析
    sa_info = json.loads(st.secrets["json_text"])

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    
    st.success("✅ スプレッドシートへの接続に成功しました！10時間の戦い、お疲れ様でした。")

except Exception as e:
    st.error(f"❌ 接続エラー: {e}")
    st.info("※もしエラーが消えない場合、JSONのコピペが欠けていないか、スプレッドシートが checker-bot@... に共有されているか確認してください。")
    st.stop()

# --- 2. 調査実行セクション（変更なし） ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.2
            rem = int((len(targets) - (i + 1)) * avg)
            time_text.info(f"⏳ 予想残り時間: 約 {rem // 60}分 {rem % 60}秒")
            
            target_id = row[0]
            try:
                res = requests.get(f"https://www.threads.net/@{target_id}", timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
            
        time_text.empty()
        st.success("✅ 調査が完了しました！")
        st.balloons()
