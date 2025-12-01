# Импорт необходимых библиотек и модулей
import flet as ft                                  # Фреймворк для создания кроссплатформенных приложений с современным UI
from api.openrouter import OpenRouterClient        # Клиент для взаимодействия с OpenRouter API с поддержкой прямой передачи ключа
from ui.styles import AppStyles                    # Модуль с настройками стилей всего приложения
from ui.components import MessageBubble, ModelSelector  # Пользовательские компоненты: пузырьки сообщений и выбор модели с поиском
from utils.cache import ChatCache                  # Модуль для хранения истории чата и данных аутентификации (ключ + PIN)
from utils.logger import AppLogger                 # Модуль для логирования всех событий приложения
from utils.analytics import Analytics              # Модуль для сбора и анализа статистики использования
from utils.monitor import PerformanceMonitor       # Модуль для мониторинга производительности приложения
import asyncio                                     # Библиотека для асинхронного выполнения запросов к API
import time                                        # Библиотека для измерения времени ответа модели
import os                                          # Библиотека для работы с файловой системой (создание папки exports)
import random                                      # Библиотека для генерации случайного 4-значного PIN-кода
from datetime import datetime                      # Класс для работы с датой и временем (имена файлов, таймстампы)
import json                                        # Библиотека для сохранения истории чата в JSON-формате


