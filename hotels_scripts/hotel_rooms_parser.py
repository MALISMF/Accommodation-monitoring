from playwright.sync_api import sync_playwright
import requests
import csv
import json
import os
import uuid
import time
from typing import Optional
from urllib.parse import urlparse

class OstrovokParserAdvanced:
    def __init__(self):
        self.session = requests.Session()
        self.api_url = "https://ostrovok.ru/hotel/search/v1/site/hp/search"
        self.cookies = None
    
    def get_cookies_from_browser(self):
        """Получение куков через реальный браузер"""
        print("Запуск браузера для получения куков...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            page.goto('https://ostrovok.ru')
            
            # Получаем куки
            cookies = context.cookies()
            self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
            
            browser.close()
            
        print(f"✓ Получено {len(self.cookies)} куков")
        return self.cookies

    def _extract_hotel_id(self, hotel_url: str) -> Optional[str]:
        """Достаем слаг отеля из URL (последний сегмент пути)."""
        try:
            path = urlparse(hotel_url).path.rstrip("/")
            return path.split("/")[-1] if path else None
        except Exception as exc:
            print(f"Не удалось распарсить url {hotel_url}: {exc}")
            return None
    
    def search_hotel(self, hotel_id, checkin_date, checkout_date, adults=1):
        """Поиск с куками из браузера"""
        
        if not self.cookies:
            self.get_cookies_from_browser()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://ostrovok.ru',
            'Referer': 'https://ostrovok.ru/'
        }
        
        payload = {
            "arrival_date": checkin_date,
            "departure_date": checkout_date,
            "hotel": hotel_id,
            "currency": "RUB",
            "lang": "ru",
            "region_id": 965821539,
            "paxes": [{"adults": adults}],
            "search_uuid": str(uuid.uuid4())
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                cookies=self.cookies,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

# Использование
def run_for_hotels_list(
    csv_path: str = "hotels_list.csv",
    checkin_date: str = "2026-01-24",
    checkout_date: str = "2026-01-25",
    out_dir: str = "json",
):
    parser = OstrovokParserAdvanced()
    parser.get_cookies_from_browser()

    os.makedirs(out_dir, exist_ok=True)

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            hotel_url = row.get("show_rooms_url") or row.get("detail_url")
            hotel_name = row.get("hotel_name") or "unknown"
            hotel_id = parser._extract_hotel_id(hotel_url) if hotel_url else None

            if not hotel_id:
                print(f"✗ Пропускаю {hotel_name}: не найден hotel_id")
                continue

            print(f"→ Запрашиваю {hotel_name} ({hotel_id})")
            result = parser.search_hotel(hotel_id, checkin_date, checkout_date)

            if not result:
                print(f"✗ Нет данных для {hotel_name}")
                continue

            out_path = os.path.join(out_dir, f"{hotel_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✓ Сохранено {out_path}")


if __name__ == "__main__":
    run_for_hotels_list()
