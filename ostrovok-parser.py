from playwright.sync_api import sync_playwright
import time

def input_destination(page, destination="Иркутская область"):
    """Вводит название места назначения в поле поиска"""
    try:
        print(f"Ищем поле для ввода места назначения...")
        # Ждем появления поля ввода
        input_field = page.wait_for_selector('input[data-testid="destination-input"]', timeout=10000)
        
        print(f"Вводим '{destination}'...")
        # Кликаем на поле и очищаем его
        input_field.click()
        input_field.fill("")
        # Вводим текст
        input_field.type(destination, delay=100)  # delay для более естественного ввода
        
        # Ждем немного, чтобы увидеть результат
        time.sleep(2)
        print("Текст введен!")
        
        return True
    except Exception as e:
        print(f"Ошибка при вводе текста: {e}")
        return False

def select_destination_from_suggest(page, destination_text="Иркутская облась, Россия"):
    """Выбирает место назначения из выпадающего списка предложений"""
    try:
        print(f"Ждем появления списка предложений...")
        # Ждем появления элемента с предложением
        suggest_element = page.wait_for_selector(
            'div.Suggest-module__destinationTitle--FrP_e',
            timeout=10000
        )
        
        # Ищем элемент с нужным текстом
        print(f"Ищем '{destination_text}' в списке...")
        # Можно искать по тексту напрямую
        target_element = page.locator(
            f'div.Suggest-module__destinationTitle--FrP_e:has-text("{destination_text}")'
        ).first
        
        if target_element.count() > 0:
            print(f"Найден элемент '{destination_text}', кликаем...")
            target_element.click()
            time.sleep(1)  # Ждем немного после клика
            
            # Нажимаем кнопку Найти
            print("Ищем кнопку Найти...")
            search_button = page.locator('div.Button-module__content--2FF16:has-text("Найти")').first
            if search_button.count() > 0:
                print("Нажимаем кнопку Найти...")
                search_button.click()
                time.sleep(2)  # Ждем перехода
                print("Поиск выполнен!")
            else:
                print("Кнопка Найти не найдена")
            
            return True
        else:
            print(f"Элемент '{destination_text}' не найден в списке")
            return False
            
    except Exception as e:
        print(f"Ошибка при выборе из списка: {e}")
        return False

def click_hotels_tab(page):
    """Нажимает на кнопку 'Отели' для перехода в раздел только отелей"""
    try:
        print("Ищем кнопку 'Отели'...")
        # Ждем появления кнопки
        hotels_button = page.wait_for_selector(
            'button.Tabs_tab__QiT8_:has-text("Отели")',
            timeout=10000
        )
        
        # Проверяем, не активна ли уже кнопка
        button_class = hotels_button.get_attribute('class') or ''
        if 'Tabs_tab_active__6B0SQ' in button_class:
            print("Кнопка 'Отели' уже активна.")
            return True
        
        print("Нажимаем на кнопку 'Отели'...")
        hotels_button.click()
        
        # Ждем загрузки раздела отелей
        time.sleep(2)
        print("Переход в раздел 'Отели' выполнен!")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при нажатии на кнопку 'Отели': {e}")
        return False

def extract_hotel_names(page):
    """Извлекает все названия отелей из карточек на странице результатов"""
    hotel_names = []
    
    try:
        print("Ждем загрузки карточек отелей...")
        # Ждем появления хотя бы одной карточки отеля
        page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
        
        print("Ищем все карточки отелей...")
        # Находим все элементы с названиями отелей
        hotel_elements = page.query_selector_all('a[data-testid="hotel-card-name"]')
        
        print(f"Найдено карточек: {len(hotel_elements)}")
        
        # Извлекаем названия из каждого элемента
        for element in hotel_elements:
            try:
                hotel_name = element.inner_text().strip()
                if hotel_name:  # Добавляем только если название не пустое
                    hotel_names.append(hotel_name)
                    print(f"  - {hotel_name}")
            except Exception as e:
                print(f"Ошибка при извлечении названия: {e}")
                continue
        
        print(f"\nВсего извлечено названий отелей: {len(hotel_names)}")
        return hotel_names
        
    except Exception as e:
        print(f"Ошибка при извлечении названий отелей: {e}")
        return hotel_names

def paginate_and_extract_all_hotels(page, hotel_names):
    """Перелистывает все страницы и собирает названия отелей со всех страниц"""
    page_num = 2  # Начинаем со второй страницы, так как первая уже обработана
    
    while True:
        print(f"\n--- Страница {page_num} ---")
        
        try:
            # Ищем кнопку "Вперед"
            next_button = page.locator('button:has(div.Button_content__1ypi3:has-text("Вперед"))').first
            
            # Проверяем, существует ли кнопка
            if next_button.count() == 0:
                print("Кнопка 'Вперед' не найдена. Достигнута последняя страница.")
                break
            
            # Получаем класс кнопки для проверки disabled
            button_class = next_button.get_attribute('class') or ''
            
            # Проверяем, не disabled ли кнопка
            is_disabled = (
                'Button_button_disabled__Hp_eZ' in button_class or 
                'PageButtons_button_disabled__rtp6Z' in button_class
            )
            
            if is_disabled:
                print("Кнопка 'Вперед' disabled. Достигнута последняя страница.")
                break
            
            # Если кнопка активна, нажимаем на неё
            print(f"Нажимаем кнопку 'Вперед'...")
            next_button.click()
            
            # Ждем загрузки новой страницы
            time.sleep(3)
            page.wait_for_selector('a[data-testid="hotel-card-name"]', timeout=15000)
            
            # Извлекаем названия с новой страницы
            current_page_hotels = extract_hotel_names(page)
            hotel_names.extend(current_page_hotels)
            
            page_num += 1
            
        except Exception as e:
            print(f"Ошибка при перелистывании страницы: {e}")
            break
    print(hotel_names)
    print(f"\n=== Всего собрано названий отелей со всех страниц: {len(hotel_names)} ===")
    return hotel_names

def open_ostrovok():
    """Простая функция для открытия сайта ostrovok.ru"""
    with sync_playwright() as p:
        # Запускаем браузер (headless=False - видим браузер)
        browser = p.chromium.launch(headless=False)
        
        # Создаем контекст с русской локалью
        context = browser.new_context(
            locale="ru-RU"
        )
        page = context.new_page()
        
        # Устанавливаем заголовки для русского языка
        page.set_extra_http_headers({
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        })
        
        print("Заходим на ostrovok.ru...")
        page.goto("https://ostrovok.ru", timeout=60000)
        
        print("Страница загружена!")
        print(f"Заголовок страницы: {page.title()}")
        
        # Вводим место назначения
        input_destination(page, "Иркутская область")
        
        # Выбираем из списка предложений
        select_destination_from_suggest(page, "Иркутская область, Россия")
        
        # Нажимаем на кнопку "Отели" для перехода в раздел только отелей
        click_hotels_tab(page)
        
        # Извлекаем названия отелей с первой страницы
        hotel_names = extract_hotel_names(page)
        
        # Перелистываем все страницы и собираем названия со всех страниц
        hotel_names = paginate_and_extract_all_hotels(page, hotel_names)
        
        # Браузер остается открытым
        input("Нажмите Enter для закрытия браузера...")
        browser.close()

if __name__ == "__main__":
    open_ostrovok()
