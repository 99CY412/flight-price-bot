import os
import requests
from datetime import datetime
from fast_flights import FlightData, Passengers, get_flights, Result

# Secrets from GitHub
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

# Round-trip search setup
flight_data = [
    FlightData(
        date="2026-03-20",
        from_airport="HKG",
        to_airport="TPE"
    ),
    FlightData(
        date="2026-03-22",
        from_airport="TPE",
        to_airport="HKG"
    )
]

try:
    result: Result = get_flights(
        flight_data=flight_data,
        trip="round-trip",
        seat="economy",
        passengers=Passengers(adults=1),
        fetch_mode="fallback"  # Use fallback if direct fails
    )
except Exception as e:
    result = None
    error_msg = str(e)

hx_total = "暫無數據"
hx_details = "無匹配 HX252/HX261"
uo_total = "暫無數據"
uo_details = "無匹配 UO110/UO115"

if result and result.trips:
    for trip in result.trips:
        if not trip.legs or len(trip.legs) != 2:
            continue
        leg1 = trip.legs[0]  # outbound
        leg2 = trip.legs[1]  # return
        airline1 = leg1.airline.code if hasattr(leg1, 'airline') else ""
        airline2 = leg2.airline.code if hasattr(leg2, 'airline') else ""
        price = trip.price.amount if trip.price else "未知"

        # Check for HX
        if airline1 == "HX" and airline2 == "HX":
            fn1 = leg1.flight_number if hasattr(leg1, 'flight_number') else ""
            fn2 = leg2.flight_number if hasattr(leg2, 'flight_number') else ""
            if "252" in fn1 and "261" in fn2:
                hx_total = f"HKD {price}"
                hx_details = f"- HX252 (去程): {leg1.departure_time} HKG → {leg1.arrival_time} TPE\n- HX261 (回程): {leg2.departure_time} TPE → {leg2.arrival_time} HKG"
            else:
                # Fallback cheapest HX
                if hx_total == "暫無數據" or price < float(hx_total.replace("HKD ", "")):
                    hx_total = f"HKD {price}"
                    hx_details = "最平 HX nonstop 選項（可能非指定航班）"

        # Check for UO
        if airline1 == "UO" and airline2 == "UO":
            fn1 = leg1.flight_number if hasattr(leg1, 'flight_number') else ""
            fn2 = leg2.flight_number if hasattr(leg2, 'flight_number') else ""
            if "110" in fn1 and "115" in fn2:
                uo_total = f"HKD {price}"
                uo_details = f"- UO110 (去程): {leg1.departure_time} HKG → {leg1.arrival_time} TPE\n- UO115 (回程): {leg2.departure_time} TPE → {leg2.arrival_time} HKG"
            else:
                if uo_total == "暫無數據" or price < float(uo_total.replace("HKD ", "")):
                    uo_total = f"HKD {price}"
                    uo_details = "最平 UO nonstop 選項（可能非指定航班）"

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20 出發 / 03-22 返程\n經濟艙 單人來回總價\n\n"

msg += "<b>香港航空 (超值飛)：</b>\n" + hx_details + "\n- 單人來回總價: " + hx_total + "\n\n"
msg += "<b>香港快運 (隨心飛)：</b>\n" + uo_details + "\n- 單人來回總價: " + uo_total + "\n\n"

msg += "數據來自 Google Flights scrape (fast-flights library)，實際以官網為準。時間為預定，可能有變。"

if result is None:
    msg += f"\n\n錯誤: {error_msg}"

send_msg(msg)
