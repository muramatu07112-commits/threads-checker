import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
import requests
import random  # ランダムな待機時間のために追加
from datetime import datetime

# =========================================================
# 1. 判定ロジックの高度化（シグネチャ分析 + ランダム待機）
# =========================================================
def check_threads_strict(username, proxy_str=None):
    url = f"https://www.threads.net/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    proxies = None
    if proxy_str:
        # 形式 ip:port:user:pass を想定
        parts = proxy_str.split(':')
        if len(parts) == 4:
            p = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            proxies = {"http": p, "https": p}

    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        
        # プロキシ自体のブロック判定
        if resp.status_code in [403, 407]:
            return "プロキシブロック", False
            
        # コンテンツによる厳密判定
        content = resp.text.lower()
        if resp.status_code == 200 and username.lower() in content:
            if "page not found" in content or "unavailable" in content:
                return "凍結/削除", True
            return "生存", True
        elif resp.status_code == 404 or "page not found" in content:
            return "凍結/削除", True
        else:
            return f"エラー({resp.status_code})", False

    except Exception as e:
        return f"通信失敗: {type(e).__name__}", False

# =========================================================
# 2. メインシステム
# =========================================================
def main():
    st.set_page_config(page_title="Threads Pro Checker", layout="wide")
    
    # 中断フラグの管理
    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False

    st.title("🛡️ Threads生存確認 (プロキシ・ゆらぎ待機版)")
    
    with st.sidebar:
        raw_json = st.text_area("1. Service Account JSON")
        sheet_url = st.text_area("2. Spreadsheet URL")
        user_col = st.text_input("ID列名", "username")
        proxy_col = st.text_input("プロキシ列名", "proxy")
        if st.button("🔴 緊急停止リセット"):
            st.session_state.stop_requested = False
            st.rerun()

    if not raw_json or not sheet_url:
        st.info("サイドバーに設定を入力してください。")
        return

    try:
        # 認証
        info = json.loads(raw_json)
        info["private_key"] = info["private_key"].replace('\\n', '\n')
        creds = Credentials.from_service_account_info(
            info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        
        df = pd.DataFrame(sheet.get_all_records())
        st.write(f"📊 読込データ: {len(df)}件")

        col1, col2 = st.columns(2)
        start_btn = col1.button("🚀 調査開始", use_container_width=True)
        stop_btn = col2.button("⏹️ 中断", use_container_width=True)

        if stop_btn:
            st.session_state.stop_requested = True

        if start_btn:
            st.session_state.stop_requested = False
            progress_bar = st.progress(0)
            status_text = st.empty()
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
                    st.error("⏹️ 中断されました。")
                    break

                user = str(row.get(user_col, "")).replace("@", "").strip()
                proxy = str(row.get(proxy_col, ""))
                
                # 判定実行
                status, is_valid_proxy = check_threads_strict(user, proxy)
                
                # 結果書き込み
                sheet.update_cell(i + 2, res_idx, status)
                sheet.update_cell(i + 2, time_idx, datetime.now().strftime("%Y-%m-%d %H:%M"))

                if not is_valid_proxy and "プロキシ" in status:
                    st.sidebar.warning(f"⚠️ プロキシブロック報告: 行 {i+2}")

                # 時間計算
                elapsed = time.time() - start_time
                avg = elapsed / (i + 1)
                rem = avg * (len(df) - (i + 1))
                
                status_text.markdown(f"**進行中**: `{user}` | 結果: **{status}** | 残り約 `{int(rem)}`秒")
                progress_bar.progress((i + 1) / len(df))
                
                # --- 【重要】5秒～10秒のゆらぎ設定 ---
                wait_time = random.uniform(5, 10)
                time.sleep(wait_time) 

            if not st.session_state.stop_requested:
                st.balloons()
                st.success("全ての工程が完了しました。")

    except Exception as e:
        st.error(f"🔥 システムエラー: {e}")

if __name__ == "__main__":
    main()
