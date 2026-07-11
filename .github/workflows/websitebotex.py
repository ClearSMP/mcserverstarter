import os
import time
import re
import imaplib
import email

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import selenium_stealth

EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SITE_URL = "https://accounts.seedloaf.com/sign-in"
SESSION_DIR = "/tmp/seedloaf-session"

os.makedirs(SESSION_DIR, exist_ok=True)


def get_chrome_options():
    options = Options()

    # GitHub ActionsでインストールしたChrome
    options.binary_location = "/usr/bin/google-chrome"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )

    options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    options.add_argument(f"--user-data-dir={SESSION_DIR}")

    return options


def init_driver():
    # Selenium Manager が自動でChromeDriverを管理
    driver = webdriver.Chrome(options=get_chrome_options())

    selenium_stealth.stealth(
        driver,
        languages=["ja-JP", "ja"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL",
        fix_hairline=True,
    )

    return driver


def get_latest_verification_code(timeout=120):
    """
    Gmailから最新の6桁認証コードを取得
    """
    start = time.time()

    while time.time() - start < timeout:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL, EMAIL_PASSWORD)
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")

            if status != "OK":
                time.sleep(5)
                continue

            ids = messages[0].split()

            for msg_id in reversed(ids[-10:]):
                status, msg_data = mail.fetch(msg_id, "(RFC822)")

                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_payload(decode=True).decode(
                                errors="ignore"
                            )
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                match = re.search(r"\b(\d{6})\b", body)

                if match:
                    mail.logout()
                    return match.group(1)

            mail.logout()

        except Exception as e:
            print(f"メール取得エラー: {e}")

        time.sleep(5)

    return None


def main():
    driver = None

    try:
        print("🚀 ログイン開始 (Selenium Manager)")

        driver = init_driver()
        wait = WebDriverWait(driver, 20)

        driver.get(SITE_URL)
        print("ページロード完了")

        email_field = wait.until(
            EC.presence_of_element_located((By.NAME, "email"))
        )

        email_field.clear()
        email_field.send_keys(EMAIL)
        print("メール入力完了")

        continue_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Continue')]")
            )
        )

        continue_btn.click()
        print("Continueクリック")

        print("認証コード待機...")
        code = get_latest_verification_code()

        if not code:
            raise Exception("認証コード取得失敗")

        print(f"取得コード: {code}")

        inputs = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "input[type='text']")
            )
        )

        for i, digit in enumerate(code):
            if i < len(inputs):
                inputs[i].send_keys(digit)

        print("6桁コード入力完了")

        final_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Continue')]")
            )
        )

        final_btn.click()

        print("✅ ログイン成功")

        with open(f"{SESSION_DIR}/.valid_session", "w") as f:
            f.write("valid")

    except Exception as e:
        print(f"❌ エラー: {e}")

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
