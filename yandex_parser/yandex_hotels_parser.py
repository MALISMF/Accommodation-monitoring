import requests
import json
import os
import asyncio
from playwright.async_api import async_playwright

async def get_unauthenticated_cookies():
    """Получение cookies неавторизированного пользователя через playwright"""
    async with async_playwright() as p:
        # Запускаем браузер и создаем новый контекст без сохраненных данных (чистый профиль)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        try:
            page = await context.new_page()

            # Переходим на сайт Яндекс.Путешествий
            await page.goto('https://travel.yandex.ru/hotels/irkutsk-oblast/?adults=2&bbox=104.13056255102043%2C51.5404668592517~107.37870529166668%2C53.507196730491884&checkinDate=2026-01-25&checkoutDate=2026-01-26&childrenAges=&filterAtoms=rubric_id%3AHOTEL&flexibleDatesType&geoId=11266&navigationToken=0&oneNightChecked=false&onlyCurrentGeoId=1&roomCount=1&searchPagePollingId=fa259bdc3150c804ade3acb89f40bce-2-newsearch&selectedSortId=relevant-first', timeout=30000)
            await page.wait_for_selector('body', timeout=10000)  # Ждем загрузки body элемента

            # Получаем cookies из чистого сеанса
            cookies_raw = await context.cookies()
            cookies = {cookie['name']: cookie['value'] for cookie in cookies_raw}

            print(f"Получено {len(cookies)} cookies для неавторизированного пользователя")
            return cookies

        finally:
            await context.close()

# Получаем cookies для неавторизированного пользователя
cookies = asyncio.run(get_unauthenticated_cookies())

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://travel.yandex.ru/hotels/irkutsk-oblast/?adults=2&bbox=104.13056255102043%2C51.54264369120642~107.37870529166668%2C53.505019898537164&checkinDate=2026-01-25&checkoutDate=2026-01-26&childrenAges=&filterAtoms=rubric_id%3AHOTEL&flexibleDatesType&geoId=11266&lastSearchTimeMarker=1769238200213&navigationToken=0&oneNightChecked=false&onlyCurrentGeoId=1&roomCount=1&searchPagePollingId=b7dd8df58d9c6c1fbcec79fc7d495925-1-newsearch&selectedSortId=relevant-first',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'x-csrf-token': 'xxx',
    'x-requested-with': 'XMLHttpRequest',
    'x-retpath-y': 'https://travel.yandex.ru/hotels/irkutsk-oblast/?adults=2&bbox=104.13056255102043%2C51.54264369120642~107.37870529166668%2C53.505019898537164&checkinDate=2026-01-25&checkoutDate=2026-01-26&childrenAges=&filterAtoms=rubric_id%3AHOTEL&flexibleDatesType&geoId=11266&lastSearchTimeMarker=1769238200213&navigationToken=0&oneNightChecked=false&onlyCurrentGeoId=1&roomCount=1&searchPagePollingId=b7dd8df58d9c6c1fbcec79fc7d495925-1-newsearch&selectedSortId=relevant-first',
    'x-ya-travel-page-token': '',
}

            # Базовый URL для запросов
base_url = 'https://travel.yandex.ru/api/hotels/searchHotels?startSearchReason=mount&mapAspectRatio=0.5184705017352793&pollIteration=0&pollEpoch=0&roomCount=1&adults=2&checkinDate=2026-01-25&checkoutDate=2026-01-26&geoId=11266&bbox=104.13056255102043,51.54264369120642~107.37870529166668,53.505019898537164&navigationToken={}&filterAtoms[]=rubric_id:HOTEL&onlyCurrentGeoId=true&selectedSortId=relevant-first&geoLocationStatus=unknown&geoSlug=irkutsk-oblast&pageHotelCount=50&pricedHotelLimit=50&totalHotelLimit=50&totalHotelPointLimit=800&searchPagePollingId=b7dd8df58d9c6c1fbcec79fc7d495925-1-newsearch&seoMode=search&searchOriginType=SEARCH&imageLimit=10'

# Начальный navigationToken
navigation_token = '0'
page_counter = 1

while navigation_token:
    print(f"Парсим страницу {page_counter} с navigationToken: {navigation_token}")

    # Формируем URL с текущим токеном
    url = base_url.format(navigation_token)

    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Сохраняем результат в файл
        filename = f'yandex_parser/yandex_json/page_{page_counter}.json'
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"Страница {page_counter} сохранена в {filename}")

        # Извлекаем следующий navigationToken
        if 'data' in data and 'navigationTokens' in data['data'] and 'nextPage' in data['data']['navigationTokens']:
            next_token = data['data']['navigationTokens']['nextPage']
            if next_token and str(next_token) != str(navigation_token):
                navigation_token = str(next_token)
                page_counter += 1
            else:
                print("Больше страниц нет")
                break
        else:
            print("navigationToken не найден в ответе")
            break

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе страницы {page_counter}: {e}")
        break
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON страницы {page_counter}: {e}")
        break

print(f"Парсинг завершен. Обработано {page_counter - 1} страниц.")