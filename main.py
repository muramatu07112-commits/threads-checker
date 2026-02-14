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
# 1. 認証エンジン（金庫 Secrets から自動読込）
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
# 2. 高精度判定エンジン（メタタグ監視方式）
# =========================================================
def check_threads_strict(username, proxy_str=None):
    url = f"https://www.threads.net/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    proxies = None
    if proxy_str:
        parts = proxy_str.split(':')
        if len(parts) == 4:
            p = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            proxies = {"http": p, "https": p}

    try:
        # プロフィールリンクへ直接アクセス
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if resp.status_code in [403, 407]: return "プロキシブロック", False
        
        content = resp.text.lower()
        # SEO用のメタタイトルを確認（これが最も確実な生存の指紋です）
        signature = f"(@{username.lower()})"
        
        if signature in content:
            return "生存", True
        elif "login" in content and resp.status_code == 200:
            return "検閲（ログイン要求）", False
        else:
            return "凍結/削除", True
    except:
        return "通信失敗", False

# =========================================================
# 3. メインコントロールパネル（全機能統合）
# =========================================================
def main():
    st.set_page_config(page_title="Threads Pro Checker", layout="wide")
    st.title("🛡️ Threads生存確認：完全統合版システム")

    # 状態管理の初期化
    if "is_running" not in st.session_state: st.session_state.is_running = False
    if "stop_requested" not in st.session_state: st.session_state.stop_requested = False

    # 認証とシート取得
    client = get_gspread_client()
    if not client: st.stop()

    sheet_url = st.secrets.get("sheet_url", "")
    try:
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.success(f"✅ 接続成功！ 対象データ: {len(df)}件")

        # --- 操作パネル ---
        col1, col2 = st.columns(2)
        start_btn = col1.button("🚀 調査開始", use_container_width=True, disabled=st.session_state.is_running)
        # 【機能1】途中停止ボタン
        stop_btn = col2.button("⏹️ 中断（次の処理で停止）", use_container_width=True)

        if stop_btn:
            st.session_state.stop_requested = True
            st.info("⏹️ 中断リクエストを受け付けました。")

        if start_btn:
            st.session_state.is_running = True
            st.session_state.stop_requested = False
            
            # 列の準備
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
                # 【機能1の実装】中断チェック
                if st.session_state.stop_requested:
                    st.error("調査を中断しました。")
                    break

                username = str(row.get("ID", "")).replace("@", "").strip()
                proxy = str(row.get("プロキシ", ""))
                
                # 生存判定
                status, _ = check_threads_strict(username, proxy)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                # 【機能2】スプレッドシートへのリアルタイム反映
                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, now_str)

                # 【機能3】残り時間の算出（画像13の数式）
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = avg * (len(df) - (i + 1))

                status_area.markdown(f"**進行中**: `{username}` -> **{status}** ({i+1}/{len(df)})  \n⏳ **予想残り時間**: `{int(rem)}`秒")
                progress_bar.progress((i + 1) / len(df))

                # 【重要】5秒～10秒の人間らしい「ゆらぎ待機」
                time.sleep(random.uniform(5, 10))

            st.session_state.is_running = False
            if not st.session_state.stop_requested:
                st.balloons()
                st.success("全てのチェックが完了しました！")

    except Exception as e:
        st.error(f"🔥 システムエラー: {str(e)}")
        st.session_state.is_running = False

if __name__ == "__main__":
    main()
