import os
import time
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium_stealth

# ========================= CONFIG =========================
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SITE_URL = "https://accounts.seedloaf.com/sign-in"
SESSION_DIR = "/tmp/seedloaf-session"
# =========================================================

def kill_chrome():
    os.system("pkill -9 chrome 2>/dev/null || true")
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
            try:
                proc.terminate()
            except:
                pass
    print("Chromeプロセスを終了しました")

def get_chrome_options():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={SESSION_DIR}")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return options

def main():
    kill_chrome()
    
    driver = None
    try:
        print("🛑 サーバー停止処理開始...")
        driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=get_chrome_options())
        selenium_stealth.stealth(driver, languages=["ja-JP", "ja"])
        
        driver.get(SITE_URL)
        wait = WebDriverWait(driver, 20)
        
        # ログイン（簡易版 - セッションが残っていればスキップされる可能性あり）
        try:
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_field.send_keys(EMAIL)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]"))).click()
            time.sleep(8)
            
            # コード入力は省略（セッションが有効なら不要な場合が多い）
        except:
            print("ログインセッションが残っている可能性があります")
        
        # 停止ボタンクリック
        try:
            stop_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-error') or contains(., 'Stop')]")))
            driver.execute_script("arguments[0].scrollIntoView(true);", stop_btn)
            stop_btn.click()
            print("🛑 停止ボタンをクリックしました")
            time.sleep(5)
        except:
            print("停止ボタンが見つかりませんでした（すでに停止している可能性）")
        
        print("✅ 停止処理完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        if driver:
            driver.quit()
        kill_chrome()

if __name__ == "__main__":
    main()
