import streamlit as st
import gspread
import requests
import time
import re
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（徹底洗浄・自己修復版） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # Secretsから保存されている鍵データを取得（どの名前で保存していても対応）
    raw_key = ""
    target_keys = ["pk_base64", "pk_data", "pk_raw", "threads_key", "gcp_service_account"]
    for k in target_keys:
        if k in st.secrets:
            raw_key = str(st.secrets[k])
            break
            
    if not raw_key:
        raw_key = str(st.secrets)

    # 【徹底洗浄ロジック】英数字、プラス、スラッシュ、イコール以外を全て抹殺
    # これにより、コピペで混入したスペース、改行、バックスラッシュを物理的に消滅させます
    clean_body = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_key.replace("PRIVATE KEY", ""))
    
    # 【PEM再構築】正しいPEM形式（64文字ごとの改帰）に強制的に組み直す
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_body), 64):
        formatted_key += clean_body[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"

    # 認証情報を辞書にセット
    sa_info = {
        "type": "service_account",
        "project_id": "threads-checker",
        "private_key_id": "feedba476b9bcad61b66b93e91aaab7c871f2d52",
        "private_key": formatted_key,
        "client_email": "checker-bot@threads-checker.iam.gserviceaccount.com",
        "client_id": "102355019665572843670",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/checker-bot%40threads-checker.iam.gserviceaccount.com"
    }

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    
    try:
        proxy_ws = sheet.worksheet("プロキシ")
    except:
        proxy_ws = None

    st.success("✅ Googleスプレッドシートへの接続に成功しました！")

except Exception as e:
    st.error(f"❌ 接続エラー: {e}")
    st.stop()

# --- 2. 調査実行セクション（画像13のロジックを最適化） ---
#
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    proxy_list = [r[0] for r in proxy_ws.get_all_values()[1:] if r] if proxy_ws else []

    st.sidebar.write(f"📊 調査対象: {len(targets)} 件")
    
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        start_time = time.time()
        
        for i, row in enumerate(targets):
            # 残り時間計算ロジック
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
