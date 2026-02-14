import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import random
import requests
from datetime import datetime

# =========================================================
# 1. 認証エンジン（Secretsから取得）
# =========================================================
def get_gspread_client():
    try:
        if "gcp_service_account" not in st.secrets:
            return None
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace('\\n', '\n')
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes)
        return gspread.authorize(creds)
    except Exception:
        return None

# =========================================================
# 2. 【一撃必殺】軽量判定エンジン（1段階アクセス）
# =========================================================
def check_threads_minimal(username, proxy_input):
    url = f"https://www.threads.net/@{username}"
    proxies = {"http": f"http://{proxy_input}", "https": f"http://{proxy_input}"} if proxy_input else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "X-IG-App-ID": "238280553337440",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    try:
        # 直接アクセス（リクエスト回数を最小化）
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        
        # 1. 404（ページ不在）なら即座に確定
        if resp.status_code == 404:
            return "存在しない（凍結/削除）", True
            
        content = resp.text.lower()
        
        # 2. IDが含まれていれば生存
        if f"@{username.lower()}" in content:
            return "生存", True
            
        # 3. ログイン画面が出た場合は判定不能
        if "login" in content:
            return "判定不能（Meta遮断中）", False
            
        return "存在しない（凍結/削除）", True
    except Exception:
        return "通信失敗", False

# =========================================================
# 3. メインコントロール（再開機能・30秒ゆらぎ搭載）
# =========================================================
def main():
    st.set_page_config(page_title="Threads Ultimate Checker", layout="wide")
    st.title("🛡️ Threads生存確認：再開機能・30秒ゆらぎ版")

    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False

    client = get_gspread_client()
    if not client:
        st.error("Secretsの認証設定を確認してください。")
        st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 接続成功！ 調査リスト: {len(df)}件")

        col1, col2, col3 = st.columns(3)
        btn_new = col1.button("🚀 最初から調査", use_container_width=True)
        btn_resume = col2.button("⏯️ 続きから再開", use_container_width=True)
        btn_stop = col3.button("⏹️ 中断", use_container_width=True)

        if btn_stop:
            st.session_state.stop_requested = True

        mode = "new" if btn_new else ("resume" if btn_resume else None)

        if mode:
            st.session_state.stop_requested = False
            progress_bar = st.progress(0)
            status_area = st.empty()
            start_time = time.time()
            
            headers = sheet.row_values(1)
            for h in ["判定結果", "確認日時"]:
                if h not in headers:
                    sheet.update_cell(1, len(headers)+1, h)
                    headers = sheet.row_values(1)
            res_idx = headers.index("判定結果") + 1
            time_idx = headers.index("確認日時") + 1

            for i, row in df.iterrows():
                if st.session_state.stop_requested:
                    st.warning("中断しました。")
                    break

                # 再開モード時は判定済みの行をスキップ
                if mode == "resume" and str(row.get("判定結果", "")).strip() != "":
                    continue

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                # 判定実行
                status, _ = check_threads_minimal(username, proxy)
                now_str = datetime.now().strftime("%m/%d %H:%M")

                # シート更新
                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, now_str)

                # 進捗と残り時間の表示
                done = i + 1
                elapsed = time.time() - start_time
                status_area.markdown(f"**進行中**: `{username}` -> **{status}** ({done}/{len(df)})")
                progress_bar.progress(done / len(df))

                # 【重要】Metaの警戒を解
