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

EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SITE_URL = "https://accounts.seedloaf.com/sign-in"
SESSION_DIR = "/tmp/seedloaf-session"

os.makedirs(SESSION_DIR, exist_ok=True)

def get_chrome_options():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    return options

def init_driver():
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=get_chrome_options())
    selenium_stealth.stealth(driver, languages=["ja-JP", "ja"])
    return driver

def save_debug_info(driver, step):
    driver.save_screenshot(f"{SESSION_DIR}/{step}_screenshot.png")
    with open(f"{SESSION_DIR}/{step}_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"📸 デバッグ情報保存: {step}")

def get_latest_verification_code():
    try:
        mail = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        mail.login(EMAIL, EMAIL_PASSWORD)
        mail.select("INBOX")
        _, data = mail.search(None, 'FROM "seedloaf" SINCE "1d"')
        if data[0]:
            _, msg_data = mail.fetch(data[0].split()[-1], "(RFC822)")
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
                return code_match.group(1)
    except:
        pass
    return None

def main():
    driver = None
    try:
        print("🚀 ログイン開始")
        driver = init_driver()
        wait = WebDriverWait(driver, 20)
        
        driver.get(SITE_URL)
        print("ページロード完了")
        save_debug_info(driver, "1_after_load")
        
        # Email入力
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.clear()
        email_field.send_keys(EMAIL)
        print("メール入力完了")
        save_debug_info(driver, "2_after_email")
        
        # Continue
        continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]")))
        continue_btn.click()
        print("Continueクリック")
        save_debug_info(driver, "3_after_continue")
        
        time.sleep(10)
        
        code = get_latest_verification_code()
        if not code:
            raise Exception("コード取得失敗")
        print(f"コード取得: {code}")
        
        # 6桁入力
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        for i, d in enumerate(code):
            if i < len(inputs):
                inputs[i].send_keys(d)
        print("コード入力完了")
        save_debug_info(driver, "4_after_code")
        
        # 最終Continue
        final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]")))
        final_btn.click()
        print("✅ ログイン成功！")
        
        with open(f"{SESSION_DIR}/.valid_session", "w") as f:
            f.write("valid")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        if driver:
            save_debug_info(driver, "ERROR")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
