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

    # 【核心】Secretsではなく、ここに直接定義します
    # ここにスペースや改行が混じっていても、下の正規表現で物理的に消滅させます
    raw_pk_data = "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCVa+ODKkA7W/Js71Bk8mi/fhR6LB6n7punbUFj5yB3pdGrmdw96zE+EnfjB/adIXl2Ns77zN7brGTvXp6Q5T6W7KIRoidR/laIarm6hrXloAiqFmkP3O0gseD9wDMMUHEFD8tcgUZPSQ9Pa5jYl2ndc+/KTvMKbW7NgOKbiikK8BcmLlmNE032SHMjznfkWbvtFCIYmFUn+aixKODS/NZP4wuV/QBlRuLz0XCN7e5ImNtODN3IqKWzKdkZMSSDQIYIabcBkdH0cKrDD94C5H14UhZ5B/rERQ2NixtEZvDfCAqAPgKBoLZLBCJnnCCxra1FvXZDMNauZE/R3zUVaMXDAgMBAAECggEAGCm4Qu/EL1UxINiaYZipw725xf/4fSOi3DJYzrUDlRWlnkGBzMzgjYGxQItCY2tQc9jbqxeFdcJyyPdtJPRk1Q+bEnvSUm3MnuOSi3MPXPOBHCAHav3UKsczaD/1/xzaDWU6HCw+BOSSUdFzMBLWpo2XiP1DaTkBB3JYJHgHdQVekOY2975FkmzcE+rDO9XOkLajG30HPDDVfyhC2DFIngYUx9sdz08aOjrgV/2z4bQDe2FMwLGMdiyPcxlKOakVAQCUZtgERj/p+J3mS9KliQ819sMsfDUmbibJD4ORu3OObOIN/wn/r6LJ0Q9QpVXJXtHEvFq9o0QKBgQDDxYN5beRdmFIfncJbcE5vMmR6IbJh7arGj/ADlkQMhmZZiovbvJmYNG9YpkijlP0Vhk5fGshiPb5RQ82sL67k+8kCQznr599ZimD3DGK/XLNIgMCxOP/OqrSxcFfnMdeAjB0hqW6Ic/fNDHlezwfUuVeeoLogDdjlVPd+0EyZ1wKBgQDDY/SCNEWEmrc+F81qcaURxm9NGTRFTUelRlmnkBcVfW91VNB1Q9jTCnEIsAFn/yhZfAZ1/rmqps+WGs+HmlyV1cLEcKzofjQEIbPuFhVX20TMR5yYF460TS0MGR+1defoV8yCqI3IluCoWfV7vOBXNHaI4X/Q6vOL8s+RXQ9t9QKBgB2AYjOmT8ea8KU7DNLita8kFOgis9L2EcoiXrTrrA2HI11S94iBf1PkcvMU+9VK2min+J90VcYYL9nnMdNEzEJNfxkMMGpQYuQHal1QTIEx4wKGBIOwZzwplVk36Mc6R5NjifBMrA98CleoDZIv+Koh1AZfiizSaWEF0NYXZbO5AoGAfNYQEmBzShXPncx3YdraLFEsK4Y+70hAzkf0YCqflQtfeweFaGbA0ZWKQpKxU1Ci5wlm11y4I2AQoUbf8TOek9zPY9LZpnF7qmgeHa/eUxO1EQ9v7XyfoHLupRwoNjfuw3PVJmWqsKffgbB4N2alrxHF6g6pK0Hx+ShZlfZvNUECgYAUbMfOwp2JzY4fDa7XQQJJt4jjlt1QCFRpjT7Vzgw5hafWmCd5U0wTDSFj+bm5Fbjgi7FMJozXnc+CJzC0Q6+27wFB7G0wwrgeASi0uwDFm/1gN7jPPy0LQDogUvO8RlKRMP+xRD5QZl7yyXalm3j8u5hq+b3LbwGqIT+3NtCRQQ=="

    # 【徹底洗浄ロジック】英数字、プラス、スラッシュ、イコール以外をすべて削除
    # これにより、コピペで混入したスペース、改行、バックスラッシュを物理的に抹殺します
    clean_body = re.sub(r'[^a-zA-Z0-9+/=]', '', raw_pk_data)
    
    # PEM形式（64文字ごとの改行）に強制構築
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_body), 64):
        formatted_key += clean_body[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"

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
    st.success("✅ スプレッドシートへの接続に成功しました！")

except Exception as e:
    st.error(f"❌ 接続エラー: {e}")
    st.stop()

# --- 2. 調査実行セクション（画像13のロジック包含） ---
all_rows = list_ws.get_all_values()
if len(all_rows) > 1:
    targets = all_rows[1:]
    if st.button("🚀 凍結確認を開始"):
        progress_bar = st.progress(0)
        start_time = time.time()
        for i, row in enumerate(targets):
            # の予想残り時間計算
            elapsed = time.time() - start_time
            avg = elapsed / (i + 1) if i > 0 else 1.2
            rem = int((len(targets) - (i + 1)) * avg)
            st.info(f"⏳ 予想残り時間: 約 {rem // 60}分 {rem % 60}秒")
            
            target_id = row[0]
            try:
                res = requests.get(f"https://www.threads.net/@{target_id}", timeout=10)
                result = "生存" if res.status_code == 200 else "凍結/削除"
            except:
                result = "エラー"
            
            list_ws.update_cell(i + 2, 2, result)
            progress_bar.progress((i + 1) / len(targets))
            time.sleep(1)
        st.success("✅ 調査完了！")
