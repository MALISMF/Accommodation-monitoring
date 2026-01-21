from playwright.sync_api import sync_playwright
import time
import sys
import json
import csv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


# Настройка stdout для корректного вывода Юникода
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def close_search_popup(page):
    """Закрывает попап поиска (если внезапно вылез), максимально безопасно."""
    try:
        # Закрываем только через кнопку "close"
        btn = page.locator('button[aria-label*="close" i]').first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
            time.sleep(0.5)
            print("Popup closed: Close button clicked")
        else:
            print("Popup not closed: Close button not found or not visible")
        return True
    except Exception as e:
        print(f"Error closing popup (maybe not open): {e}")
        return False


def save_page_html(page, filename="page.html"):
    """Сохраняет HTML текущей страницы в файл."""
    try:
        html_content = page.content()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML saved to file: {filename}")
        return True
    except Exception as e:
        print(f"Error saving HTML: {e}")
        return False


def get_hotel_cards(page):
    """
    Извлекает данные отелей из карточек на странице.
    Возвращает список словарей с полной информацией об отелях.
    """
    hotels = []

    try:
        # Ждём появления хотя бы одной карточки
        page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)

        # Находим все карточки отелей по контейнеру
        hotel_cards = page.query_selector_all('[data-testid="serp-hotelcard"]')

        for card in hotel_cards:
            try:
                hotel_data = {}
                
                # Название отеля и ссылка на страницу
                name_link = card.query_selector('a[data-testid="hotel-card-name"]')
                if name_link:
                    hotel_data['name'] = name_link.inner_text().strip()
                    href = name_link.get_attribute('href')
                    if href:
                        # Формируем полный URL
                        if href.startswith('/'):
                            hotel_data['detail_url'] = f"https://ostrovok.ru{href}"
                        else:
                            hotel_data['detail_url'] = href
                else:
                    continue

                if not hotel_data.get('name'):
                    continue

                # Адрес
                address_el = card.query_selector('[data-testid="hotel-card-distance-address"]')
                hotel_data['address'] = address_el.inner_text().strip() if address_el else ""

                # Ссылка "Показать все номера"
                show_rooms_link = card.query_selector('a[data-testid="next-step-button"]')
                if show_rooms_link:
                    rooms_href = show_rooms_link.get_attribute('href')
                    if rooms_href:
                        if rooms_href.startswith('/'):
                            hotel_data['show_rooms_url'] = f"https://ostrovok.ru{rooms_href}"
                        else:
                            hotel_data['show_rooms_url'] = rooms_href
                    else:
                        hotel_data['show_rooms_url'] = ""
                else:
                    hotel_data['show_rooms_url'] = ""

                # Минимальная цена за ночь
                price_value_el = card.query_selector('[data-testid="hotel-card-price-value"]')
                price_desc_el = card.query_selector('[data-testid="hotel-card-rate-description"]')
                if price_value_el and price_desc_el:
                    price_value = price_value_el.inner_text().strip()
                    price_desc = price_desc_el.inner_text().strip()
                    hotel_data['min_price'] = f"{price_value} {price_desc}".strip()
                else:
                    hotel_data['min_price'] = ""

                # Оценка по отзывам (число)
                rating_content_el = card.query_selector('[data-testid="hotel-card-rating-content"]')
                if rating_content_el:
                    rating_text = rating_content_el.inner_text().strip()
                    # Заменяем запятую на точку для числового значения
                    hotel_data['rating'] = rating_text.replace(',', '.')
                else:
                    hotel_data['rating'] = ""

                # Текстовая категория оценки
                rating_category_el = card.query_selector('.HotelRating_ratingCategory__cNoZe')
                if rating_category_el:
                    hotel_data['rating_category'] = rating_category_el.inner_text().strip()
                else:
                    hotel_data['rating_category'] = ""

                # Количество отзывов
                reviews_count_el = card.query_selector('.HotelRating_reviewsCount__3YYVd')
                if reviews_count_el:
                    hotel_data['reviews_count'] = reviews_count_el.inner_text().strip()
                else:
                    hotel_data['reviews_count'] = ""

                hotels.append(hotel_data)

            except Exception as e:
                print(f"Error extracting hotel data: {e}")
                continue

        return hotels

    except Exception as e:
        print(f"Error extracting hotel names: {e}")
        return hotels


def goto_page(page, page_number):
    """
    Переход на указанную страницу результатов (page=N),
    сохраняя остальные query-параметры.
    """
    current_url = page.url
    parsed = urlparse(current_url)
    qs = parse_qs(parsed.query)

    qs["page"] = [str(page_number)]
    new_query = urlencode(qs, doseq=True)
    new_url = urlunparse(parsed._replace(query=new_query))

    print(f"Navigating to page {page_number}: {new_url}")
    try:
        page.goto(new_url, timeout=60000, wait_until="domcontentloaded")
        # Ждем немного для загрузки контента
        time.sleep(1)
    except Exception as e:
        print(f"Error navigating to page {page_number}: {e}")
        raise


