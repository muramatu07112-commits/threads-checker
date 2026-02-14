import streamlit as st
import sys

# =========================================================
# 0. 最優先：グローバル・エラー・キャッチャー
# =========================================================
# UIが描画される前に死ぬのを防ぐため、最上段に配置
try:
    import gspread
    import pandas as pd
    import re
    import time
    from google.oauth2.service_account import Credentials
except Exception as e:
    st.error(f"❌ ライブラリのインポート段階で失敗: {str(e)}")
    st.stop()

def get_ultra_sanitized_credentials(raw_pk, client_email, project_id):
    # 前回の洗浄ロジック（ここでのエラーも捕捉対象）
    clean_pk = re.sub(r'[^a-zA-Z0-9+/]', '', raw_pk)
    while len(clean_pk) % 4 != 0:
        clean_pk += '='
    
    formatted_pk = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_pk), 64):
        formatted_pk += clean_pk[i:i+64] + "\n"
    formatted_pk += "-----END PRIVATE KEY-----\n"

    info = {
        "type": "service_account",
        "project_id": project_id,
        "private_key": formatted_pk.replace('\\n', '\n'),
        "client_email": client_email,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return Credentials.from_service_account_info(info)

# =========================================================
# 1. ブートストラップ・モニタリング
# =========================================================
def main():
    # 画面が真っ白になるのを防ぐため、即座にタイトルを描画
    st.title("🛡️ Debug Mode: Threads Survival Checker")
    st.write("システム起動中... (この画面が見えていれば基本構造は正常です)")

    # 設定データ（ここにあなたの情報を入力）
    # ※前回の「ASN.1 parsing error」を防ぐため、JSONの private_key 全体をコピペしてください
    RAW_PRIVATE_KEY = "ここに秘密鍵を貼り付け" 
    CLIENT_EMAIL = "your-email"
    PROJECT_ID = "your-id"
    SHEET_URL = "your-url"

    # --- 認証プロセス（ここが白画面の主犯候補） ---
    try:
        st.write("⏳ Step 1: 鍵の洗浄と認証を開始...")
        creds = get_ultra_sanitized_credentials(RAW_PRIVATE_KEY, CLIENT_EMAIL, PROJECT_ID)
        
        st.write("⏳ Step 2: Google Sheets 接続開始...")
        client = gspread.authorize(creds)
        
        st.write("⏳ Step 3: スプレッドシート取得...")
        sheet = client.open_by_url(SHEET_URL).get_worksheet(0)
        
        data = sheet.get_all_records()
        st.success("✅ 全プロセス正常完了。スプレッドシートの読み込みに成功しました。")
        st.write(f"取得データ件数: {len(data)}件")
        
        # プレビュー表示
        if data:
            st.dataframe(pd.DataFrame(data).head())

    except Exception as e:
        # すべてのエラーを画面に強制出力
        st.error(f"⚠️ 実行エラー発生: {type(e).__name__}")
        st.code(str(e))
        st.info("これが表示される場合、認証情報またはネットワークに問題があります。")

# 実行
if __name__ == "__main__":
    try:
        main()
    except Exception as fatal_e:
        st.error(f"🔥 致命的なメインループエラー: {str(fatal_e)}")
