import os
from datetime import datetime
from fast_flights import FlightData, Passengers, get_flights, Result

# Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

# 設定查詢（round-trip 例子）
flight_data = FlightData(
    origin="HKG",
    destination="TPE",
    date="2026-03-20",  # outbound
    return_date="2026-03-22",
    passengers=Passengers(adults=1),
    # filter: 只 HX (Hong Kong Airlines code HX)
    airlines=["HX"],
)

results: Result = get_flights(flight_data)

hx_total = "無數據"
hx_details = "無匹配 HX252/HX261"

if results.trips:
    for trip in results.trips:
        for leg in trip.legs:
            if leg.flight_number == "252" or leg.flight_number == "261":
                # parse price, time
                price = trip.price.amount if trip.price else "未知"
                time = f"{leg.departure_time} → {leg.arrival_time}"
                hx_details += f"\n- {leg.flight_number}: {time} 價格 HKD {price}"
        if "HX252" in hx_details and "HX261" in hx_details:
            hx_total = f"HKD {trip.price.amount}" if trip.price else "未知"

# UO 同樣加 query (airlines=["UO"])

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回\n"
msg += "<b>香港航空 (超值飛)：</b>\n" + hx_details + "\n- 單人來回總價: " + hx_total + "\n\n"
msg += "數據來自 Google Flights scrape，實際以官網為準。"

send_msg(msg)
