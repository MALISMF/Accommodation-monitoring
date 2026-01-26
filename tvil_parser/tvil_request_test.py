from playwright.sync_api import sync_playwright

def open_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://tvil.ru/city/irkutskaya-oblast/hotels/")
        input("Нажмите Enter для закрытия браузера...")
        browser.close()

if __name__ == "__main__":
    open_page()
