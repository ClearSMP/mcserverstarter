import os
import time
import re
import imaplib
import email

from selenium import webdriver
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

    options.binary_location = "/usr/bin/google-chrome"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--lang=ja-JP")

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_argument(
        "--user-agent="
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )

    options.add_argument(
        f"--user-data-dir={SESSION_DIR}"
    )

    return options



def init_driver():

    driver = webdriver.Chrome(
        options=get_chrome_options()
    )

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



def save_debug(driver):

    try:

        driver.save_screenshot(
            "error.png"
        )

        with open(
            "page.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                driver.page_source
            )

        print(
            "debug保存完了"
        )

    except Exception as e:

        print(
            "debug保存失敗:",
            e
        )



def wait_page_ready(driver):

    print(
        "⏳ ページ待機開始"
    )

    for i in range(60):

        title = driver.title

        print(
            f"{i+1}/60:",
            title
        )

        if (
            "しばらくお待ちください" not in title
            and
            "Just a moment" not in title
        ):
            print(
                "ページ切替確認"
            )
            return


        time.sleep(2)


    raise Exception(
        "ページ待機タイムアウト"
    )



def find_email_input(driver):

    selectors = [

        "input[type='email']",

        "input[name='email']",

        "input[placeholder*='Email']",

        "input[placeholder*='email']",

        "input[type='text']"

    ]


    for selector in selectors:

        try:

            element = WebDriverWait(
                driver,
                10
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        selector
                    )
                )
            )

            print(
                "入力欄発見:",
                selector
            )

            return element

        except:

            pass


    raise Exception(
        "メール入力欄が見つかりません"
    )



def get_latest_verification_code(timeout=120):

    start = time.time()


    while time.time() - start < timeout:

        try:

            mail = imaplib.IMAP4_SSL(
            "outlook.office365.com",
            993
)

            mail.login(
                EMAIL,
                EMAIL_PASSWORD
            )

            mail.select(
                "inbox"
            )


            _, messages = mail.search(
                None,
                "ALL"
            )


            for msg_id in reversed(
                messages[0].split()[-20:]
            ):

                _, data = mail.fetch(
                    msg_id,
                    "(RFC822)"
                )


                msg = email.message_from_bytes(
                    data[0][1]
                )


                body = ""


                if msg.is_multipart():

                    for part in msg.walk():

                        if part.get_content_type() == "text/plain":

                            body += part.get_payload(
                                decode=True
                            ).decode(
                                errors="ignore"
                            )

                else:

                    body = msg.get_payload(
                        decode=True
                    ).decode(
                        errors="ignore"
                    )


                result = re.search(
                    r"\b\d{6}\b",
                    body
                )


                if result:

                    mail.logout()

                    return result.group(0)


            mail.logout()


        except Exception as e:

            print(
                "メール確認:",
                e
            )


        time.sleep(5)


    return None



def main():

    driver = None


    try:

        print(
            "🚀 ログイン開始"
        )


        driver = init_driver()


        driver.get(
            SITE_URL
        )


        print(
            "URL:",
            driver.current_url
        )

        print(
            "TITLE:",
            driver.title
        )


        wait_page_ready(
            driver
        )


        email_field = find_email_input(
            driver
        )


        email_field.send_keys(
            EMAIL
        )


        print(
            "メール入力完了"
        )


        continue_btn = WebDriverWait(
            driver,
            20
        ).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(.,'Continue')]"
                )
            )
        )


        continue_btn.click()


        print(
            "Continueクリック"
        )


        code = get_latest_verification_code()


        if not code:

            raise Exception(
                "認証コード取得失敗"
            )


        print(
            "コード:",
            code
        )


    except Exception as e:

        print(
            "❌ ERROR:",
            type(e).__name__,
            e
        )


        if driver:

            save_debug(
                driver
            )


        raise


    finally:

        if driver:

            save_debug(
                driver
            )

            driver.quit()



if __name__ == "__main__":

    main()
