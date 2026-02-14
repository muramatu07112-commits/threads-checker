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
    
    # 【ここが解決のポイント】貼り付け時に混ざる「見えないゴミ」を自動で掃除します
    sa_info = dict(st.secrets["gcp_service_account"])
    # 文字としての \n を、本物の改行に変換し、余計な空白も削除します
    sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n").strip()
    
    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ スプレッドシートとの連携に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しています。")
    st.warning(f"エラー内容: {str(e)}")
    st.stop()

# --- 2. データ読み込みと実行ボタン ---
all_data = list_ws.get_all_values()
if len(all_data) > 1:
    rows = all_data[1:]
    proxies = [row[0] for row in proxy_ws.get_all_values()[1:] if row]
    if st.button("🚀 凍結確認を開始"):
        # 調査ロジック（以下略）
        st.write("調査を開始しました...")
else:
    st.info("スプレッドシートにIDを入力してください。")
