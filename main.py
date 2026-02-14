import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import random
import requests
from datetime import datetime

# =========================================================
# 1. 認証エンジン（Secretsから読み込む標準形）
# =========================================================
def get_gspread_client():
    try:
        if "gcp_service_account" not in st.secrets:
            return None
        info = dict(st.secrets["gcp_service_account"])
        # 改行コードの自動復元
        info["private_key"] = info["private_key"].replace('\\n', '\n')
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes)
        return gspread.authorize(creds)
    except:
        return None

# =========================================================
# 2. 判定エンジン（1段階・404優先）
# =========================================================
def check_threads_final(username, proxy_input):
    url = f"https://www.threads.net/@{username}"
    proxies = {"http": f"http://{proxy_input}", "https": f"http://{proxy_input}"} if proxy_input else None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "X-IG-App-ID": "238280553337440"}
    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if resp.status_code == 404: return "存在しない（凍結/削除）", True
        if f"@{username.lower()}" in resp.text.lower(): return "生存", True
        if "login" in resp.text.lower(): return "判定不能（Meta遮断中）", False
        return "存在しない（凍結/削除）", True
    except: return "通信失敗", False

# =========================================================
# 3. メイン
# =========================================================
def main():
    st.set_page_config(page_title="Threads Final", layout="wide")
    st.title("🛡️ Threads生存確認：最終安定版")
    if "stop" not in st.session_state: st.session_state.stop = False

    client = get_gspread_client()
    if not client: st.error("認証待ち：Secretsを設定してください"); st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 接続成功！ 対象: {len(df)}件")

        col1, col2, col3 = st.columns(3)
        mode = "new" if col1.button("🚀 最初から") else ("resume" if col2.button("⏯️ 続きから") else None)
        if col3.button("⏹️ 中断"): st.session_state.stop = True

        if mode:
            st.session_state.stop = False
            pb = st.progress(0)
            status_area = st.empty()
            
            headers = sheet.row_values(1)
            for h in ["判定結果", "確認日時"]:
                if h not in headers: sheet.update_cell(1, len(headers)+1, h)
            headers = sheet.row_values(1)
            r_idx, t_idx = headers.index("判定結果")+1, headers.index("確認日時")+1

            for i, row in df.iterrows():
                if st.session_state.stop: break
                if mode == "resume" and str(row.get("判定結果","")).strip() != "": continue

                user = str(row.get("ID","")).replace("@","").strip()
                status, _ = check_threads_final(user, str(row.get("プロキシ","")))
                
                sheet.update_cell(i+2, r_idx, status)
                sheet.update_cell(i+2, t_idx, datetime.now().strftime("%m/%d %H:%M"))

                status_area.write(f"進行中: {user} -> {status}")
                pb.progress((i+1)/len(df))
                time.sleep(random.uniform(30, 60))

    except Exception as e: st.error(f"エラー: {e}")

if __name__ == "__main__": main()
