import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import random
import requests
from datetime import datetime

# =========================================================
# 1. 認証エンジン
# =========================================================
def get_gspread_client():
    try:
        if "gcp_service_account" not in st.secrets: return None
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace('\\n', '\n')
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    except: return None

# =========================================================
# 2. 【ステルス版】404優先判定エンジン
# =========================================================
def check_threads_stealth_v2(username, proxy_input):
    THREADS_APP_ID = "238280553337440"
    url = f"https://www.threads.net/@{username}"
    proxies = {"http": f"http://{proxy_input}", "https": f"http://{proxy_input}"} if proxy_input else None
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "X-IG-App-ID": THREADS_APP_ID,
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    try:
        session.get("https://www.threads.net/", headers=headers, proxies=proxies, timeout=10)
        time.sleep(random.uniform(1, 2))
        resp = session.get(url, headers=headers, proxies=proxies, timeout=15)
        if resp.status_code == 404: return "存在しない（凍結/削除）", True
        content = resp.text.lower()
        if f"@{username.lower()}" in content: return "生存", True
        if "login" in content: return "判定不能（Meta遮断中）", False
        return "存在しない（凍結/削除）", True
    except: return "通信失敗", False

# =========================================================
# 3. メインコントロール
# =========================================================
def main():
    st.set_page_config(page_title="Threads Resume Checker", layout="wide")
    st.title("🛡️ Threads生存確認：再開機能付き・完全統合版")

    if "stop_requested" not in st.session_state: st.session_state.stop_requested = False

    client = get_gspread_client()
    if not client: st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        # データの最新状態を常に取得
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        st.success(f"✅ シート接続完了！ 全体データ: {len(df)}件")

        # 列のインデックス取得
        headers = sheet.row_values(1)
        for h in ["判定結果", "確認日時"]:
            if h not in headers:
                sheet.update_cell(1, len(headers)+1, h)
                headers = sheet.row_values(1)
        res_idx = headers.index("判定結果") + 1
        time_idx = headers.index("確認日時") + 1

        # 操作パネル
        col1, col2, col3 = st.columns(3)
        start_new_btn = col1.button("🚀 最初から調査", use_container_width=True)
        resume_btn = col2.button("⏯️ 続きから再開", use_container_width=True)
        stop_btn = col3.button("⏹️ 中断", use_container_width=True)

        if stop_btn: st.session_state.stop_requested = True

        mode = None
        if start_new_btn: mode = "new"
        if resume_btn: mode = "resume"

        if mode:
            st.session_state.stop_requested = False
            progress_bar = st.progress(0)
            status_area = st.empty()
            start_time = time.time()
            processed_count = 0

            for i, row in df.iterrows():
                if st.session_state.stop_requested: break

                # 【再開ロジック】モードが「再開」かつ「判定結果」が既にある場合はスキップ
                current_result = str(row.get("判定結果", "")).strip()
                if mode == "resume" and current_result != "":
                    processed_count += 1
                    continue

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                status, _ = check_threads_stealth_v2(username, proxy)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, now_str)
                processed_count += 1

                # 予測終了時間
                elapsed = time.time() - start_time
                actual_processed = processed_count - (df.index.get_loc(i) if mode == "resume" else 0)
                # 簡易的な計算
                rem_items = len(df) - processed_count
                avg = elapsed / max(actual_processed, 1)
                rem_sec = avg * rem_items

                status_area.markdown(f"**進行中**: `{username}` -> **{status}** ({processed_count}/{len(df)})  \n⏳ **およその残り時間**: `{int(rem_sec)}`秒")
                progress_bar.progress(processed_count / len(df))

                time.sleep(random.uniform(15, 25))

            if not st.session_state.stop_requested:
                st.balloons()
                st.success("全ての調査が完了しました！")

    except Exception as e:
        st.error(f"🔥 エラー: {str(e)}")

if __name__ == "__main__":
    main()
