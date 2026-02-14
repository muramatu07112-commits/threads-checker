import streamlit as st
import gspread
import requests
import time
import re
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定 (究極の洗浄・再構築エンジン) ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sa_info = dict(st.secrets["gcp_service_account"])
    
    # 【核兵器級の洗浄】鍵を一度解体して、不純物を100%排除して作り直します
    raw_key = sa_info["private_key"]
    # 1. 鍵の中身から英数字と記号以外（改行、スペース、特殊文字）をすべて物理的に消去
    core_content = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", ""))
    # 2. Googleが求める「完璧な形」で1から組み立て直す
    sa_info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{core_content}\n-----END PRIVATE KEY-----\n"

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ ついに、Google接続に成功しました！")
except Exception as e:
    st.error("❌ 接続エラーが発生しました。")
    st.warning(f"理由: {str(e)}")
    st.stop()

# --- 2. 調査実行セクション ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    proxy_list = [r[0] for r in proxy_ws.get_all_values()[1:] if r]
    
    st.sidebar.write(f"📊 調査対象: {len(targets)} 件")
    
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            # 残り時間の計算
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.5
            rem_sec = int((len(targets) - (i + 1)) * avg)
            m, s = divmod(rem_sec, 60)
            
            time_text.info(f"⏳ 予想残り時間: 約 {m}分 {s}秒")
            target_id = row[0]
            status_text.text(f"調査中: {target_id}")
            
            # プロキシ設定
            p_config = None
            if proxy_list:
                p = proxy_list[i % len(proxy_list)]
                p_config = {"http": f"http://{p}", "https": f"http://{p}"}
            
            # スレッズ確認
            try:
                res = requests.get(f"https://www.threads.net/@{target_id}", proxies=p_config, timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "通信エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
            
        time_text.empty()
        status_text.success("✅ 調査が完了しました！")
        st.balloons()
else:
    st.info("スプレッドシートにIDを入力してください。")
