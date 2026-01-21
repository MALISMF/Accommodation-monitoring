import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_room_data(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Извлекает данные по каждому номеру из JSON ответа API"""
    rooms_data = []
    
    hotel_id = json_data.get("ota_hotel_id", "")
    master_id = json_data.get("master_id", "")
    rates = json_data.get("rates", [])
    
    if not rates:
        # Если нет тарифов, возвращаем пустую строку с базовой информацией
        return [{
            "hotel_id": hotel_id,
            "master_id": master_id,
            "rate_hash": "",
            "rg_hash": "",
            "room_name": "",
            "room_type": "",
            "allotment": "",
            "bedding_type": "",
            "main_bed_count": "",
            "extra_bed_count": "",
            "has_breakfast": "",
            "meal_type": "",
            "amenities": "",
            "price_rub": "",
            "payment_types": "",
            "free_cancellation_before": "",
            "cancellation_penalty_percent": "",
            "no_show_penalty": ""
        }]
    
    for rate in rates:
        rate_hash = rate.get("hash", "")
        
        # Данные о цене и оплате из тарифа
        payment_options = rate.get("payment_options", {})
        payment_types_list = payment_options.get("payment_types", [])
        price_rub = ""
        if payment_types_list:
            first_payment = payment_types_list[0]
            price_rub = first_payment.get("amount") or first_payment.get("show_amount", "")
        
        allowed_payment_types = payment_options.get("allowed_payment_types", [])
        payment_types_str = ", ".join([
            f"{pt.get('type', '')}/{pt.get('by', '')}" 
            for pt in allowed_payment_types
        ])
        
        # Условия отмены
        cancellation_info = rate.get("cancellation_info", {})
        free_cancellation_before = cancellation_info.get("free_cancellation_before", "")
        if free_cancellation_before:
            # Убираем время, оставляем только дату
            free_cancellation_before = free_cancellation_before.split("T")[0]
        
        cancellation_policies = cancellation_info.get("policies", [])
        cancellation_penalty_percent = ""
        if cancellation_policies:
            # Берем первый penalty с процентом
            for policy in cancellation_policies:
                penalty = policy.get("penalty", {})
                if penalty.get("percent"):
                    cancellation_penalty_percent = penalty.get("percent", "")
                    break
        
        # No-show штраф
        no_show = rate.get("no_show", {})
        no_show_penalty = ""
        if no_show:
            no_show_penalty_obj = no_show.get("penalty", {})
            no_show_penalty = no_show_penalty_obj.get("amount", "")
        
        # Данные о номерах
        rooms = rate.get("rooms", [])
        
        if not rooms:
            # Если нет номеров в тарифе, создаем запись с данными тарифа
            rooms_data.append({
                "hotel_id": hotel_id,
                "master_id": master_id,
                "rate_hash": rate_hash,
                "rg_hash": "",
                "room_name": rate.get("room_name", ""),
                "room_type": rate.get("room_data_trans", {}).get("ru", {}).get("main_room_type", ""),
                "allotment": rate.get("allotment", ""),
                "bedding_type": rate.get("room_data_trans", {}).get("ru", {}).get("bedding_type", ""),
                "main_bed_count": rate.get("bed_places", {}).get("main_count", ""),
                "extra_bed_count": rate.get("bed_places", {}).get("extra_count", ""),
                "has_breakfast": rate.get("meal_data", {}).get("meals", [{}])[0].get("has_breakfast", False),
                "meal_type": rate.get("meal", [""])[0] if rate.get("meal") else "",
                "amenities": ", ".join(rate.get("serp_filters", [])),
                "price_rub": price_rub,
                "payment_types": payment_types_str,
                "free_cancellation_before": free_cancellation_before,
                "cancellation_penalty_percent": cancellation_penalty_percent,
                "no_show_penalty": no_show_penalty
            })
        else:
            # Обрабатываем каждый номер
            for room in rooms:
                room_name = room.get("room_name", "")
                room_data_trans = room.get("room_data_trans", {}).get("ru", {})
                room_type = room_data_trans.get("main_room_type", "")
                bedding_type = room_data_trans.get("bedding_type", "")
                
                bed_places = room.get("bed_places", {})
                main_bed_count = bed_places.get("main_count", "")
                extra_bed_count = bed_places.get("extra_count", "")
                
                meal_data = room.get("meal_data", {})
                meals = meal_data.get("meals", [])
                has_breakfast = False
                meal_type = ""
                if meals:
                    has_breakfast = meals[0].get("has_breakfast", False)
                    meal_type = meals[0].get("value", "")
                
                # Если meal_type пустой, пробуем из meal
                if not meal_type:
                    meal_list = room.get("meal", [])
                    if meal_list:
                        meal_type = meal_list[0]
                
                serp_filters = room.get("serp_filters", [])
                amenities = ", ".join(serp_filters) if serp_filters else ""
                
                allotment = room.get("allotment", "")
                rg_hash = room.get("rg_hash", "")
                
                rooms_data.append({
                    "hotel_id": hotel_id,
                    "master_id": master_id,
                    "rate_hash": rate_hash,
                    "rg_hash": rg_hash,
                    "room_name": room_name,
                    "room_type": room_type,
                    "allotment": allotment,
                    "bedding_type": bedding_type,
                    "main_bed_count": main_bed_count,
                    "extra_bed_count": extra_bed_count,
                    "has_breakfast": "Да" if has_breakfast else "Нет",
                    "meal_type": meal_type,
                    "amenities": amenities,
                    "price_rub": price_rub,
                    "payment_types": payment_types_str,
                    "free_cancellation_before": free_cancellation_before,
                    "cancellation_penalty_percent": cancellation_penalty_percent,
                    "no_show_penalty": no_show_penalty
                })
    
    return rooms_data


def process_json_files(json_dir: str = "json", output_csv: str = "hotels_rooms.csv"):
    """Обрабатывает все JSON файлы из папки и создает CSV"""
    
    json_path = Path(json_dir)
    if not json_path.exists():
        print(f"Папка {json_dir} не найдена!")
        return
    
    all_rooms = []
    
    # Обрабатываем все JSON файлы
    json_files = list(json_path.glob("*.json"))
    print(f"Найдено {len(json_files)} JSON файлов")
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            rooms_data = extract_room_data(data)
            all_rooms.extend(rooms_data)
            print(f"[OK] Обработан {json_file.name}: {len(rooms_data)} номеров")
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Ошибка парсинга JSON в {json_file.name}: {e}")
        except Exception as e:
            print(f"[ERROR] Ошибка при обработке {json_file.name}: {e}")
    
    # Сохраняем в CSV
    if not all_rooms:
        print("Нет данных для сохранения!")
        return
    
    fieldnames = [
        "hotel_id",
        "master_id",
        "rate_hash",
        "rg_hash",
        "room_name",
        "room_type",
        "allotment",
        "bedding_type",
        "main_bed_count",
        "extra_bed_count",
        "has_breakfast",
        "meal_type",
        "amenities",
        "price_rub",
        "payment_types",
        "free_cancellation_before",
        "cancellation_penalty_percent",
        "no_show_penalty"
    ]
    
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rooms)
    
    print(f"\n[OK] Данные сохранены в {output_csv}")
    print(f"Всего записей: {len(all_rooms)}")


if __name__ == "__main__":
    process_json_files()
