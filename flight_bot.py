import os
import requests
from datetime import datetime
from fast_flights import FlightData, Passengers, get_flights, Result

# Secrets
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

# Setup round-trip search
flight_data = [
    FlightData(date="2026-03-20", from_airport="HKG", to_airport="TPE"),
    FlightData(date="2026-03-22", from_airport="TPE", to_airport="HKG")
]

hx_total = "暫無數據"
hx_details = "無匹配 HX252/HX261"
uo_total = "暫無數據"
uo_details = "無匹配 UO110/UO115"

try:
    result: Result = get_flights(
        flight_data=flight_data,
        trip="round-trip",
        seat="economy",
        passengers=Passengers(adults=1),
        fetch_mode="fallback"  # 推薦用 fallback 模式
    )

    if result and result.flights:
        # 迭代所有 flights (每個是 round-trip 行程)
        for flight in result.flights:
            price_str = flight.price if hasattr(flight, 'price') else "未知"
            # flight.name 可能如 "Hong Kong Airlines HX252 · 2h 45m" 或類似
            name = flight.name if hasattr(flight, 'name') else ""
            departure_time = flight.departure if hasattr(flight, 'departure') else "未知"
            arrival_time = flight.arrival if hasattr(flight, 'arrival') else "未知"

            # 簡單 parse name 找 flight number (e.g. "HX252", "UO110")
            if "HX252" in name and "HX261" in name:  # 假設 name 包含兩個 flight number
                hx_total = price_str
                hx_details = f"- HX252 (去程): {departure_time} HKG → ... TPE\n- HX261 (回程): ... TPE → {arrival_time} HKG"
            elif "UO110" in name and "UO115" in name:
                uo_total = price_str
                uo_details = f"- UO110 (去程): {departure_time} HKG → ... TPE\n- UO115 (回程): ... TPE → {arrival_time} HKG"
            else:
                # fallback: 找 HX 或 UO 相關 name 的最平價
                if "HX" in name and (hx_total == "暫無數據" or price_str < hx_total):
                    hx_total = price_str
                    hx_details = "最平 HX nonstop 選項（可能非指定航班）"
                if "UO" in name and (uo_total == "暫無數據" or price_str < uo_total):
                    uo_total = price_str
                    uo_details = "最平 UO nonstop 選項（可能非指定航班）"

except Exception as e:
    hx_details = uo_details = f"查詢失敗: {str(e)}"

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20 出發 / 03-22 返程\n經濟艙 單人來回總價\n\n"

msg += "<b>香港航空 (超值飛)：</b>\n" + hx_details + "\n- 單人來回總價: " + hx_total + "\n\n"
msg += "<b>香港快運 (隨心飛)：</b>\n" + uo_details + "\n- 單人來回總價: " + uo_total + "\n\n"

msg += "數據來自 Google Flights scrape (fast-flights)，實際以官網為準。時間為預定，可能有變。"

send_msg(msg)
