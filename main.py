import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (自動洗浄エンジン) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから情報を取得（辞書形式に変換）
    sa_info = dict(st.secrets["gcp_service_account"])
    
    # 【ここが特効薬】貼り付けミスによるゴミを強制的に掃除します
    raw_key = sa_info["private_key"]
    # 1. 実際の改行を「\n」という文字に変換してから、再度「本物の改行」に統一
    clean_key = raw_key.replace("\\n", "\n").replace("\n\n", "\n").strip()
    # 2. 鍵の前後にある不要な引用符や空白を完全除去
    clean_key = clean_key.strip("'").strip('"')
    sa_info["private_key"] = clean_key

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ スプレッドシートへの接続に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しました。理由：")
    st.warning(str(e))
    st.stop()

# --- 2. 実行ボタン表示 ---
all_data = list_ws.get_all_values()
if len(all_data) > 1:
    if st.button("🚀 凍結確認を開始"):
        rows = all_data[1:]
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, row in enumerate(rows):
            target_id = row[0]
            status_text.text(f"調査中: {target_id}")
            url = f"https://www.threads.net/@{target_id}"
            try:
                res = requests.get(url, timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "エラー"
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(rows))
            time.sleep(1)
        status_text.text("✅ 調査完了！")
        st.balloons()
else:
    st.info("調査リストにIDを入力してください。")
