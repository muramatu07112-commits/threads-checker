import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査サイト", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# 接続テスト
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    st.success("✅ スプレッドシートに無事つながりました！")
except Exception as e:
    st.error("❌ つながらない本当の理由が表示されました：")
    st.warning(str(e)) # ここに英語で理由が出ます
    st.stop()