def paginate_and_extract_all_hotels(page, hotels):
    """
    Обходит номера страниц (1, 2, 3, ...), пока в пагинации
    существует ссылка на следующую страницу.
    Собирает все отели со всех страниц без удаления дубликатов
    и без дополнительного объединения информации.
    """
    # TEMP: limit pagination to first 5 pages for debugging
    max_page = 5

    while True:
        try:
            # Определяем текущую страницу по URL (?page=N)
            url = page.url
            current_page = 1
            if "page=" in url:
                qs = parse_qs(urlparse(url).query)
                current_page = int(qs.get("page", ["1"])[0])

            next_page = current_page + 1
            if next_page > max_page:
                print(f"\nReached debug page limit ({max_page}). Stopping pagination.")
                break
            print(f"\n--- Page {current_page} ---")

            # Проверяем наличие ссылки на next_page в пагинации
            # На реальной странице пагинация выглядит как "1 2 3 ... 40" [page:1]
            next_link = page.locator(f'a:has-text("{next_page}")').first

            if next_link.count() == 0:
                print(f"No link for page {next_page} found. Reached last page.")
                break

            # Переходим на следующую страницу через параметр ?page=
            goto_page(page, next_page)

            # Ретраи для загрузки карточек (scroll + wait)
            cards_found = False
            for attempt in range(3):
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.5)

                    page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
                    cards_found = True
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} on page {next_page} failed: {e}")
                    if attempt < 2:
                        time.sleep(2)

            if not cards_found:
                print(f"Could not find hotel cards on page {next_page}. Stopping.")
                break

            time.sleep(1.0)

            # Собираем отели на новой странице (как есть, без удаления дубликатов)
            current_hotels = get_hotel_cards(page)

            if len(current_hotels) == 0:
                print(f"Warning: no hotels found on page {next_page}.")
                break
            else:
                hotels.extend(current_hotels)
                print(f"Extracted {len(current_hotels)} hotels on page {next_page}.")

        except Exception as e:
            print(f"Error while going to next page: {e}")
            break

    print(f"\n=== Total hotels collected from all pages: {len(hotels)} ===")
    return hotels


def get_hotels_list():
    """Основная функция: собирает список всех отелей и сохраняет в JSON/CSV."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(
            "https://ostrovok.ru/hotel/russia/western_siberia_irkutsk_oblast_multi/?type_group=hotel"
        )

        # Небольшая пауза для первичной загрузки
        time.sleep(1)

        # Закрываем возможные попапы
        close_search_popup(page)

        # Ждём появления карточек
        page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
        time.sleep(2)

        # Сохраняем HTML (для отладки и анализа разметки)
        save_page_html(page, "page.html")

        # Отели на первой странице
        hotels = get_hotel_cards(page)

        # Переход по страницам и сбор всех отелей
        hotels = paginate_and_extract_all_hotels(page, hotels)

        # Сохраняем в JSON
        with open('hotels_list.json', 'w', encoding='utf-8') as f:
            json.dump(hotels, f, ensure_ascii=False, indent=2)

        print(f"\nHotels list saved to hotels_list.json ({len(hotels)} hotels)")

        # Сохраняем в CSV: все поля отеля
        # Используем quoting для правильного экранирования значений с запятыми
        with open('hotels_list.csv', 'w', encoding='utf-8-sig', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'hotel_name', 
                'address', 
                'detail_url', 
                'show_rooms_url', 
                'min_price', 
                'rating', 
                'rating_category', 
                'reviews_count'
            ])
            for hotel in hotels:
                writer.writerow([
                    hotel.get('name', ''), 
                    hotel.get('address', ''),
                    hotel.get('detail_url', ''),
                    hotel.get('show_rooms_url', ''),
                    hotel.get('min_price', ''),
                    hotel.get('rating', ''),
                    hotel.get('rating_category', ''),
                    hotel.get('reviews_count', '')
                ])

        print(f"Hotels list also saved to hotels_list.csv ({len(hotels)} rows)")

        # Печатаем список (если консоль позволяет)
        try:
            print("\nHotels list (first 10):")
            for i, hotel in enumerate(hotels[:10], 1):
                address_info = f" ({hotel.get('address', '')})" if hotel.get('address') else ""
                rating_info = f" | Рейтинг: {hotel.get('rating', 'N/A')} ({hotel.get('rating_category', 'N/A')})" if hotel.get('rating') else ""
                price_info = f" | {hotel.get('min_price', '')}" if hotel.get('min_price') else ""
                print(f"{i}. {hotel['name']}{address_info}{rating_info}{price_info}")
            if len(hotels) > 10:
                print(f"... and {len(hotels) - 10} more")
        except UnicodeEncodeError:
            print(f"\nTotal hotels: {len(hotels)}")
            print("(Full list saved to hotels_list.json and hotels_list.csv)")

        browser.close()


if __name__ == "__main__":
    get_hotels_list()
