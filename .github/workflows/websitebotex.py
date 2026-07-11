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


# デバッグ確認（一時用）
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
