import streamlit as st
import re
import base64
from google.oauth2.service_account import Credentials

def get_ultra_sanitized_credentials(raw_pk, client_email, project_id):
    """
    ASN.1の整合性を保つための超精密洗浄
    """
    # 1. 物理的な欠損チェック
    if "-----BEGIN PRIVATE KEY-----" not in raw_pk:
        # ヘッダーがない場合は、単なるBase64文字列として処理
        clean_pk = re.sub(r'[^a-zA-Z0-9+/]', '', raw_pk)
    else:
        # ヘッダー/フッターがある場合は、その間だけを抽出
        matches = re.findall(r'-----BEGIN PRIVATE KEY-----(.*?)-----END PRIVATE KEY-----', raw_pk, re.DOTALL)
        if matches:
            clean_pk = re.sub(r'[^a-zA-Z0-9+/]', '', matches[0])
        else:
            clean_pk = re.sub(r'[^a-zA-Z0-9+/]', '', raw_pk)

    # 2. パディングの数学的補正
    while len(clean_pk) % 4 != 0:
        clean_pk += '='

    # 3. 診断（重要）：現在の文字数を出力
    # 標準的なGoogle秘密鍵(RSA 2048)は約1600〜1700文字程度です
    st.write(f"🔧 診断情報: 洗浄後のBase64文字数 = {len(clean_pk)}")
    
    # 4. PEM再構築
    formatted_pk = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(clean_pk), 64):
        formatted_pk += clean_pk[i:i+64] + "\n"
    formatted_pk += "-----END PRIVATE KEY-----\n"

    info = {
        "type": "service_account",
        "project_id": project_id,
        "private_key": formatted_pk.replace('\\n', '\n'), # エスケープの強制置換
        "client_email": client_email,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return Credentials.from_service_account_info(info)

# --- 実行部分 ---
# RAW_PRIVATE_KEY には、JSONファイル内の "private_key" の値（-----BEGIN...から...END-----\nまで）
# を、前後のダブルクォーテーションを除いてそのまま貼り付けてください。
