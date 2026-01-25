from playwright.sync_api import sync_playwright
import time
import sys
import json
import csv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Настройка stdout для корректного вывода Юникода
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class OstrovokHotelsParser:
    def __init__(self):
        self.api_url = "https://ostrovok.ru/hotel/search/v1/site/hp/search"
        self.all_hotels = []
        self.current_page = 1
        self.base_url = "https://ostrovok.ru/hotel/russia/western_siberia_irkutsk_oblast_multi/?type_group=hotel"
    
    def get_all_hotels_list(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # --- Переходим на страницу с отелями ---
            page.goto(self.base_url)
            page.wait_for_selector('body', timeout=10000) # Ждем загрузки страницы

            # --- Закрываем попапы ---
            self.close_popup(page)

            # Ждём появления карточек на первой странице
            page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
            time.sleep(2)

            self.paginate_and_extract_all_hotels(page)


            # --- Сохраняем данные в CSV ---
            with open('hotels_list.csv', 'w', encoding='utf-8-sig', newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                writer.writerow([
                    'hotel_name', 
                    'address', 
                    'url', 
                    'show_rooms_url', 
                    'price', 
                    'rating', 
                    'rating_category', 
                    'reviews_count'
                ])
                for hotel in self.all_hotels:
                    writer.writerow([
                        hotel.get('name', ''), 
                        hotel.get('address', ''),
                        hotel.get('url', ''),
                        hotel.get('show_rooms_url', ''),
                        hotel.get('price', ''),
                        hotel.get('rating', ''),
                        hotel.get('rating_category', ''),
                        hotel.get('reviews_count', '')
                    ])
            
            print(f"Сохранено {len(self.all_hotels)} отелей в hotels_list.csv")
            
        browser.close()
        return self.all_hotels
            

    def close_popup(self, page):
        try:
            btn = page.locator('button[aria-label*="close"]').first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_selector('body', timeout=10000)
        except Exception as e:
            print(f"Error closing popup: {e}")
            return False
        return True
    
    def get_hotel_cards(self, page):
        hotels = []
        try:
            page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
            
            hotel_cards = page.query_selector_all('[data-testid="serp-hotelcard"]')

            for card in hotel_cards:
                try:
                    hotel_data = {}

                    # Название отеля и ссылка на страницу
                    hotel_data['name'] = card.query_selector('a[data-testid="hotel-card-name"]').inner_text().strip()
                    hotel_data['href'] = card.query_selector('a[data-testid="hotel-card-name"]').get_attribute('href')

                    # Полная ссылка на страницу отеля
                    hotel_data['url'] = f"https://ostrovok.ru{hotel_data['href']}"

                    # Ссылка "Показать все номера"
                    hotel_data['show_rooms_url'] = card.query_selector('a[data-testid="next-step-button"]').get_attribute('href')

                    # Адрес отеля
                    hotel_data['address'] = card.query_selector('[data-testid="hotel-card-distance-address"]').inner_text().strip() 

                    # Минимальная цена за ночь и валюта
                    price_value_el = card.query_selector('[data-testid="hotel-card-price-value"]').inner_text().strip()
                    price_desc_el = card.query_selector('[data-testid="hotel-card-rate-description"]').inner_text().strip()
                    price_value = price_value_el.replace('\u202f', '').replace('\xa0', '').strip()
                    hotel_data['price'] = f"{price_value} {price_desc_el}"
                    
                    # Оценка по отзывам (число)
                    hotel_data['rating'] = card.query_selector('[data-testid="hotel-card-rating-content"]').inner_text().strip()
                    hotel_data['rating'] = hotel_data['rating'].replace(',', '.')

                    # Текстовая категория оценки
                    hotel_data['rating_category'] = card.query_selector('.HotelRating_ratingCategory__cNoZe').inner_text().strip()

                    # Количество отзывов
                    hotel_data['reviews_count'] = card.query_selector('.HotelRating_reviewsCount__3YYVd').inner_text().strip()
                    
                    hotels.append(hotel_data)

                except Exception as e:
                    print(f"Error getting hotel data: {e}")
                    continue

        except Exception as e:
            print(f"Error getting hotel cards: {e}")
            return hotels
        
        return hotels

    def goto_page(self, page, page_number):
        current_url = page.url
        parsed = urlparse(current_url)
        qs = parse_qs(parsed.query)
        qs["page"] = [str(page_number)]
        new_query = urlencode(qs, doseq=True)
        new_url = urlunparse(parsed._replace(query=new_query))
        
        print(f"Navigating to page {page_number}: {new_url}")
        try:
            page.goto(new_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(1)
        except Exception as e:
            print(f"Error navigating to page {page_number}: {e}")
            raise

    def paginate_and_extract_all_hotels(self, page):
        # Собираем отели на первой странице
        hotels = self.get_hotel_cards(page)
        if hotels:
            self.all_hotels.extend(hotels)
            print(f"Extracted {len(hotels)} hotels on page 1.")
        
        while True:
            try:
                # Определяем текущую страницу по URL
                url = page.url
                current_page = 1
                if "page=" in url:
                    qs = parse_qs(urlparse(url).query)
                    current_page = int(qs.get("page", ["1"])[0])
                
                next_page = current_page + 1
                print(f"\n--- Page {current_page} ---")
                
                # Проверяем наличие ссылки на следующую страницу
                next_link = page.locator(f'a:has-text("{next_page}")').first
                
                if next_link.count() == 0:
                    print(f"No link for page {next_page} found. Reached last page.")
                    break
                
                # Переходим на следующую страницу
                self.goto_page(page, next_page)
                self.close_popup(page)
                
                # Единоразовая загрузка карточек (scroll + wait)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)
                page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
                time.sleep(1.0)
                
                # Собираем отели на новой странице
                hotels = self.get_hotel_cards(page)
                
                if len(hotels) == 0:
                    print(f"Warning: no hotels found on page {next_page}.")
                    break
                else:
                    self.all_hotels.extend(hotels)
                    print(f"Extracted {len(hotels)} hotels on page {next_page}.")
                
            except Exception as e:
                print(f"Error paginating and extracting hotels: {e}")
                break
        
        print(f"\n=== Total hotels collected from all pages: {len(self.all_hotels)} ===")
        return self.all_hotels
    
if __name__ == "__main__":
    parser = OstrovokHotelsParser()
    parser.get_all_hotels_list()