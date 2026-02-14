import streamlit as st
import gspread
import requests
import time
import re
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（徹底洗浄ロジック） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから読み込み
    if "pk_base64" in st.secrets:
        raw_key = st.secrets["pk_base64"]
    else:
        # キー名が違う場合の保険
        raw_key = str(st.secrets)

    # 【重要】英数字、プラス、スラッシュ、イコール以外を「完全に削除」します
    # これにより、コピペで混入したスペース、改行、バックスラッシュを全て消し去ります
    clean_key = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_key)
    
    # Googleが受け付けるPEM形式に再構成
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_key), 64):
        formatted_key += clean_key[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"
    
    sa_info = {
        "type": "service_account",
        "project_id": "threads-checker",
        "private_key_id": "feedba476b9bcad61b66b93e91aaab7c871f2d52",
        "private_key": formatted_key,
        "client_email": "checker-bot@threads-checker.iam.gserviceaccount.com",
        "client_id": "102355019665572843670",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/checker-bot%40threads-checker.iam.gserviceaccount.com"
    }

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    st.success("✅ スプレッドシート接続成功！")

except Exception as e:
    st.error(f"❌ 接続エラー: {e}")
    st.stop()

# --- 2. 調査ロジック（画像13の処理を包含） ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        start_time = time.time()
        for i, row in enumerate(targets):
            # 画像13の計算ロジック
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.2
            rem = int((len(targets) - (i + 1)) * avg)
            st.info(f"⏳ 予想残り時間: 約 {rem // 60}分 {rem % 60}秒")
            
            target_id = row[0]
            try:
                # 簡易チェック
                res = requests.get(f"https://www.threads.net/@{target_id}", timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
        st.success("完了！")
