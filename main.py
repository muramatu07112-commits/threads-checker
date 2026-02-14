import streamlit as st
import gspread
import requests
import time
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Threads調査ツール", layout="wide")
st.title("🌐 Threads 生存確認ツール")

# --- 1. Google接続設定（Secrets不使用・直接埋め込み版） ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # 【修正の決定打】
    # Secretsを経由せず、正しい鍵データをここに直接定義します。
    # これにより、保存時の改行コード変換や文字化けを物理的に回避します。
    
    # あなたの鍵データ（整形・掃除済み）
    clean_key_base64 = "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCVa+ODKkA7W/Js71Bk8mi/fhR6LB6n7punbUFj5yB3pdGrmdw96zE+EnfjB/adIXl2Ns77zN7brGTvXp6Q5T6W7KIRoidR/laIarm6hrXloAiqFmkP3O0gseD9wDMMUHEFD8tcgUZPSQ9Pa5jYl2ndc+/KTvMKbW7NgOKbiikK8BcmLlmNE032SHMjznfkWbvtFCIYmFUn+aixKODS/NZP4wuV/QBlRuLz0XCN7e5ImNtODN3IqKWzKdkZMSSDQIYIabcBkdH0cKrDD94C5H14UhZ5B/rERQ2NixtEZvDfCAqAPgKBoLZLBCJnnCCxra1FvXZDMNauZE/R3zUVaMXDAgMBAAECggEAGCm4Qu/EL1UxINiaYZipw725xf/4fSOi3DJYzrUDlRWlnkGBzMzgjYGxQItCY2tQc9jbqxeFdcJyyPdtJPRk1Q+bEVqGoRiQhDjJkEnvSUm3MnuOSi3MPXPOBHCAHav3UKsczaD/1/xzaDWU6HCw+BOSSUdFzMBLWpo2XiP1DaTkBB3JYJHgHdQVekOY2975FkmzcE+rDO9XOkLajG30HPDDVfyhC2DFIngYUx9sdz08aOjrgV/2z4bQDe2FMwLGMdiyPcxlKOakVAQCUZtgERj/p+J3mS9KliQ819sMsfDUmbibJD4ORu3OObOIN/wn/r6LJ0Q9QpVXJXtHEvFq9o0QKBgQDDxYN5beRdmFIfncJbcE5vMmR6IbJh7arGj/ADlkQMhmZZiovbvJmYNG9YpkijlP0Vhk5fGshiPb5RQ82sL67k+8kCQznr599ZimD3DGK/XLNIgMCxOP/OqrSxcFfnMdeAjB0hqW6Ic/fNDHlezwfUuVeeoLogDdjlVPd+0EyZ1wKBgQDDY/SCNEWEmrc+F81qcaURxm9NGTRFTUelRlmnkBcVfW91VNB1Q9jTCnEIsAFn/yhZfAZ1/rmqps+WGs+HmlyV1cLEcKzofjQEIbPuFhVX20TMR5yYF460TS0MGR+1defoV8yCqI3IluCoWfV7vOBXNHaI4X/Q6vOL8s+RXQ9t9QKBgB2AYjOmT8ea8KU7DNLita8kFOgis9L2EcoiXrTrrA2HI11S94iBf1PkcvMU+9VK2min+J90VcYYL9nnMdNEzEJNfxkMMGpQYuQHal1QTIEx4wKGBIOwZzwplVk36Mc6R5NjifBMrA98CleoDZIv+Koh1AZfiizSaWEF0NYXZbO5AoGAfNYQEmBzShXPncx3YdraLFEsK4Y+70hAzkf0YCqflQtfeweFaGbA0ZWKQpKxU1Ci5wlm11y4I2AQoUbf8TOek9zPY9LZpnF7qmgeHa/eUxO1EQ9v7XyfoHLupRwoNjfuw3PVJmWqsKffgbB4N2alrxHF6g6pK0Hx+ShZlfZvNUECgYAUbMfOwp2JzY4fDa7XQQJJt4jjlt1QCFRpjT7Vzgw5hafWmCd5U0wTDSFj+bm5Fbjgi7FMJozXnc+CJzC0Q6+27wFB7G0wwrgeASi0uwDFm/1gN7jPPy0LQDogUvO8RlKRMP+xRD5QZl7yyXalm3j8u5hq+b3LbwGqIT+3NtCRQQ=="

    # 鍵を正しい形式（64文字区切り）に復元
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_key_base64), 64):
        formatted_key += clean_key_base64[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"

    # 認証情報の辞書を作成
    sa_info = {
