import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

url = "https://www.google.com/travel/flights/booking?tfs=CBwQAhpHEgoyMDI2LTAzLTIwIh8KA0hLRxIKMjAyNi0wMy0yMBoDVFBFKgJIWDIDMjUyMgJVTzICSFhqBwgBEgNIS0dyBwgBEgNUUEUaRxIKMjAyNi0wMy0yMiIfCgNUUEUSCjIwMjYtMDMtMjIaA0hLRyoCSFgyAzI2MTICVU8yAkhYagcIARIDVFBFcgcIARIDSEtHQAFIAXABggELCP___________wGYAQE&tfu=CmxDalJJUlUxc1EzQkdOakU1WW1kQlFuSmlhWGRDUnkwdExTMHRMUzB0TFMxMGJITnVNVUZCUVVGQlIyMUdOMkpWUjJwWlZsRkJFZ1ZJV0RJMk1Sb0tDT0FMRUFBYUEwaExSRGdjY0xHV0FRPT0SAggAIgA&hl=zh-TW&gl=hk&curr=HKD"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")

    # 提取總價格 (e.g. HK$1,449)
    total_price = page.query_selector("div[jsname='IWWDBc']")  # 價格元素 selector，可能需調
    price_text = total_price.inner_text() if total_price else "未抓到價格"

    # 提取去程細節
    outbound = page.query_selector_all("div[jsname='oa3M6e']")[0]  # 去程 block
    outbound_details = outbound.inner_text() if outbound else "無去程資料"

    # 提取回程細節
    return_flight = page.query_selector_all("div[jsname='oa3M6e']")[1]  # 回程 block
    return_details = return_flight.inner_text() if return_flight else "無回程資料"

    browser.close()

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20/22\n經濟艙 單人來回總價\n\n"

msg += f"總價格: {price_text}\n\n"
msg += "去程:\n" + outbound_details + "\n\n"
msg += "回程:\n" + return_details + "\n\n"

msg += "數據直接從 Google Flights 頁面 scrape，實際以官網為準。頁面可能變或需手動驗證。"

send_msg(msg)
