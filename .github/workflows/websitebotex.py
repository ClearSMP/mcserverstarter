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

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_argument(
        "--user-agent="
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
        languages=["ja-JP","ja"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL",
        fix_hairline=True
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

        print("debug保存完了")

    except Exception as e:

        print(
            "debug error:",
            e
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
                5
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        selector
                    )
                )
            )

            print(
                "email input found:",
                selector
            )

            return element


        except:

            pass


    # iframe確認

    frames = driver.find_elements(
        By.TAG_NAME,
        "iframe"
    )

    print(
        "iframe:",
        len(frames)
    )


    for frame in frames:

        driver.switch_to.frame(frame)

        for selector in selectors:

            try:

                element = driver.find_element(
                    By.CSS_SELECTOR,
                    selector
                )

                print(
                    "iframe email found:",
                    selector
                )

                return element


            except:

                pass


        driver.switch_to.default_content()


    raise Exception(
        "email input not found"
    )



def get_latest_verification_code():

    mail = imaplib.IMAP4_SSL(
        "imap.gmail.com"
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
        messages[0].split()
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

                if part.get_content_type()=="text/plain":

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


        code = re.search(
            r"\b\d{6}\b",
            body
        )


        if code:

            mail.logout()

            return code.group(0)


    mail.logout()

    return None



def main():

    driver=None


    try:

        print(
            "🚀 ログイン開始"
        )


        driver=init_driver()


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


        time.sleep(5)


        email_field=find_email_input(
            driver
        )


        email_field.send_keys(
            EMAIL
        )


        print(
            "メール入力完了"
        )


        btn=WebDriverWait(
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


        btn.click()


        print(
            "Continueクリック"
        )


        time.sleep(10)


        code=get_latest_verification_code()


        if not code:

            raise Exception(
                "コード取得失敗"
            )


        print(
            "code:",
            code
        )


    except Exception as e:

        print(
            "ERROR:",
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



if __name__=="__main__":

    main()
