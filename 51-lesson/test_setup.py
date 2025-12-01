import flet as ft
from dotenv import load_dotenv
import os

def main(page: ft.Page):
    # Проверка загрузки переменных окружения
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    # Вывод результата
    page.add(
        ft.Text("Настройка успешна!" if api_key else "Проверьте .env файл!")
    )

ft.app(target=main)