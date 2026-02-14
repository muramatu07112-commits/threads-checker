import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import random
import json
import requests
from datetime import datetime

# =========================================================
# 1. 認証エンジン
# =========================================================
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            info["private_key"] = info["private_key"].replace('\\n', '\n')
            scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            return gspread.authorize(creds)
        return None
    except Exception as e:
        st.error(f"🔥 認証エラー: {str(e)}")
        return None

# =========================================================
# 2. 判定エンジン
# =========================================================
def check_threads_status(username, proxy_str=None):
    url = f"https://www.threads.net/@{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    proxies = None
    if proxy_str:
        parts = proxy_str.split(':')
        if len(parts) == 4:
            p = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            proxies = {"http": p, "https": p}
    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        content = resp.text.lower()
        if resp.status_code == 200 and username.lower() in content:
            if "page not found" in content or "unavailable" in content: return "凍結/削除", True
            return "生存", True
        return "凍結/削除", True
    except:
        return "通信失敗", False

# =========================================================
# 3. メインコントロール
# =========================================================
def main():
    st.set_page_config(page_title="Threads Checker", layout="wide")
    st.title("🛡️ Threads生存確認システム (構造修復済み)")

    if "stop_requested" not in st.session_state: st.session_state.stop_requested = False

    client = get_gspread_client()
    if not client: st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 接続成功: {len(df)}件")

        col1, col2 = st.columns(2)
        start_btn = col1.button("🚀 調査開始", use_container_width=True)
        stop_btn = col2.button("⏹️ 中断", use_container_width=True)

        if stop_btn: st.session_state.stop_requested = True

        if start_btn:
            st.session_state.stop_requested = False
            progress_bar = st.progress(0)
            status_area = st.empty()
            start_time = time.time() # 初期時刻取得

            # 列インデックスの準備
            headers = sheet.row_values(1)
            for h in ["判定結果", "確認日時"]:
                if h not in headers:
                    sheet.update_cell(1, len(headers)+1, h)
                    headers = sheet.row_values(1)
            res_idx = headers.index("判定結果") + 1
            time_idx = headers.index("確認日時") + 1

            for i, row in df.iterrows():
                if st.session_state.stop_requested:
                    st.warning("⏹️ 中断リクエストにより停止しました。")
                    break

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                # 判定と書き込み
                status, _ = check_threads_status(username, proxy)
                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, datetime.now().strftime("%Y-%m-%d %H:%M"))

                # 【重要修正】画像13：残り時間の算出ロジック
                # $T_{elapsed} = T_{now} - T_{start}$
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = avg * (len(df) - (i + 1))

                status_area.markdown(f"**進行中**: `{username}` -> **{status}** | ⏳ **残り約**: `{int(rem)}`秒")
                progress_bar.progress((i + 1) / len(df))

                # 人間らしいゆらぎ待機
                time.sleep(random.uniform(5, 10))

            if not st.session_state.stop_requested:
                st.balloons()
                st.success("完了しました。")

    except Exception as e:
        st.error(f"🔥 システムエラー: {str(e)}")

if __name__ == "__main__":
    main()
