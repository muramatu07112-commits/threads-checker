import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (自動修復エンジン搭載) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから情報を取得
    sa_info = dict(st.secrets["gcp_service_account"])
    
    # 【重要】貼り付けミスによる「見えないゴミ」をここで強制排除します
    fixed_key = sa_info["private_key"].replace("\\n", "\n").strip()
    if not fixed_key.endswith("\n"):
        fixed_key += "\n"
    sa_info["private_key"] = fixed_key

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ スプレッドシートへの接続に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しました。理由を以下に表示します：")
    st.warning(str(e))
    st.stop()

# --- 2. 実行ボタン表示 ---
all_data = list_ws.get_all_values()
if len(all_data) > 1:
    if st.button("🚀 凍結確認を開始"):
        # 調査処理（以下略）
        st.write("調査を開始しました...")
