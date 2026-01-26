import json
import csv
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

# Настройка stdout для корректного вывода Юникода
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class TvilHotelsParser:
    def __init__(self):
        self.base_url = "https://tvil.ru/api/entities"
        self.init_url = "https://tvil.ru/city/irkutskaya-oblast/hotels/"
        self.all_hotels = []
        self.offset = 0
        self.limit = 20
        self.current_dir = Path(__file__).parent
        
        # Параметры запроса
        self.params = {
            "page[limit]": str(self.limit),
            "page[offset]": "0",
            "include": "params,child_params,photos_t2,photos_t1,tooltip,services,inflect,characteristics",
            "filter[type]": "hotel",
            "filter[geo]": "251",
            "format[withNearEntities]": "1",
            "format[withBusyEntities]": "1",
            "order[priceFrom]": "0"
        }
    
    def get_all_hotels_list(self):
        """
        Парсит API ТВИЛ, получая отели с пагинацией через Playwright.
        Сохраняет данные в CSV файл.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Инициализация сессии через главную страницу
            print("Инициализация сессии через главную страницу...")
            page = context.new_page()
            page.goto(self.init_url, wait_until="networkidle")
            time.sleep(5)  # Даём время на обработку антибота
            
            # Парсим все страницы
            self._parse_all_pages(page)
            
            browser.close()
        
        # Сохраняем данные в CSV
        self._save_to_csv()
        
        print(f"\nПарсинг завершён. Всего обработано {len(self.all_hotels)} отелей.")
        return self.all_hotels
    
    def _parse_all_pages(self, page):
        """
        Парсит все страницы с отелями через API запросы.
        """
        self.offset = 0
        
        while True:
            try:
                # Обновляем offset в параметрах
                self.params["page[offset]"] = str(self.offset)
                
                # Формируем query string
                query_string = "&".join([f"{k}={v}" for k, v in self.params.items()])
                url = f"{self.base_url}?{query_string}"
                
                print(f"Запрос для offset={self.offset}...")
                
                # Выполняем запрос через JavaScript fetch
                response_data = self._make_api_request(page, url)
                
                if not response_data:
                    print(f"Не удалось получить данные для offset={self.offset}")
                    break
                
                # Извлекаем отели из ответа
                hotels = self._extract_hotels_from_response(response_data)
                
                if not hotels or len(hotels) == 0:
                    print(f"Получен пустой список отелей для offset={self.offset}. Останавливаем парсинг.")
                    break
                
                # Добавляем отели в общий список
                self.all_hotels.extend(hotels)
                print(f"Извлечено {len(hotels)} отелей. Всего: {len(self.all_hotels)}")
                
                # Если получили меньше отелей, чем limit, значит это последняя страница
                if len(hotels) < self.limit:
                    print(f"Получено меньше отелей ({len(hotels)}), чем limit ({self.limit}). Это последняя страница.")
                    break
                
                # Увеличиваем offset для следующей итерации
                self.offset += self.limit
                
                # Небольшая задержка между запросами
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Ошибка при выполнении запроса для offset={self.offset}: {e}")
                break
    
    def _make_api_request(self, page, url):
        """
        Выполняет API запрос через JavaScript fetch в контексте страницы.
        """
        try:
            response_data = page.evaluate("""
                async (url) => {
                    try {
                        const response = await fetch(url, {
                            method: 'GET',
                            credentials: 'same-origin',
                            headers: {
                                'Referer': 'https://tvil.ru/city/irkutskaya-oblast/hotels/'
                            }
                        });
                        const contentType = response.headers.get('content-type') || '';
                        let data;
                        let text;
                        
                        // Пытаемся прочитать как текст сначала
                        text = await response.text();
                        
                        // Пытаемся распарсить как JSON
                        try {
                            data = JSON.parse(text);
                        } catch (e) {
                            // Если не JSON, возвращаем ошибку
                            return {
                                status: response.status,
                                statusText: response.statusText,
                                error: 'Not JSON response',
                                text: text.substring(0, 1000)
                            };
                        }
                        
                        return {
                            status: response.status,
                            statusText: response.statusText,
                            data: data
                        };
                    } catch (error) {
                        return {
                            status: 0,
                            statusText: 'Error',
                            error: error.toString()
                        };
                    }
                }
            """, url)
            
            print(f"Получен ответ со статусом {response_data['status']}")
            
            # Проверяем наличие ошибки
            if 'error' in response_data:
                print(f"Ошибка при выполнении запроса: {response_data['error']}")
                return None
            
            # Проверяем статус ответа
            if response_data['status'] != 200:
                print(f"Ошибка: сервер вернул статус {response_data['status']}")
                return None
            
            return response_data.get('data')
            
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return None
    
    def _extract_hotels_from_response(self, data):
        """
        Извлекает список отелей из ответа API.
        """
        hotels = []
        
        if data is None:
            return hotels
        
        # Проверяем структуру ответа
        if isinstance(data, dict):
            if "data" in data:
                hotels_data = data["data"]
            elif "entities" in data:
                hotels_data = data["entities"]
            else:
                return hotels
        elif isinstance(data, list):
            hotels_data = data
        else:
            return hotels
        
        # Извлекаем информацию об отелях
        for hotel_item in hotels_data:
            try:
                hotel = {}
                
                # Извлекаем данные из структуры API
                if isinstance(hotel_item, dict):
                    # ID отеля
                    hotel['id'] = hotel_item.get('id', '')
                    
                    # Атрибуты
                    attributes = hotel_item.get('attributes', {})
                    
                    hotel['title'] = attributes.get('title', '')
                    hotel['cabinet_title'] = attributes.get('cabinet_title', '')
                    hotel['full_title'] = attributes.get('full_title', '')
                    hotel['list_title'] = attributes.get('list_title', '')
                    hotel['entity_type'] = attributes.get('entity_type', '')
                    hotel['subtype'] = attributes.get('subtype', '')
                    hotel['address'] = attributes.get('address', '')
                    hotel['short_address'] = attributes.get('short_address', '')
                    hotel['full_address'] = attributes.get('full_address', '')
                    hotel['map_address'] = attributes.get('map_address', '')
                    hotel['city_address'] = attributes.get('city_address', '')
                    hotel['latitude'] = attributes.get('latitude', '')
                    hotel['longitude'] = attributes.get('longitude', '')
                    hotel['description'] = attributes.get('description', '')
                    hotel['conditions'] = attributes.get('conditions', '')
                    
                    # Цены
                    price = attributes.get('price', [])
                    if isinstance(price, list) and len(price) >= 2:
                        hotel['price_min'] = price[0]
                        hotel['price_max'] = price[1]
                    else:
                        hotel['price_min'] = ''
                        hotel['price_max'] = ''
                    
                    daily_price = attributes.get('daily_rubles_price', [])
                    if isinstance(daily_price, list) and len(daily_price) >= 2:
                        hotel['daily_price_min'] = daily_price[0]
                        hotel['daily_price_max'] = daily_price[1]
                    else:
                        hotel['daily_price_min'] = ''
                        hotel['daily_price_max'] = ''
                    
                    # Валюта
                    currency = attributes.get('currency', {})
                    hotel['currency_id'] = currency.get('id', '')
                    hotel['currency_title'] = currency.get('title', '')
                    hotel['currency_symbol'] = currency.get('symbol', '')
                    
                    hotel['prepayment'] = attributes.get('prepayment', '')
                    hotel['rooms_total'] = attributes.get('rooms_total', '')
                    hotel['bedroom_total'] = attributes.get('bedroom_total', '')
                    hotel['count_rooms'] = attributes.get('count_rooms', '')
                    hotel['count_reviews'] = attributes.get('count_reviews', '')
                    hotel['count_real_reviews'] = attributes.get('count_real_reviews', '')
                    hotel['rating_overall'] = attributes.get('rating_overall', '')
                    hotel['entity_rating'] = attributes.get('entity_rating', '')
                    hotel['total_rating'] = attributes.get('total_rating', '')
                    hotel['user_rating'] = attributes.get('user_rating', '')
                    hotel['stars'] = attributes.get('stars', '')
                    hotel['country_id'] = attributes.get('country_id', '')
                    hotel['region_id'] = attributes.get('region_id', '')
                    hotel['city_id'] = attributes.get('city_id', '')
                    hotel['aria_id'] = attributes.get('aria_id', '')
                    hotel['count_photos'] = attributes.get('count_photos', '')
                    hotel['count_guest'] = attributes.get('count_guest', '')
                    hotel['count_guest_max'] = attributes.get('count_guest_max', '')
                    hotel['categories_count'] = attributes.get('categories_count', '')
                    hotel['occupied_categories'] = attributes.get('occupied_categories', '')
                    hotel['last_reserve'] = attributes.get('last_reserve', '')
                    hotel['last_reserve_label'] = attributes.get('last_reserve_label', '')
                    hotel['is_new'] = attributes.get('is_new', False)
                    hotel['is_instant_reserve'] = attributes.get('is_instant_reserve', False)
                    hotel['is_searchable_and_has_prices'] = attributes.get('is_searchable_and_has_prices', False)
                    hotel['allow_quota'] = attributes.get('allow_quota', False)
                    hotel['food_type_label'] = attributes.get('food_type_label', '')
                    hotel['food_type_text_short'] = attributes.get('food_type_text_short', '')
                    hotel['food_type_text_full'] = attributes.get('food_type_text_full', '')
                    hotel['status_enabled'] = attributes.get('status_enabled', '')
                    hotel['status_checked'] = attributes.get('status_checked', '')
                    hotel['status_deleted'] = attributes.get('status_deleted', '')
                    hotel['owner_first_time'] = attributes.get('owner_first_time', '')
                    hotel['owner_update_time'] = attributes.get('owner_update_time', '')
                    hotel['ros_accreditation_code'] = attributes.get('ros_accreditation_code', '')
                    hotel['ros_accreditation_url'] = attributes.get('ros_accreditation_url', '')
                    hotel['ics_export_link'] = attributes.get('ics_export_link', '')
                    hotel['more_often'] = attributes.get('more_often', '')
                    hotel['more_often_type'] = attributes.get('more_often_type', '')
                    
                    # Параметры (params) - сохраняем как JSON строку
                    params = attributes.get('params', {})
                    hotel['params'] = json.dumps(params, ensure_ascii=False) if params else ''
                    
                    # URL отеля
                    hotel['url'] = f"https://tvil.ru/entity/{hotel['id']}"
                    
                    hotels.append(hotel)
                    
            except Exception as e:
                print(f"Error extracting hotel data: {e}")
                continue
        
        return hotels
    
    def _save_to_csv(self):
        """
        Сохраняет данные отелей в CSV файл.
        """
        if not self.all_hotels:
            print("Нет данных для сохранения.")
            return
        
        csv_filename = self.current_dir / 'tvil_hotels.csv'
        
        # Определяем все возможные поля
        fieldnames = [
            'id', 'title', 'cabinet_title', 'full_title', 'list_title', 'entity_type', 'subtype',
            'address', 'short_address', 'full_address', 'map_address', 'city_address',
            'latitude', 'longitude', 'description', 'conditions',
            'price_min', 'price_max', 'daily_price_min', 'daily_price_max',
            'currency_id', 'currency_title', 'currency_symbol',
            'prepayment', 'rooms_total', 'bedroom_total', 'count_rooms',
            'count_reviews', 'count_real_reviews', 'rating_overall', 'entity_rating',
            'total_rating', 'user_rating', 'stars',
            'country_id', 'region_id', 'city_id', 'aria_id',
            'count_photos', 'count_guest', 'count_guest_max', 'categories_count',
            'occupied_categories', 'last_reserve', 'last_reserve_label',
            'is_new', 'is_instant_reserve', 'is_searchable_and_has_prices', 'allow_quota',
            'food_type_label', 'food_type_text_short', 'food_type_text_full',
            'status_enabled', 'status_checked', 'status_deleted',
            'owner_first_time', 'owner_update_time',
            'ros_accreditation_code', 'ros_accreditation_url', 'ics_export_link',
            'more_often', 'more_often_type', 'params', 'url'
        ]
        
        with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for hotel in self.all_hotels:
                writer.writerow(hotel)
        
        print(f"Сохранено {len(self.all_hotels)} отелей в {csv_filename.name}")

if __name__ == "__main__":
    parser = TvilHotelsParser()
    parser.get_all_hotels_list()