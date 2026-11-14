from selenium import webdriver
import asyncio

def open_browser_sync():
    driver = webdriver.Firefox()
    driver.get("https://example.com")
    return driver

async def main():
    # Запускаем синхронный Selenium в фоне, не блокируя ассистента
    driver = await asyncio.to_thread(open_browser_sync)

asyncio.run(main())