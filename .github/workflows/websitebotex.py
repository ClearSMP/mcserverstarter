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


print("EMAIL:", EMAIL)
print(
    "PASSWORD LENGTH:",
    len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 0
)


SITE_URL = "https://accounts.seedloaf.com/sign-in"
SESSION_DIR = "/tmp/seedloaf-session"


os.makedirs(
    SESSION_DIR,
    exist_ok=True
)



def get_chrome_options():

    options = Options()

    options.binary_location = "/usr/bin/google-chrome"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument(
        "--window-size=1920,1080"
    )

    options.add_argument(
        "--lang=ja-JP"
    )

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_argument(
        f"--user-data-dir={SESSION_DIR}"
    )

    options.add_experimental_option(
        "excludeSwitches",
        [
            "enable-automation"
        ]
    )

    return options




def init_driver():

    print(
        "Chrome起動"
    )

    driver = webdriver.Chrome(
        options=get_chrome_options()
    )


    selenium_stealth.stealth(
        driver,
        languages=[
            "ja-JP",
            "ja"
        ],
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


        print(
            "debug保存完了"
        )


    except Exception as e:

        print(
            "debug保存失敗",
            e
        )




def wait_page(driver):

    print(
        "⏳ ページ確認"
    )


    for i in range(30):

        print(
            f"{i+1}/30",
            driver.title
        )


        if (
            "しばらくお待ちください"
            not in driver.title
        ):

            print(
                "ページOK"
            )

            return


        time.sleep(5)



    raise Exception(
        "ページロードタイムアウト"
    )




def find_email(driver):

    selectors = [

        "input[type='email']",

        "input[name='email']",

        "input[placeholder*='email']",

        "input[type='text']"

    ]


    for s in selectors:

        try:

            el = WebDriverWait(
                driver,
                15
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        s
                    )
                )
            )


            print(
                "入力欄:",
                s
            )


            return el


        except:

            pass



    raise Exception(
        "メール入力欄なし"
    )




def get_latest_verification_code(timeout=120):

    print(
        "📧 Outlook確認開始"
    )


    start=time.time()


    while time.time()-start < timeout:

        try:

            mail = imaplib.IMAP4_SSL(
                "imap-mail.outlook.com",
                993
            )


            mail.login(
                EMAIL,
                EMAIL_PASSWORD
            )


            print(
                "Outlook IMAPログイン成功"
            )


            mail.select(
                "INBOX"
            )


            status, data = mail.search(
                None,
                "ALL"
            )


            if status != "OK":

                mail.logout()

                time.sleep(5)

                continue



            ids = data[0].split()


            for msg_id in reversed(
                ids[-30:]
            ):


                status, msg_data = mail.fetch(
                    msg_id,
                    "(RFC822)"
                )


                if status != "OK":

                    continue



                msg = email.message_from_bytes(
                    msg_data[0][1]
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



                code = re.search(
                    r"\b\d{6}\b",
                    body
                )


                if code:

                    mail.logout()

                    print(
                        "認証コード:",
                        code.group(0)
                    )


                    return code.group(0)



            mail.logout()



        except imaplib.IMAP4.error as e:

            print(
                "IMAP認証エラー:",
                e
            )

            raise Exception(
                "Outlook IMAP認証失敗。アプリパスワード確認"
            )



        except Exception as e:

            print(
                "メール確認:",
                e
            )



        time.sleep(5)



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


        wait_page(
            driver
        )


        field=find_email(
            driver
        )


        field.send_keys(
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
                "認証コード取得失敗"
            )



        print(
            "コード取得成功:",
            code
        )



        inputs=driver.find_elements(
            By.CSS_SELECTOR,
            "input[type='text']"
        )


        for i,c in enumerate(code):

            if i < len(inputs):

                inputs[i].send_keys(
                    c
                )



        print(
            "6桁入力完了"
        )



        final=WebDriverWait(
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


        final.click()



        print(
            "✅ ログイン完了"
        )



    except Exception as e:

        print(
            "❌ ERROR:",
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
