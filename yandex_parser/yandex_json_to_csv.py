import json
import csv
import os
import glob

def extract_hotel_info(hotel_data):
    """Извлекает информацию об отеле из данных hotel"""
    hotel = hotel_data.get('hotel', {})

    return {
        'id': hotel.get('permalink', ''),
        'name': hotel.get('name', ''),
        'address': hotel.get('address', ''),
        'address_en': hotel.get('addressEn', ''),
        'stars': hotel.get('stars', 0),
        'rating': hotel.get('rating', 0),
        'review_count': hotel.get('totalTextReviewCount', 0),
        'image_count': hotel.get('totalImageCount', 0),
        'latitude': hotel.get('coordinates', {}).get('lat', 0),
        'longitude': hotel.get('coordinates', {}).get('lon', 0),
        'category': hotel.get('category', {}).get('name', ''),
        'has_verified_owner': hotel.get('hasVerifiedOwner', False),
        'phone_available': hotel.get('isPhoneCallAvailable', False)
    }

def parse_json_files():
    """Парсит все JSON файлы и извлекает информацию об отелях"""
    json_dir = 'yandex_parser/yandex_json'
    all_hotels = []

    # Находим все JSON файлы
    json_files = glob.glob(os.path.join(json_dir, 'page_*.json'))

    if not json_files:
        print(f"Не найдены JSON файлы в папке {json_dir}")
        return []

    print(f"Найдено {len(json_files)} JSON файлов")

    for json_file in sorted(json_files):
        print(f"Парсим файл: {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Извлекаем отели из data.hotels
            hotels_data = data.get('data', {}).get('hotels', [])

            for hotel_item in hotels_data:
                hotel_info = extract_hotel_info(hotel_item)
                all_hotels.append(hotel_info)

        except Exception as e:
            print(f"Ошибка при парсинге файла {json_file}: {e}")

    print(f"Всего извлечено {len(all_hotels)} отелей")
    return all_hotels

def save_to_csv(hotels, filename='yandex_hotels.csv'):
    """Сохраняет данные об отелях в CSV файл"""
    if not hotels:
        print("Нет данных для сохранения")
        return

    fieldnames = [
        'id', 'name', 'address', 'address_en', 'stars', 'rating',
        'review_count', 'image_count', 'latitude', 'longitude',
        'category', 'has_verified_owner', 'phone_available'
    ]

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for hotel in hotels:
                writer.writerow(hotel)

        print(f"Данные сохранены в файл {filename}")
        print(f"Всего записей: {len(hotels)}")

    except Exception as e:
        print(f"Ошибка при сохранении CSV файла: {e}")

def main():
    """Основная функция"""
    print("Начинаем парсинг JSON файлов...")

    # Парсим все JSON файлы
    hotels = parse_json_files()

    # Сохраняем в CSV
    save_to_csv(hotels)

    print("Парсинг завершен!")

if __name__ == "__main__":
    main()