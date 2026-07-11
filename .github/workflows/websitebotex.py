import os
import time
import re
import imaplib
import email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import selenium_stealth

# ========================= CONFIG =========================
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SITE_URL = "https://seedloaf.com"   # ← 必要なら変更
HEADLESS = True
SESSION_DIR = "/tmp/seedloaf-session"

os.makedirs(SESSION_DIR, exist_ok=True)
# =========================================================

def get_chrome_options():
    options = Options()
    
    if HEADLESS:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    
    # ユーザーエージェント偽装
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # セッション保存
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    
    return options

def init_driver():
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=get_chrome_options())
    
    # Stealth対策
    selenium_stealth.stealth(driver,
        languages=["ja-JP", "ja"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    driver.set_page_load_timeout(30)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def get_latest_verification_code():
    """Outlookから最新の認証コードを取得"""
    try:
        mail = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        mail.login(EMAIL, EMAIL_PASSWORD)
        mail.select("INBOX")
        
        _, data = mail.search(None, 'FROM "seedloaf" SINCE "1d"')
        email_ids = data[0].split()
        
        if not email_ids:
            print("seedloafからのメールが見つかりません")
            return None
            
        latest_id = email_ids[-1]
        _, msg_data = mail.fetch(latest_id, "(RFC822)")
        
        msg = email.message_from_bytes(msg_data[0][1])
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        
        code_match = re.search(r'\b(\d{6})\b', body)
        if code_match:
            code = code_match.group(1)
            print(f"✅ 認証コードを取得しました: {code}")
            return code
        return None
        
    except Exception as e:
        print(f"IMAPエラー: {e}")
        return None
    finally:
        try:
            mail.logout()
        except:
            pass

def main():
    driver = None
    try:
        print("🚀 Selenium起動中... (Stealthモード)")
        driver = init_driver()
        wait = WebDriverWait(driver, 20)
        
        driver.get(f"{SITE_URL}/login")
        print("ログインページにアクセスしました")
        
        # メール入力
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))  # 必要ならCSS_SELECTORなどに変更
        email_field.clear()
        email_field.send_keys(EMAIL)
        
        # コード送信ボタン
        send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Send') or contains(., 'コード') or contains(., '送信')]")))
        send_btn.click()
        print("認証コードを送信しました")
        
        time.sleep(8)  # メール到着待ち
        
        # 認証コード取得
        code = get_latest_verification_code()
        if not code:
            raise Exception("認証コードの取得に失敗しました")
        
        # コード入力
        code_field = wait.until(EC.presence_of_element_located((By.NAME, "code")))
        code_field.clear()
        code_field.send_keys(code)
        
        # 送信
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Verify') or contains(., '確認') or contains(., 'ログイン')]")))
        submit_btn.click()
        
        print("✅ ログイン成功！")
        
        # ここにMinecraftサーバー起動などの処理を追加してください
        time.sleep(10)
        
        # セッション有効フラグ
        with open(f"{SESSION_DIR}/.valid_session", "w") as f:
            f.write("valid")
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        if driver:
            driver.save_screenshot(f"{SESSION_DIR}/error.png")
            print("エラー時のスクリーンショットを保存しました")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
