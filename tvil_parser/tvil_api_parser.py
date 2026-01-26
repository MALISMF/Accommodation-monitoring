import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

def parse_tvil_api():
    """
    Парсит API ТВИЛ, получая отели с пагинацией через Playwright.
    Сохраняет каждый ответ в отдельный JSON-файл.
    """
    base_url = "https://tvil.ru/api/entities"
    offset = 0
    limit = 20
    
    # Получаем текущую директорию
    current_dir = Path(__file__).parent
    
    with sync_playwright() as p:
        # Запускаем браузер
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Сначала открываем главную страницу, чтобы получить cookies и пройти антибот
        print("Инициализация сессии через главную страницу...")
        page = context.new_page()
        page.goto("https://tvil.ru/city/irkutskaya-oblast/hotels/", wait_until="networkidle")
        time.sleep(5)  # Даём больше времени на обработку антибота
        
        # Теперь делаем запросы через JavaScript прямо в контексте страницы
        # Это обходит антибот, так как запрос выполняется как обычный браузерный запрос
        
        while True:
            # Формируем URL с параметрами
            params = {
                "page[limit]": str(limit),
                "page[offset]": str(offset),
                "include": "params,child_params,photos_t2,photos_t1,tooltip,services,inflect,characteristics",
                "filter[type]": "hotel",
                "filter[geo]": "251",
                "format[withNearEntities]": "1",
                "format[withBusyEntities]": "1",
                "order[priceFrom]": "0"
            }
            
            # Формируем query string
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{base_url}?{query_string}"
            
            try:
                print(f"Запрос для offset={offset}...")
                
                # Делаем запрос через JavaScript fetch в контексте страницы
                # Это использует все cookies и заголовки браузера
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
                            
                            // Пытаемся распарсить как JSON, даже если Content-Type не application/json
                            try {
                                data = JSON.parse(text);
                            } catch (e) {
                                // Если не JSON, возвращаем текст
                                return {
                                    status: response.status,
                                    statusText: response.statusText,
                                    headers: Object.fromEntries(response.headers.entries()),
                                    data: null,
                                    error: 'Not JSON response',
                                    text: text.substring(0, 1000)
                                };
                            }
                            
                            return {
                                status: response.status,
                                statusText: response.statusText,
                                headers: Object.fromEntries(response.headers.entries()),
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
                    if 'text' in response_data:
                        print(f"Ответ сервера (первые 1000 символов): {response_data['text']}")
                        # Сохраняем ответ в файл для анализа
                        error_filename = current_dir / f"tvil_irko_{offset}_error.txt"
                        with open(error_filename, "w", encoding="utf-8") as f:
                            f.write(f"Status Code: {response_data.get('status', 'N/A')}\n")
                            f.write(f"Error: {response_data['error']}\n")
                            f.write(f"Response Text:\n{response_data.get('text', '')}")
                        print(f"Ответ сохранён в {error_filename.name} для анализа")
                    break
                
                # Проверяем статус ответа
                if response_data['status'] != 200:
                    print(f"Ошибка: сервер вернул статус {response_data['status']}")
                    print(f"Status Text: {response_data.get('statusText', '')}")
                    # Если есть данные, выводим их для диагностики
                    if response_data.get('data'):
                        print(f"Ответ сервера: {json.dumps(response_data['data'], ensure_ascii=False, indent=2)[:500]}")
                    break
                
                # Получаем данные
                data = response_data['data']
                
                if data is None:
                    print(f"Получен пустой ответ для offset={offset}")
                    break
                
                # Проверяем, есть ли данные об отелях
                # Структура ответа может быть разной, проверяем несколько вариантов
                hotels = []
                if isinstance(data, dict):
                    # Если это словарь, ищем данные в разных возможных ключах
                    if "data" in data:
                        hotels = data["data"]
                    elif "entities" in data:
                        hotels = data["entities"]
                    elif isinstance(data.get("data"), list):
                        hotels = data["data"]
                elif isinstance(data, list):
                    hotels = data
                
                # Если список отелей пуст, останавливаемся
                if not hotels or len(hotels) == 0:
                    print(f"Получен пустой список отелей для offset={offset}. Останавливаем парсинг.")
                    break
                
                # Сохраняем в файл
                filename = current_dir / f"tvil_irko_{offset}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Выводим информацию
                hotels_count = len(hotels) if isinstance(hotels, list) else 0
                print(f"Сохранён файл: {filename.name}, отелей в ответе: {hotels_count}")
                
                # Если получили меньше отелей, чем limit, значит это последняя страница
                if hotels_count < limit:
                    print(f"Получено меньше отелей ({hotels_count}), чем limit ({limit}). Это последняя страница.")
                    break
                
                # Увеличиваем offset для следующей итерации
                offset += limit
                
                # Небольшая задержка между запросами
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Ошибка при выполнении запроса для offset={offset}: {e}")
                # Сохраняем ошибку для анализа
                error_filename = current_dir / f"tvil_irko_{offset}_error.txt"
                with open(error_filename, "w", encoding="utf-8") as f:
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"URL: {url}\n")
                print(f"Ошибка сохранена в {error_filename.name}")
                break
        
        browser.close()
    
    print(f"\nПарсинг завершён. Всего обработано offset до {offset}.")

if __name__ == "__main__":
    parse_tvil_api()
