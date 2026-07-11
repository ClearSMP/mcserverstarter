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
import selenium_stealth
from webdriver_manager.chrome import ChromeDriverManager

EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SITE_URL = "https://accounts.seedloaf.com/sign-in"
SESSION_DIR = "/tmp/seedloaf-session"

os.makedirs(SESSION_DIR, exist_ok=True)

def get_chrome_options():
    options = Options()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    return options

def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=get_chrome_options())
    selenium_stealth.stealth(driver, languages=["ja-JP", "ja"])
    return driver

# (get_latest_verification_code and main function remain the same as previous version)
# ... (前の完全版の get_latest_verification_code と main をそのまま使ってください)

def main():
    driver = None
    try:
        print("🚀 ログイン開始 (webdriver-manager使用)")
        driver = init_driver()
        wait = WebDriverWait(driver, 20)
        
        driver.get(SITE_URL)
        print("ページロード完了")
        
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.clear()
        email_field.send_keys(EMAIL)
        print("メール入力完了")
        
        continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]")))
        continue_btn.click()
        print("Continueクリック")
        
        time.sleep(10)
        
        code = get_latest_verification_code()
        if not code:
            raise Exception("コード取得失敗")
        print(f"コード: {code}")
        
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        for i, d in enumerate(code):
            if i < len(inputs):
                inputs[i].send_keys(d)
        print("6桁入力完了")
        
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]")))
        final_btn.click()
        print("✅ ログイン成功！")
        
        with open(f"{SESSION_DIR}/.valid_session", "w") as f:
            f.write("valid")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
