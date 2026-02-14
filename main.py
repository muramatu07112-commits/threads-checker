import streamlit as st
import gspread
import requests
import time
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（文字列一括読み込み版） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Secretsから "threads_key" という名前の「ただの文字列」を読み込む
    if "threads_key" in st.secrets:
        key_string = st.secrets["threads_key"]
        # その文字列をJSON（プログラムが読める辞書）に変換する
        sa_info = json.loads(key_string)
    else:
        st.error("設定エラー: Secretsに 'threads_key' が保存されていません。")
        st.stop()

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    
    # プロキシシートの読み込み（念のためエラー回避付き）
    try:
        proxy_ws = sheet.worksheet("プロキシ")
    except:
        proxy_ws = None

    st.success("✅ Googleスプレッドシートへの接続に成功しました！")

except Exception as e:
    st.error("❌ 接続エラーが発生しました。")
    st.warning(f"理由: {str(e)}")
    st.stop()

# --- 2. 調査実行セクション ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    # プロキシリストの取得
    proxy_list = []
    if proxy_ws:
        try:
            proxy_list = [r[0] for r in proxy_ws.get_all_values()[1:] if r]
        except:
            pass

    st.sidebar.write(f"📊 調査対象: {len(targets)} 件")
    
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            # 残り時間計算
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.2
            rem = int((len(targets) - (i + 1)) * avg)
            time_text.info(f"⏳ 予想残り時間: 約 {rem // 60}分 {rem % 60}秒")
            
            target_id = row[0]
            status_text.text(f"調査中: {target_id}")
            
            p_config = None
            if proxy_list:
                p = proxy_list[i % len(proxy_list)]
                p_url = p if p.startswith("http") else f"http://{p}"
                p_config = {"http": p_url, "https": p_url}
            
            try:
                res = requests.get(f"https://www.threads.net/@{target_id}", proxies=p_config, timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "通信エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
            
        time_text.empty()
        st.success("✅ 調査完了！")
        st.balloons()
else:
    st.info("スプレッドシートのA列にIDを入力してください。")
