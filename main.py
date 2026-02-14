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
# 1. 認証エンジン（Secrets経由）
# =========================================================
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            # \n を実際の改行コードに修復（ValueError対策）
            info["private_key"] = info["private_key"].replace('\\n', '\n')
            
            scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            return gspread.authorize(creds)
        return None
    except Exception as e:
        st.error(f"🔥 認証エラー: {str(e)}")
        return None

# =========================================================
# 2. 生存判定エンジン（厳密判定・プロキシ対応）
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
        if resp.status_code in [403, 407]: return "プロキシブロック", False
        content = resp.text.lower()
        if resp.status_code == 200 and username.lower() in content:
            if "page not found" in content or "unavailable" in content: return "凍結/削除", True
            return "生存", True
        elif resp.status_code == 404 or "page not found" in content: return "凍結/削除", True
        else: return f"エラー({resp.status_code})", False
    except: return "通信失敗", False

# =========================================================
# 3. メインコントロールパネル
# =========================================================
def main():
    st.set_page_config(page_title="Threads Pro Checker", layout="wide")
    st.title("🛡️ Threads生存確認システム (完全統合版)")

    # 停止フラグの管理
    if "is_running" not in st.session_state: st.session_state.is_running = False
    if "stop_requested" not in st.session_state: st.session_state.stop_requested = False

    # 認証
    client = get_gspread_client()
    if not client:
        st.warning("👈 StreamlitのSecretsを設定してください。")
        st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    if not sheet_url:
        st.error("Secretsに 'sheet_url' が設定されていません。")
        st.stop()

    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 接続成功！ 対象データ: {len(df)}件")
        st.dataframe(df.head(10))

        # 操作ボタン
        col1, col2 = st.columns(2)
        start_btn = col1.button("🚀 調査開始", use_container_width=True, disabled=st.session_state.is_running)
        stop_btn = col2.button("⏹️ 中断", use_container_width=True)

        if stop_btn:
            st.session_state.stop_requested = True
            st.info("⏹️ 中断リクエストを送信しました。次の処理で停止します。")

        if start_btn:
            st.session_state.is_running = True
            st.session_state.stop_requested = False
            
            # 列の準備（判定結果、確認日時）
            headers = sheet.row_values(1)
            for h in ["判定結果", "確認日時"]:
                if h not in headers:
                    sheet.update_cell(1, len(headers)+1, h)
                    headers = sheet.row_values(1)
            res_idx = headers.index("判定結果") + 1
            time_idx = headers.index("確認日時") + 1

            progress_bar = st.progress(0)
            status_area = st.empty()
            start_time = time.time()

            for i, row in df.iterrows():
                # 中断チェック
                if st.session_state.stop_requested:
                    st.error("調査を中断しました。")
                    break

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                # 生存判定実行
                status, is_valid_proxy = check_threads_status(username, proxy)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                # シートに即時書き込み
                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, now_str)

                # 【画像13のロジック】残り時間の算出
                elapsed = time.time
