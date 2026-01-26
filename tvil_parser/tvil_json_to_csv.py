import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_hotel_data(hotel: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает данные об отеле из JSON структуры.
    
    Args:
        hotel: Словарь с данными об отеле из JSON
        
    Returns:
        Словарь с извлеченными данными для CSV
    """
    hotel_id = hotel.get("id", "")
    attributes = hotel.get("attributes", {})
    
    # Извлекаем базовую информацию
    row = {
        "id": hotel_id,
        "title": attributes.get("title", ""),
        "cabinet_title": attributes.get("cabinet_title", ""),
        "full_title": attributes.get("full_title", ""),
        "list_title": attributes.get("list_title", ""),
        "entity_type": attributes.get("entity_type", ""),
        "subtype": attributes.get("subtype", ""),
    }
    
    # Адреса
    row["address"] = attributes.get("address", "")
    row["short_address"] = attributes.get("short_address", "")
    row["full_address"] = attributes.get("full_address", "")
    row["map_address"] = attributes.get("map_address", "")
    row["city_address"] = attributes.get("city_address", "")
    
    # Координаты
    row["latitude"] = attributes.get("latitude", "")
    row["longitude"] = attributes.get("longitude", "")
    
    # Описание
    row["description"] = attributes.get("description", "")
    row["conditions"] = attributes.get("conditions", "")
    
    # Цены
    price = attributes.get("price", [])
    if isinstance(price, list) and len(price) > 0:
        row["price_min"] = price[0] if len(price) > 0 else ""
        row["price_max"] = price[-1] if len(price) > 1 else price[0] if len(price) > 0 else ""
    else:
        row["price_min"] = ""
        row["price_max"] = ""
    
    daily_price = attributes.get("daily_rubles_price", [])
    if isinstance(daily_price, list) and len(daily_price) > 0:
        row["daily_price_min"] = daily_price[0] if len(daily_price) > 0 else ""
        row["daily_price_max"] = daily_price[-1] if len(daily_price) > 1 else daily_price[0] if len(daily_price) > 0 else ""
    else:
        row["daily_price_min"] = ""
        row["daily_price_max"] = ""
    
    year_price = attributes.get("year_price", [])
    if isinstance(year_price, list) and len(year_price) > 0:
        row["year_price_min"] = year_price[0] if len(year_price) > 0 else ""
        row["year_price_max"] = year_price[-1] if len(year_price) > 1 else year_price[0] if len(year_price) > 0 else ""
    else:
        row["year_price_min"] = ""
        row["year_price_max"] = ""
    
    # Валюта
    currency = attributes.get("currency", {})
    if isinstance(currency, dict):
        row["currency_id"] = currency.get("id", "")
        row["currency_title"] = currency.get("title", "")
        row["currency_symbol"] = currency.get("symbol", "")
    else:
        row["currency_id"] = ""
        row["currency_title"] = ""
        row["currency_symbol"] = ""
    
    # Предоплата
    row["prepayment"] = attributes.get("prepayment", "")
    
    # Номера
    row["rooms_total"] = attributes.get("rooms_total", "")
    row["bedroom_total"] = attributes.get("bedroom_total", "")
    row["count_rooms"] = attributes.get("count_rooms", "")
    
    # Рейтинги и отзывы
    row["count_reviews"] = attributes.get("count_reviews", "")
    row["count_real_reviews"] = attributes.get("count_real_reviews", "")
    row["rating_overall"] = attributes.get("rating_overall", "")
    row["entity_rating"] = attributes.get("entity_rating", "")
    row["total_rating"] = attributes.get("total_rating", "")
    row["user_rating"] = attributes.get("user_rating", "")
    row["stars"] = attributes.get("stars", "")
    
    # Географические ID
    row["country_id"] = attributes.get("country_id", "")
    row["region_id"] = attributes.get("region_id", "")
    row["city_id"] = attributes.get("city_id", "")
    row["aria_id"] = attributes.get("aria_id", "")
    
    # Дополнительная информация
    row["count_photos"] = attributes.get("count_photos", "")
    row["count_guest"] = attributes.get("count_guest", "")
    row["count_guest_max"] = attributes.get("count_guest_max", "")
    row["categories_count"] = attributes.get("categories_count", "")
    row["occupied_categories"] = attributes.get("occupied_categories", "")
    
    # Временные метки
    row["last_reserve"] = attributes.get("last_reserve", "")
    row["last_reserve_label"] = attributes.get("last_reserve_label", "")
    
    # Флаги и статусы
    row["is_new"] = attributes.get("is_new", "")
    row["is_instant_reserve"] = attributes.get("is_instant_reserve", "")
    row["is_searchable_and_has_prices"] = attributes.get("is_searchable_and_has_prices", "")
    row["allow_quota"] = attributes.get("allow_quota", "")
    
    # Питание
    food_type = attributes.get("food_type", {})
    if isinstance(food_type, dict):
        row["food_type_label"] = food_type.get("label", "")
        row["food_type_text_short"] = food_type.get("text_short", "")
        row["food_type_text_full"] = food_type.get("text_full", "")
    else:
        row["food_type_label"] = ""
        row["food_type_text_short"] = ""
        row["food_type_text_full"] = ""
    
    # Статус
    status = attributes.get("status", {})
    if isinstance(status, dict):
        row["status_enabled"] = status.get("enabled", "")
        row["status_checked"] = status.get("checked", "")
        row["status_deleted"] = status.get("deleted", "")
    else:
        row["status_enabled"] = ""
        row["status_checked"] = ""
        row["status_deleted"] = ""
    
    # Владелец
    owner = attributes.get("owner", {})
    if isinstance(owner, dict):
        row["owner_first_time"] = owner.get("first_time", "")
        row["owner_update_time"] = owner.get("update_time", "")
    else:
        row["owner_first_time"] = ""
        row["owner_update_time"] = ""
    
    # Аккредитация
    row["ros_accreditation_code"] = attributes.get("ros_accreditation_code", "")
    row["ros_accreditation_url"] = attributes.get("ros_accreditation_url", "")
    
    # Ссылки
    row["ics_export_link"] = attributes.get("ics_export_link", "")
    
    # Популярность
    row["more_often"] = attributes.get("more_often", "")
    row["more_often_type"] = attributes.get("more_often_type", "")
    
    # Параметры (сериализуем в JSON строку)
    params = attributes.get("params", {})
    if isinstance(params, dict):
        row["params"] = json.dumps(params, ensure_ascii=False)
    else:
        row["params"] = ""
    
    return row


def get_csv_columns() -> List[str]:
    """
    Возвращает список колонок для CSV файла.
    
    Returns:
        Список названий колонок
    """
    return [
        "id",
        "title",
        "cabinet_title",
        "full_title",
        "list_title",
        "entity_type",
        "subtype",
        "address",
        "short_address",
        "full_address",
        "map_address",
        "city_address",
        "latitude",
        "longitude",
        "description",
        "conditions",
        "price_min",
        "price_max",
        "daily_price_min",
        "daily_price_max",
        "year_price_min",
        "year_price_max",
        "currency_id",
        "currency_title",
        "currency_symbol",
        "prepayment",
        "rooms_total",
        "bedroom_total",
        "count_rooms",
        "count_reviews",
        "count_real_reviews",
        "rating_overall",
        "entity_rating",
        "total_rating",
        "user_rating",
        "stars",
        "country_id",
        "region_id",
        "city_id",
        "aria_id",
        "count_photos",
        "count_guest",
        "count_guest_max",
        "categories_count",
        "occupied_categories",
        "last_reserve",
        "last_reserve_label",
        "is_new",
        "is_instant_reserve",
        "is_searchable_and_has_prices",
        "allow_quota",
        "food_type_label",
        "food_type_text_short",
        "food_type_text_full",
        "status_enabled",
        "status_checked",
        "status_deleted",
        "owner_first_time",
        "owner_update_time",
        "ros_accreditation_code",
        "ros_accreditation_url",
        "ics_export_link",
        "more_often",
        "more_often_type",
        "params",
    ]


def convert_json_to_csv(json_dir: Optional[Path] = None, output_file: Optional[Path] = None) -> None:
    """
    Конвертирует JSON файлы с отелями в CSV таблицу.
    
    Args:
        json_dir: Директория с JSON файлами (по умолчанию - директория скрипта)
        output_file: Путь к выходному CSV файлу (по умолчанию - tvil_hotels.csv в директории скрипта)
    """
    if json_dir is None:
        json_dir = Path(__file__).parent
    
    if output_file is None:
        output_file = json_dir / "tvil_hotels.csv"
    
    # Находим все JSON файлы с паттерном tvil_irko_*.json
    json_files = sorted(json_dir.glob("tvil_irko_*.json"))
    
    if not json_files:
        print(f"Не найдено JSON файлов в директории {json_dir}")
        return
    
    print(f"Найдено {len(json_files)} JSON файлов для обработки")
    
    # Собираем все отели из всех файлов
    all_hotels = []
    processed_files = 0
    
    for json_file in json_files:
        try:
            print(f"Обработка файла: {json_file.name}")
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Извлекаем массив отелей
            hotels = data.get("data", [])
            
            if not hotels:
                print(f"  Предупреждение: файл {json_file.name} не содержит данных об отелях")
                continue
            
            # Обрабатываем каждый отель
            for hotel in hotels:
                hotel_data = extract_hotel_data(hotel)
                all_hotels.append(hotel_data)
            
            processed_files += 1
            print(f"  Извлечено {len(hotels)} отелей из {json_file.name}")
            
        except json.JSONDecodeError as e:
            print(f"  Ошибка: не удалось распарсить JSON файл {json_file.name}: {e}")
            continue
        except Exception as e:
            print(f"  Ошибка при обработке файла {json_file.name}: {e}")
            continue
    
    if not all_hotels:
        print("Не найдено отелей для записи в CSV")
        return
    
    # Удаляем дубликаты по ID (если один отель встречается в нескольких файлах)
    seen_ids = set()
    unique_hotels = []
    duplicates_count = 0
    
    for hotel in all_hotels:
        hotel_id = hotel.get("id", "")
        if hotel_id and hotel_id not in seen_ids:
            seen_ids.add(hotel_id)
            unique_hotels.append(hotel)
        elif hotel_id:
            duplicates_count += 1
    
    if duplicates_count > 0:
        print(f"Удалено {duplicates_count} дубликатов отелей")
    
    # Записываем в CSV
    columns = get_csv_columns()
    
    print(f"Запись {len(unique_hotels)} уникальных отелей в CSV файл: {output_file}")
    
    try:
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(unique_hotels)
        
        print(f"✓ Успешно создан CSV файл: {output_file}")
        print(f"  Обработано файлов: {processed_files}")
        print(f"  Всего отелей: {len(unique_hotels)}")
        
    except Exception as e:
        print(f"Ошибка при записи CSV файла: {e}")
        raise


if __name__ == "__main__":
    convert_json_to_csv()
