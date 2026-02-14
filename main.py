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
# 1. 認証エンジン（Secretsから自動取得）
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
# 2. 【IDダイレクトチェック】判定エンジン
# =========================================================
def check_threads_simple(username, proxy_str=None):
    # あなたが提示した「最も単純なリンク」
    url = f"https://www.threads.net/@{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    proxies = None
    if proxy_str:
        parts = proxy_str.split(':')
        if len(parts) == 4:
            p = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            proxies = {"http": p, "https": p}

    try:
        # 直接ページを読みに行く
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        content = resp.text.lower()
        
        # タイトルやメタ情報にIDが含まれているか（単純な生存確認）
        if f"@{username.lower()}" in content:
            return "生存", True
        
        # ログイン画面に飛ばされた場合
        if "login" in content and resp.status_code == 200:
            return "判定不能（Meta遮断中）", False
            
        return "存在しない（凍結/削除）", True
    except:
        return "通信失敗", False

# =========================================================
# 3. メインシステム（全機能統合版）
# =========================================================
def main():
    st.set_page_config(page_title="Threads Pro Checker", layout="wide")
    st.title("🛡️ Threads生存確認：完全統合版（IDダイレクト式）")

    if "stop_requested" not in st.session_state: st.session_state.stop_requested = False

    # 認証
    client = get_gspread_client()
    if not client: st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 接続成功！ 対象データ: {len(df)}件")

        # --- 操作パネル ---
        col1, col2 = st.columns(2)
        start_btn = col1.button("🚀 調査開始", use_container_width=True)
        # 【中断ボタン】
        stop_btn = col2.button("⏹️ 中断", use_container_width=True)

        if stop_btn:
            st.session_state.stop_requested = True
            st.info("⏹️ 中断リクエストを送信しました。次の処理で停止します。")

        if start_btn:
            st.session_state.stop_requested = False
            progress_bar = st.progress(0)
            status_area = st.empty()
            start_time = time.time()
            
            # 列の準備
            headers = sheet.row_values(1)
            for h in ["判定結果", "確認日時"]:
                if h not in headers:
                    sheet.update_cell(1, len(headers)+1, h)
                    headers = sheet.row_values(1)
            res_idx = headers.index("判定結果") + 1
            time_idx = headers.index("確認日時") + 1

            for i, row in df.iterrows():
                # 【中断チェック】
                if st.session_state.stop_requested: break

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                # 判定実行
