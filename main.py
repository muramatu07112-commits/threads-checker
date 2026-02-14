def check_threads_stealth(username, proxy_input):
    # Threadsが正規ブラウザと認識するための必須ID
    THREADS_APP_ID = "238280553337440"
    
    session = requests.Session() # クッキーを保持するセッションを作成
    url = f"https://www.threads.net/@{username}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "X-IG-App-ID": THREADS_APP_ID, # これが生存率を上げます
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1"
    }
    
    proxies = {"http": f"http://{proxy_input}", "https": f"http://{proxy_input}"} if proxy_input else None

    try:
        # 1. まずトップページを「偵察」してクッキーを拾う（これが重要）
        session.get("https://www.threads.net/", headers=headers, proxies=proxies, timeout=10)
        
        # 2. 本番のプロフィール確認
        resp = session.get(url, headers=headers, proxies=proxies, timeout=15)
        content = resp.text.lower()
        
        if f"@{username.lower()}" in content:
            return "生存", True
        if "login" in content:
            # 住宅プロキシでこれが出るなら「ゆらぎ」を15秒以上に設定してください
            return "判定不能（Meta遮断中）", False
        return "存在しない（凍結/削除）", True
    except:
        return "通信失敗", False
