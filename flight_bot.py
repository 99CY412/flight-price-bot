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

def get_one_way_flights(from_airport, to_airport, date, time_start, time_end):
    flight_data = FlightData(date=date, from_airport=from_airport, to_airport=to_airport)
    try:
        result = get_flights(
            flight_data=[flight_data],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="fallback"
        )
        matching_flights = []
        if result and result.flights:
            for flight in result.flights:
                dep_time = flight.departure if hasattr(flight, 'departure') else ""
                name = flight.name if hasattr(flight, 'name') else ""
                price = flight.price if hasattr(flight, 'price') else "未知"
                # 匹配時間範圍 (e.g. "09:" for 9:xx, "19:" for 19:xx)
                if time_start in dep_time or time_end in dep_time:
                    if "HX" in name:  # 只限香港航空
                        flight_num = name.split()[1] if len(name.split()) > 1 else "未知"  # 假設 name 如 "HX 252"
                        matching_flights.append({
                            "num": flight_num,
                            "time": dep_time,
                            "price": price,
                            "name": name
                        })
        return matching_flights
    except Exception as e:
        return []

# 去程：2026-03-20 HKG→TPE 上午9:05–10:50 (filter "09:" or "10:")
go_flights = get_one_way_flights("HKG", "TPE", "2026-03-20", "09:", "10:")
hx_go_details = "無匹配 9:05–10:50 HX 航班"
hx_go_price = "無數據"
if go_flights:
    # 取第一個匹配的 (或最平的)
    best_go = go_flights[0]
    hx_go_details = f"{best_go['num']} (去程): {best_go['time']} HKG → TPE, 價格 {best_go['price']}"
    hx_go_price = best_go['price']

# 回程：2026-03-22 TPE→HKG 晚上7:20–9:25 (filter "19:" or "20:" or "21:")
ret_flights = get_one_way_flights("TPE", "HKG", "2026-03-22", "19:", "21:")
hx_ret_details = "無匹配 19:20–21:25 HX 航班"
hx_ret_price = "無數據"
if ret_flights:
    best_ret = ret_flights[0]
    hx_ret_details = f"{best_ret['num']} (回程): {best_ret['time']} TPE → HKG, 價格 {best_ret['price']}"
    hx_ret_price = best_ret['price']

# 計算總價
hx_total = "無法計算"
if hx_go_price != "無數據" and hx_ret_price != "無數據":
    try:
        go_num = float(hx_go_price.replace("HKD ", "").replace(",", "").strip())
        ret_num = float(hx_ret_price.replace("HKD ", "").replace(",", "").strip())
        total = go_num + ret_num
        hx_total = f"HKD {total:.0f}"
    except:
        hx_total = "計算錯誤 (價格格式異常)"

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20 出發 / 03-22 返程\n經濟艙 單人來回總價\n\n"

msg += "<b>香港航空 (超值飛)：</b>\n"
msg += f"- {hx_go_details}\n"
msg += f"- {hx_ret_details}\n"
msg += f"- 單人來回總價: {hx_total}\n\n"

msg += "數據來自 Google Flights scrape (fast-flights)，以指定時間範圍搜尋香港航空航班。實際以官網為準。如果無價格，可能 fares 未 release。"

send_msg(msg)
