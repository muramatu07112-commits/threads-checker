import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
import requests
from datetime import datetime

# =========================================================
# 【設定】UI・スコープ定義
# =========================================================
def initialize_ui():
    st.set_page_config(page_title="Threads Survival Checker", layout="wide")
    st.title("🛡️ 鉄壁のThreads生存確認システム (実戦稼働版)")
    st.sidebar.header("⚙️ システム設定")
    raw_json = st.sidebar.text_area("1. JSONファイルの中身を全部貼り付け", height=200)
    sheet_url = st.sidebar.text_area("2. スプレッドシートのURLを貼り付け", height=100)
    # ユーザー名が入っている列名（シートの1行目の名前に合わせてください）
    target_column = st.sidebar.text_input("3. ユーザー名(ID)が入っている列名", value="username")
    return raw_json, sheet_url, target_column

def get_creds_with_scopes(json_str):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    try:
        info = json.loads(json_str.strip())
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace('\\n', '\n')
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    except: return None

# =========================================================
# 【核心】Threads生存判定ロジック
# =========================================================
def check_threads_status(username):
    """
    Threadsのプロフィールページにアクセスし、生存を確認する。
    """
    url = f"https://www.threads.net/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    try:
        # プロキシ補正（将来的にここにプロキシ設定を追加可能）
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return "生存"
        elif response.status_code == 404:
            return "凍結/削除"
        elif response.status_code == 429:
            return "制限(要待機)"
        else:
            return f"エラー({response.status_code})"
    except Exception as e:
        return "通信エラー"

# =========================================================
# メイン実行ループ
# =========================================================
def main():
    raw_json, sheet_url, target_col = initialize_ui()
    if not raw_json or not sheet_url:
        st.warning("👈 左側のサイドバーに設定を入力してください。")
        return

    try:
        creds = get_creds_with_scopes(raw_json)
        if not creds: return
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.get_worksheet(0)
        
        # 全データ読み込み
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        
        if target_col not in df.columns:
            st.error(f"❌ 列名 '{target_col}' が見つかりません。現在の列名: {list(df.columns)}")
            return

        st.success(f"✅ 接続成功！ 対象データ: {len(df)}件")
        st.dataframe(df.head(10))

        if st.button("🚀 生存確認チェックを開始"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            start_time = time.time()
            
            # 結果を格納するリスト
            results = []
            
            # スプレッドシートの「結果」列のインデックスを探す（なければ作成）
            headers = sheet.row_values(1)
            if "判定結果" not in headers:
                sheet.update_cell(1, len(headers) + 1, "判定結果")
                sheet.update_cell(1, len(headers) + 2, "確認日時")
                result_col_idx = len(headers) + 1
                time_col_idx = len(headers) + 2
            else:
                result_col_idx = headers.index("判定結果") + 1
                time_col_idx = headers.index("確認日時") + 1

            for i, row in df.iterrows():
                username = str(row[target_col]).replace("@", "").strip()
                
                # 実際の判定を実行
                status = check_threads_status(username)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # スプレッドシートに即時書き込み（i+2 はヘッダーの次から）
                sheet.update_cell(i + 2, result_col_idx, status)
                sheet.update_cell(i + 2, time_col_idx, now_str)

                # 画像13の「予想残り時間」ロジック
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = avg * (len(df) - (i + 1))
                
                status_text.markdown(f"**処理中**: `{username}` -> **{status}** ({i+1}/{len(df)})  \n⏳ **予想残り時間**: `{int(rem)}`秒")
                progress_bar.progress((i + 1) / len(df))
                
                # Metaのブロックを避けるための適度なインターバル
                time.sleep(1.5) 

            st.balloons()
            st.success("完了しました！ スプレッドシートを確認してください。")

    except Exception as e:
        st.error(f"🔥 エラー: {str(e)}")

if __name__ == "__main__":
    main()
