import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import random
import requests
from datetime import datetime

# =========================================================
# 1. 認証エンジン（Secretsチェック）
# =========================================================
def get_gspread_client():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("❌ Secretsに 'gcp_service_account' が設定されていません。")
            return None
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace('\\n', '\n')
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"🔥 認証エラー: {str(e)}")
        return None

# =========================================================
# 2. 【究極ステルス】住宅プロキシ専用エンジン
# =========================================================
def check_threads_stealth(username, proxy_input):
    # Threads公式アプリが使用しているID（これがないと弾かれやすい）
    THREADS_APP_ID = "238280553337440"
    
    url = f"https://www.threads.net/@{username}"
    
    # 住宅プロキシをURL形式に変換
    proxies = None
    if proxy_input and "@" in proxy_input:
        proxies = {"http": f"http://{proxy_input}", "https": f"http://{proxy_input}"}

    # セッションを開始（クッキーを保持して人間らしく振る舞う）
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "X-IG-App-ID": THREADS_APP_ID,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # ステップ1: まずトップページを訪れて「私は一般客です」というクッキーを拾う
        session.get("https://www.threads.net/", headers=headers, proxies=proxies, timeout=10)
        time.sleep(random.uniform(1, 3)) # わずかに待機
        
        # ステップ2: 本番のアカウント確認
        resp = session.get(url, headers=headers, proxies=proxies, timeout=15)
        content = resp.text.lower()
        
        if f"@{username.lower()}" in content:
            return "生存", True
        if "login" in content:
            return "判定不能（Meta遮断中）", False
        return "存在しない（凍結/削除）", True
    except Exception as e:
        return f"通信失敗: {type(e).__name__}", False

# =========================================================
# 3. メインコントロール
# =========================================================
def main():
    st.set_page_config(page_title="Threads Final Checker", layout="wide")
    st.title("🛡️ Threads生存確認：ステルス・住宅プロキシ版")

    # 診断メッセージ
    st.info("システム起動中... 認証を確認しています。")

    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False

    client = get_gspread_client()
    if not client:
        st.warning("認証に失敗しました。Secretsを確認してください。")
        return

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 準備完了！ 調査対象: {len(df)}件")

        col1, col2 = st.columns(2)
        start_btn = col1.button("🚀 調査開始", use_container_width=True)
        stop_btn = col2.button("⏹️ 中断", use_container_width=True)

        if stop_btn:
            st.session_state.stop_requested = True

        if start_btn:
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
                    st.error("⏹️ 中断しました。")
                    break

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                # 判定実行
                status, _ = check_threads_stealth(username, proxy)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                # シート反映
                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, now_str)

                # 予測終了時間
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = avg * (len(df) - (i + 1))

                status_area.markdown(f"**進行中**: `{username}` -> **{status}** \n⏳ **およその残り時間**: `{int(rem)}`秒")
                progress_bar.progress((i + 1) / len(df))

                # 住宅IPを守るための「深めのゆらぎ」（15～25秒）
                time.sleep(random.uniform(15, 25))

            if not st.session_state.stop_requested:
                st.balloons()
                st.success("全ての調査が完了しました！")

    except Exception as e:
        st.error(f"🔥 システムエラー: {str(e)}")

if __name__ == "__main__":
    main()
