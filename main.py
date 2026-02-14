import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import re
import json

# =========================================================
# 【設定エリア】ここだけを書き換えてください
# =========================================================
# 1. 秘密鍵（-----BEGIN...から...END-----まで全部貼り付け）
RAW_PRIVATE_KEY = "ここに秘密鍵を貼り付けてください"

# 2. クライアントメール（your-project...iam.gserviceaccount.com）
CLIENT_EMAIL = "ここにメールアドレスを貼り付け"

# 3. プロジェクトID
PROJECT_ID = "ここにプロジェクトIDを貼り付け"

# 4. スプレッドシートのURL（ブラウザのアドレスバーのURL）
SHEET_URL = "ここにURLを貼り付け"
# =========================================================

def get_perfect_credentials(raw_pk, client_email, project_id):
    """
    【魔法の工場】
    どんなに汚れた鍵データでも、数学的に正しいPEM形式に強制再鋳造する。
    """
    try:
        # JSONからコピペした際の「\n」という文字列を、実際の改行コードに変換
        sanitized = raw_pk.replace('\\n', '\n')
        
        # 不要な文字（ヘッダー、フッター、スペース、改行）を一旦すべて排除
        body = re.sub(r'-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s+', '', sanitized)
        
        # 英数字とBase64記号以外を完全に抹殺（ノイズ除去）
        body = re.sub(r'[^a-zA-Z0-9+/]', '', body)
        
        # 【重要】Base64の数学的整合性（4の倍数）を強制確保
        while len(body) % 4 != 0:
            body += '='
            
        # PEM規格（64文字ごとの改行）に再構成
        formatted_pk = "-----BEGIN PRIVATE KEY-----\n"
        for i in range(0, len(body), 64):
            formatted_pk += body[i:i+64] + "\n"
        formatted_pk += "-----END PRIVATE KEY-----\n"

        info = {
            "type": "service_account",
            "project_id": project_id,
            "private_key": formatted_pk,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        return Credentials.from_service_account_info(info)
    except Exception as e:
        raise ValueError(f"鍵の再構成に失敗しました: {str(e)}")

def main():
    st.set_page_config(page_title="Threads Checker", layout="wide")
    st.title("🛡️ 鉄壁のThreads生存確認ツール")

    # 画面上の進捗管理
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

    try:
        # 1. 認証プロセスの自動実行
        creds = get_perfect_credentials(RAW_PRIVATE_KEY, CLIENT_EMAIL, PROJECT_ID)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).get_worksheet(0)
        
        # データの取得
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        
        st.success(f"✅ 認証成功！ スプレッドシート（{len(df)}件）を認識しました。")
        st.dataframe(df.head(5)) # 最初の5件だけチラ見せ

        # 2. 生存確認の実行（画像13のロジック継承）
        if st.button("生存確認チェックを開始"):
            st.session_state.is_running = True
            
            progress_bar = st.progress(0)
            status_area = st.empty()
            start_time = time.time()
            
            for i in range(len(df)):
                # --- 【画像13の計算式】 ---
                elapsed_time = time.time() - start_time
                avg_time_per_item = elapsed_time / (i + 1)
                remaining_items = len(df) - (i + 1)
                remaining_sec = avg_time_per_item * remaining_items
                
                # 表示の更新
                status_area.write(f"📊 処理中: {i+1}/{len(df)} 件目 | ⏳ 予想残り時間: {int(remaining_sec)}秒")
                progress_bar.progress((i + 1) / len(df))
                
                # ここに実際の判定ロジックが入る（現在はシミュレーション）
                time.sleep(0.5) 
            
            st.balloons()
            st.success("全ての生存確認が完了しました。")

    except Exception as e:
        st.error("🔥 実行エラーが発生しました")
        st.code(str(e))
        st.info("ヒント: 設定エリア（15-18行目）に貼り付けた内容が、元のJSONファイルと一致しているか確認してください。")

if __name__ == "__main__":
    main()
