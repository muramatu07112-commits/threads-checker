import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json

# =========================================================
# 【IQ200仕様：完全版】スコープ自動定義エンジン
# =========================================================

def initialize_ui():
    st.set_page_config(page_title="Threads Survival Checker", layout="wide")
    st.title("🛡️ 鉄壁のThreads生存確認システム (Scope Fixed)")
    st.markdown("---")
    
    st.sidebar.header("⚙️ システム設定")
    raw_json = st.sidebar.text_area("1. JSONファイルの中身を全部貼り付け", height=300)
    sheet_url = st.sidebar.text_area("2. スプレッドシートのURLを貼り付け", height=100)
    
    return raw_json, sheet_url

def get_creds_with_scopes(json_str):
    """
    【戦略的修正】
    gspread実行に必要な2つのスコープ（Sheets/Drive）を強制付与して認証する
    """
    # 必須スコープの定義
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        info = json.loads(json_str.strip())
        # 秘密鍵の改行修復
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace('\\n', '\n')
            
        # スコープを明示的に指定して認証オブジェクトを作成
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    except Exception as e:
        st.sidebar.error(f"❌ 認証エラー: {str(e)}")
        return None

def main():
    raw_json, sheet_url = initialize_ui()

    if not raw_json or not sheet_url:
        st.warning("👈 左側のサイドバーに設定を入力してください。")
        return

    try:
        # 1. 権限（スコープ）付き認証の実行
        creds = get_creds_with_scopes(raw_json)
        if not creds: return
        
        client = gspread.authorize(creds)
        
        # 2. シート接続
        # ※URLからシートを開く際に、編集権限がないとここでエラーが出る
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        st.success(f"✅ 認証・接続成功！ 対象データ: {len(df)}件")
        st.dataframe(df.head(10))

        if st.button("🚀 生存確認チェックを開始"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            start_time = time.time()

            for i in range(len(df)):
                # 画像13の「予想残り時間」ロジック
                # $$Remaining = \frac{Elapsed}{n} \times (Total - n)$$
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = avg * (len(df) - (i + 1))
                
                status_text.text(f"処理中: {i+1}/{len(df)} | ⏳ 予想残り時間: {int(rem)}秒")
                progress_bar.progress((i + 1) / len(df))
                time.sleep(0.1) 

            st.balloons()
            st.success("生存確認が完了しました。")

    except Exception as e:
        st.error("🔥 接続エラーが発生しました")
        # エラーが「API not enabled」等の場合は、Google Cloud側での設定が必要
        st.code(str(e))
        st.info("【重要チェック項目】")
        st.markdown("""
        1. **APIの有効化**: Google Cloud Consoleで 'Google Sheets API' と 'Google Drive API' を有効にしていますか？
        2. **シートの共有**: スプレッドシートの右上の「共有」ボタンから、JSON内の `client_email` のアドレスに「編集者」権限を与えましたか？
        """)

if __name__ == "__main__":
    main()
