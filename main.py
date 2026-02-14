import streamlit as st
import gspread
import json
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (究極の安定版) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから文字列としてJSONを読み込み、Python側で解凍します
    info_json = st.secrets["service_account_json"]
    sa_info = json.loads(info_json)
    
    # 秘密鍵の改行コードだけを念のため補正
    sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    st.success("✅ システム接続に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しています。")
    st.warning(f"理由: {str(e)}")
    st.stop()

# --- 2. 調査ボタン ---
if st.button("🚀 凍結確認を開始"):
    st.write("調査を開始します...")
