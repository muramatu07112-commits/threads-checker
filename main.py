import streamlit as st
import gspread
import time
import requests
from google.oauth2.service_account import Credentials

# ページ設定
st.set_page_config(page_title="Threads調査サイト", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- Google接続設定 ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # StreamlitのSecretsから鍵を読み込む設定（後ほど行います）
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    
    # シートの読み込み
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    
    # データの準備
    all_data = list_ws.get_all_values()[1:]
    proxies = [row[0] for row in proxy_ws.get_all_values()[1:]]
    to_process = [(i+2, row[0]) for i, row in enumerate(all_data) if len(row) < 2 or not row[1]]

    # 1. 登録数表示
    st.sidebar.info(f"📊 登録済み: {len(all_data)} 件")
    st.sidebar.warning(f"📝 未完了: {len(to_process)} 件")
    st.sidebar.success(f"🌐 プロキシ: {len(proxies)} 件")

except Exception as e:
    st.warning("⏳ Googleスプレッドシートの接続待機中です。設定完了後に表示されます。")
    st.stop()

# 2. 実行ボタン
if st.button("🚀 凍結確認を開始"):
    status_msg = st.empty()
    eta_msg = st.empty()
    
    # 3. 完了後「生存」と「凍結」にわけて表示（枠の準備）
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚠️ 凍結リスト")
        frozen_area = st.empty()
    with col2:
        st.subheader("✅ 生存リスト")
        alive_area = st.empty()

    frozen_list = []
    alive_list = []
    proxy_idx = 0
    start_time = time.time()

    for idx, (row_num, user_id) in enumerate(to_process):
        success = False
        while not success and proxy_idx < len(proxies):
            curr_p = proxies[proxy_idx]
            p_config = {"http": f"http://{curr_p}", "https": f"http://{curr_p}"}
            
            try:
                res = requests.get(f"https://www.threads.net/@{user_id}", proxies=p_config, timeout=10)
                
                if res.status_code == 200:
                    res_status = "生存"
                    alive_list.append(user_id)
                    success = True
                elif res.status_code == 404:
                    res_status = "凍結"
                    # 凍結を先に（リストの先頭に）追加
                    frozen_list.insert(0, user_id)
                    success = True
                elif res.status_code in [403, 429]:
                    st.error(f"🚫 IPブロック検知: {curr_p.split('@')[-1]} → プロキシを切り替えます")
                    proxy_idx += 1
                else:
                    break
            except:
                proxy_idx += 1

        if success:
            # スプレッドシートへ自動保存（オートセーブ）
            list_ws.update_cell(row_num, 2, res_status)
            
            # リアルタイム反映
            frozen_area.write(", ".join(frozen_list))
            alive_area.write(", ".join(alive_list))
            
            # 4. おおよその調査終了時刻を表示
            elapsed = time.time() - start_time
            avg = elapsed / (idx + 1)
            eta = int(avg * (len(to_process) - (idx + 1)))
            eta_msg.write(f"⌛ 完了予測まであと 約 {eta} 秒")

    st.balloons()
    st.success("すべての調査が完了しました！")
