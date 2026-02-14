import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（鍵の自動復元版） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # 1. Secretsから「暗号文字列」だけを取得
    if "pk_base64" not in st.secrets:
        st.error("設定エラー: Secretsに 'pk_base64' が見つかりません。")
        st.stop()
        
    base64_key = st.secrets["pk_base64"]
    
    # 2. ここでプログラムが「正しい鍵の形」に組み立て直します
    # (ヘッダーをつけ、64文字ごとに改行を入れる)
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(base64_key), 64):
        formatted_key += base64_key[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"
    
    # 3. 固定情報と合体させて完成
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
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/checker-bot%40threads-checker.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }

    creds = Credentials.from_service_account_info(sa_info, scopes=scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Threads調査ツール")
    list_ws = sheet.worksheet("調査リスト")
    
    # プロキシシートの読み込み
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
