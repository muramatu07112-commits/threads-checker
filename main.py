import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（基本に忠実な修正版） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sa_info = dict(st.secrets["gcp_service_account"])
    
    # 唯一必要な処理：文字としての「\n」を、本当の改行コードに変換する
    sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    proxy_ws = sheet.worksheet("プロキシ")
    st.success("✅ Googleスプレッドシートへの接続に成功しました！")

except Exception as e:
    st.error("❌ 接続エラーが発生しました。")
    st.warning(f"理由: {str(e)}")
    st.stop()

# --- 2. 調査実行セクション ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    # プロキシリストの読み込み（エラー回避付き）
    try:
        proxy_list = [r[0] for r in proxy_ws.get_all_values()[1:] if r]
    except:
        proxy_list = []

    st.sidebar.write(f"📊 調査対象: {len(targets)} 件")
    st.sidebar.write(f"🌐 プロキシ: {len(proxy_list)} 件")
    
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            # 残り時間の計算
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.2
            rem = int((len(targets) - (i + 1)) * avg)
            time_text.info(f"⏳ 予想残り時間: 約 {rem // 60}分 {rem % 60}秒")
            
            target_id = row[0]
            status_text.text(f"調査中 ({i+1}/{len(targets)}): {target_id}")
            
            # プロキシ設定
            p_config = None
            if proxy_list:
                p = proxy_list[i % len(proxy_list)]
                # http://の有無を確認して補正
                p_url = p if p.startswith("http") else f"http://{p}"
                p_config = {"http": p_url, "https": p_url}
            
            # 生存確認実行
            try:
                res = requests.get(f"https://www.threads.net/@{target_id}", proxies=p_config, timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "通信エラー"
            
            # 結果書き込み
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
            
        time_text.empty()
        status_text.success("✅ 調査が完了しました！シートを確認してください。")
        st.balloons()
else:
    st.info("スプレッドシートの「調査リスト」シートのA列にIDを入力してください。")