class ChatApp:
    """
    Основной класс приложения — полностью управляет жизненным циклом чата.
    
    Реализует:
    - Систему аутентификации без modal-диалогов (чтобы избежать багов с overlay в Flet)
    - Первый запуск: ввод API-ключа → проверка → генерация и показ PIN-кода
    - Последующие запуски: вход по 4-значному PIN
    - Полноценный чат с сохранением истории, аналитикой, экспортом и очисткой
    """
    def __init__(self):
        """
        Инициализация всех подсистем приложения.
        """
        self.cache = ChatCache()                   # Кэширование сообщений и данных аутентификации
        self.logger = AppLogger()                  # Логирование событий
        self.analytics = Analytics(self.cache)     # Сбор статистики использования
        self.monitor = PerformanceMonitor()        # Мониторинг производительности

        # Загрузка сохранённых данных аутентификации из базы
        self.stored_api_key, self.stored_pin = self.cache.get_api_key_and_pin()
        self.api_client = None                     # Будет создан после успешного входа

        # Создание папки для экспорта истории чата
        self.exports_dir = "exports"
        os.makedirs(self.exports_dir, exist_ok=True)

        # Элементы основного интерфейса чата (создаются после входа)
        self.balance_text = None
        self.model_dropdown = None
        self.chat_history = None
        self.message_input = None

    def main(self, page: ft.Page):
        """
        Точка входа в приложение — вызывается Flet при запуске.
        
        Args:
            page (ft.Page): Главная страница приложения
        """
        self.page = page
        
        # Применение глобальных стилей страницы
        for key, value in AppStyles.PAGE_SETTINGS.items():
            setattr(page, key, value)
        AppStyles.set_window_size(page)
        page.title = "OpenRouter Chat"

        # Выбор экрана в зависимости от наличия сохранённого ключа/PIN
        if not self.stored_api_key or not self.stored_pin:
            self.show_key_entry_screen()       # Первый запуск
        else:
            self.show_pin_entry_screen()       # Повторный запуск

    # Универсальная функция закрытия любого диалогового окна (аналитика, очистка, сохранение)
    def close_dialog(self):
        """
        Полное и безопасное закрытие диалога.
        Используется вместо page.overlay.remove() — надёжнее работает в разных версиях Flet.
        """
        if self.page.dialog:
            self.page.dialog.open = False      # Закрываем диалог
            self.page.dialog = None            # Полностью убираем ссылку
        self.page.update()                     # Принудительное обновление страницы

    def show_key_entry_screen(self):
        """
        Экран ввода API-ключа при первом запуске.
        
        Полностью заменяет содержимое страницы (без modal).
        """
        self.page.controls.clear()
        self.page.bgcolor = ft.Colors.with_opacity(0.95, "#0f0f1f")  # Тёмный фон для экрана входа
        self.page.update()

        key_input = ft.TextField(
            label="API-ключ OpenRouter.ai",
            password=True,                         # Скрытие символов
            width=540,
            hint_text="sk-or-v1-...",
            text_style=ft.TextStyle(size=16)
        )
        error_text = ft.Text("", color=ft.Colors.RED_600, size=14)  # Текст ошибки

        def submit_key(e):
            """Проверка введённого API-ключа и генерация PIN-кода"""
            api_key = key_input.value.strip()
            if not api_key:
                error_text.value = "Введите ключ"
                self.page.update()
                return

            try:
                # Создаём временный клиент для проверки ключа
                temp_client = OpenRouterClient(api_key=api_key)

                # Генерируем случайный 4-значный PIN
                new_pin = f"{random.randint(0, 9999):04d}"
                self.cache.set_api_key_and_pin(api_key, new_pin)

                # Сохраняем данные для текущей сессии
                self.stored_api_key = api_key
                self.stored_pin = new_pin
                self.api_client = temp_client

                # Переходим к экрану показа PIN-кода
                self.show_pin_created_screen(new_pin)

            except Exception as ex:
                # Любая ошибка (401, нет интернета и т.д.) — показываем сообщение
                error_text.value = "Неверный ключ или нет интернета"
                self.page.update()

        self.page.add(
            ft.Column([
                ft.Text("Первый запуск", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Введите ваш API-ключ от OpenRouter.ai", size=16, color=ft.Colors.WHITE70),
                key_input,
                error_text,
                ft.ElevatedButton("Проверить и сохранить", on_click=submit_key, width=540, height=50),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=25)
        )
        self.page.update()

    def show_pin_created_screen(self, pin: str):
        """
        Экран отображения сгенерированного PIN-кода.
        
        Показывается один раз после успешной проверки ключа.
        
        Args:
            pin (str): 4-значный PIN-код
        """
        self.page.controls.clear()
        self.page.bgcolor = ft.Colors.with_opacity(0.98, "#0a0a1a")
        self.page.update()

        self.page.add(
            ft.Column([
                ft.Text("PIN-код успешно создан!", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                ft.Text("Запомните его прямо сейчас:", size=19, color=ft.Colors.WHITE70),
                ft.Container(
                    content=ft.Text(pin, size=82, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.BLUE_900,
                    padding=ft.padding.symmetric(vertical=45, horizontal=60),
                    border_radius=20,
                    shadow=ft.BoxShadow(blur_radius=25, color=ft.Colors.with_opacity(0.5, ft.Colors.BLUE)),
                    width=380,
                    height=200,
                ),
                ft.Text("При следующих запусках вы будете входить только по этому PIN.", size=16, color=ft.Colors.WHITE70, text_align=ft.TextAlign.CENTER),
                ft.ElevatedButton(
                    "Запомнил → Открыть чат",
                    on_click=lambda _: self.open_main_app(),  # Переход к основному чату
                    width=420,
                    height=60,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=35)
        )
        self.page.update()

    def show_pin_entry_screen(self):
        """
        Экран ввода PIN-кода при повторном запуске приложения.
        """
        self.page.controls.clear()
        self.page.bgcolor = ft.Colors.with_opacity(0.95, "#0f0f1f")
        self.page.update()

        pin_input = ft.TextField(
            label="Введите 4-значный PIN",
            password=True,
            max_length=4,
            width=340,
            hint_text="••••",
            text_style=ft.TextStyle(size=18)
        )
        error_text = ft.Text("", color=ft.Colors.RED_600, size=14)

        def check_pin(e):
            """Проверка введённого PIN-кода и открытие чата при успехе"""
            if pin_input.value == self.stored_pin:
                try:
                    self.api_client = OpenRouterClient(api_key=self.stored_api_key)
                    self.open_main_app()
                except:
                    error_text.value = "Ключ больше не валиден"
                    self.page.update()
            else:
                error_text.value = "Неверный PIN"
                pin_input.value = ""
                self.page.update()

        def reset_key(e):
            """Полный сброс аутентификации — удаление ключа и PIN"""
            self.cache.clear_auth()
            self.stored_api_key = None
            self.stored_pin = None
            self.show_key_entry_screen()

        self.page.add(
            ft.Column([
                ft.Text("Вход по PIN-коду", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                pin_input,
                error_text,
                ft.Row([
                    ft.ElevatedButton("Войти", on_click=check_pin, width=200),
                    ft.TextButton("Сбросить ключ", on_click=reset_key),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=40)
        )
        self.page.update()

    def open_main_app(self):
        """
        Переход к основному интерфейсу чата после успешной аутентификации.
        Полностью очищает страницу и восстанавливает оригинальные стили.
        """
        self.page.controls.clear()
        self.page.overlay.clear()
        self.page.dialog = None
        
        # Восстановление оригинальных стилей страницы из AppStyles
        for key, value in AppStyles.PAGE_SETTINGS.items():
            setattr(self.page, key, value)
        AppStyles.set_window_size(self.page)
        self.page.update()

        self.build_chat_interface()                # Сборка основного интерфейса
        self.page.update()

    def build_chat_interface(self):
        """
        Сборка основного интерфейса чата.
        Вызывается только после успешного входа.
        """
        # Загрузка моделей и установка первой по умолчанию
        models = self.api_client.available_models
        self.model_dropdown = ModelSelector(models)
        self.model_dropdown.value = models[0]['id'] if models else None

        # Отображение баланса
        self.balance_text = ft.Text("Баланс: Загрузка...", **AppStyles.BALANCE_TEXT)
        self.update_balance()

        # История чата
        self.chat_history = ft.ListView(**AppStyles.CHAT_HISTORY)
        self.load_chat_history()

        # Поле ввода сообщения
        self.message_input = ft.TextField(**AppStyles.MESSAGE_INPUT)

        async def send_message_click(e):
            """Асинхронная отправка сообщения и получение ответа от модели"""
            if not self.message_input.value.strip():
                return
            try:
                self.message_input.border_color = ft.Colors.BLUE_400
                self.page.update()

                start_time = time.time()
                user_message = self.message_input.value
                self.message_input.value = ""
                self.page.update()

                # Добавляем сообщение пользователя
                self.chat_history.controls.append(MessageBubble(message=user_message, is_user=True))

                # Индикатор загрузки
                loading = ft.ProgressRing(width=20, height=20)
                self.chat_history.controls.append(loading)
                self.page.update()

                # Асинхронный запрос к API
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.api_client.send_message(user_message, self.model_dropdown.value)
                )

                # Убираем индикатор загрузки
                self.chat_history.controls.remove(loading)

                # Обработка ответа от API
                if "error" in response:
                    response_text = f"Ошибка API: {response['error']}"
                    tokens_used = 0
                    self.logger.error(f"API Error: {response['error']}")
                else:
                    response_text = response["choices"][0]["message"]["content"]
                    tokens_used = response.get("usage", {}).get("total_tokens", 0)

                # Сохраняем сообщение в базу
                self.cache.save_message(
                    model=self.model_dropdown.value,
                    user_message=user_message,
                    ai_response=response_text,
                    tokens_used=tokens_used
                )

                # Добавляем ответ AI
                self.chat_history.controls.append(MessageBubble(message=response_text, is_user=False))

                # Обновляем аналитику
                response_time = time.time() - start_time
                self.analytics.track_message(
                    model=self.model_dropdown.value,
                    message_length=len(user_message),
                    response_time=response_time,
                    tokens_used=tokens_used
                )

                self.monitor.log_metrics(self.logger)
                self.page.update()

            except Exception as ex:
                self.logger.error(f"Ошибка отправки сообщения: {ex}")
                self.message_input.border_color = ft.Colors.RED_400
                self.page.update()

        def show_analytics(e):
            """Открытие окна аналитики использования приложения"""
            stats = self.analytics.get_statistics()
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Аналитика использования"),
                content=ft.Column([
                    ft.Text(f"Всего сообщений: {stats['total_messages']}"),
                    ft.Text(f"Всего токенов: {stats['total_tokens']}"),
                    ft.Text(f"Среднее токенов/сообщение: {stats['tokens_per_message']:.1f}"),
                    ft.Text(f"Сообщений в минуту: {stats['messages_per_minute']:.1f}"),
                ], scroll=ft.ScrollMode.AUTO, width=400, height=300),
                actions=[
                    ft.TextButton("Закрыть", on_click=lambda e: self.close_dialog())
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

        def clear_chat_data():
            """Полная очистка истории чата и аналитики"""
            self.cache.clear_history()
            self.analytics.clear_data()
            self.chat_history.controls.clear()
            self.page.update()

        def confirm_clear_history(e):
            """Диалог подтверждения полной очистки истории"""
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Очистить всю историю?"),
                content=ft.Text("Это действие нельзя отменить."),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda e: self.close_dialog()),
                    ft.TextButton("Очистить", style=ft.ButtonStyle(color=ft.Colors.RED), 
                                 on_click=lambda e: (clear_chat_data(), self.close_dialog()))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

        def save_dialog(e):
            """Экспорт полной истории чата в JSON-файл"""
            try:
                history = self.cache.get_chat_history()
                dialog_data = []
                for msg in history:
                    dialog_data.append({
                        "timestamp": str(msg[4]),
                        "model": msg[1],
                        "user_message": msg[2],
                        "ai_response": msg[3],
                        "tokens_used": msg[5]
                    })

                # Формируем имя файла с текущей датой и временем
                filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.exports_dir, filename)

                # Записываем в файл
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dialog_data, f, ensure_ascii=False, indent=2, default=str)

                # Окно успешного сохранения
                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Диалог сохранён"),
                    content=ft.Column([
                        ft.Text("Путь:"),
                        ft.Text(filepath, selectable=True, weight=ft.FontWeight.BOLD)
                    ]),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: self.close_dialog()),
                        ft.TextButton("Открыть папку", on_click=lambda e: (os.startfile(self.exports_dir), self.close_dialog()))
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                self.page.dialog = dlg
                dlg.open = True
                self.page.update()

            except Exception as ex:
                self.logger.error(f"Ошибка сохранения: {ex}")

        # Создание кнопок управления
        save_button = ft.ElevatedButton(on_click=save_dialog, **AppStyles.SAVE_BUTTON)
        clear_button = ft.ElevatedButton(on_click=confirm_clear_history, **AppStyles.CLEAR_BUTTON)
        send_button = ft.ElevatedButton(on_click=send_message_click, **AppStyles.SEND_BUTTON)
        analytics_button = ft.ElevatedButton(on_click=show_analytics, **AppStyles.ANALYTICS_BUTTON)

        # Нижняя панель с кнопками
        control_buttons = ft.Row(controls=[save_button, analytics_button, clear_button], **AppStyles.CONTROL_BUTTONS_ROW)
        input_row = ft.Row(controls=[self.message_input, send_button], **AppStyles.INPUT_ROW)
        controls_column = ft.Column(controls=[input_row, control_buttons], **AppStyles.CONTROLS_COLUMN)

        # Выбор модели и баланс
        balance_container = ft.Container(content=self.balance_text, **AppStyles.BALANCE_CONTAINER)
        model_selection = ft.Column(
            controls=[self.model_dropdown.search_field, self.model_dropdown, balance_container],
            **AppStyles.MODEL_SELECTION_COLUMN
        )

        # Основная колонка приложения
        main_column = ft.Column(
            controls=[model_selection, self.chat_history, controls_column],
            **AppStyles.MAIN_COLUMN
        )

        self.page.add(main_column)
        self.monitor.get_metrics()
        self.logger.info("Чат открыт успешно")

    def update_balance(self):
        """Обновление отображения баланса аккаунта OpenRouter"""
        if not self.api_client:
            return
        try:
            balance = self.api_client.get_balance()
            self.balance_text.value = f"Баланс: {balance}"
            self.balance_text.color = ft.Colors.GREEN_400
        except:
            self.balance_text.value = "Баланс: н/д"
            self.balance_text.color = ft.Colors.RED_400
        self.page.update()

    def load_chat_history(self):
        """Загрузка сохранённой истории чата из базы данных при запуске"""
        try:
            history = self.cache.get_chat_history()
            for msg in reversed(history):
                _, model, user_message, ai_response, timestamp, tokens = msg
                self.chat_history.controls.extend([
                    MessageBubble(message=user_message, is_user=True),
                    MessageBubble(message=ai_response, is_user=False)
                ])
        except Exception as e:
            self.logger.error(f"Ошибка загрузки истории: {e}")


def main():
    """Точка входа в приложение"""
    app = ChatApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()