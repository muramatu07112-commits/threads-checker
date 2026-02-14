# --- 修正版：リクエストを最小化した判定エンジン ---
def check_threads_simple_v3(username, proxy_input):
    url = f"https://www.threads.net/@{username}"
    proxies = {"http": f"http://{proxy_input}", "https": f"http://{proxy_input}"} if proxy_input else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "X-IG-App-ID": "238280553337440",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    try:
        # 余計なトップページ訪問を廃止し、直接アクセス
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        
        # 404なら即座に「存在しない」
        if resp.status_code == 404:
            return "存在しない（凍結/削除）", True
            
        content = resp.text.lower()
        if f"@{username.lower()}" in content:
            return "生存", True
        if "login" in content:
            return "判定不能（Meta遮断中）", False
            
        return "存在しない（凍結/削除）", True
    except:
        return "通信失敗", False
