# Импорт необходимых библиотек и модулей
import sys                                         # Модуль для работы с системными функциями
import os                                          # Библиотека для работы с операционной системой
sys.path.insert(0, os.path.dirname(__file__))      # Добавление директории src в путь для импортов

import flet as ft                                  # Фреймворк для создания кроссплатформенных приложений с современным UI
from api.openrouter import OpenRouterClient        # Клиент для взаимодействия с AI API через OpenRouter
from ui.styles import AppStyles                    # Модуль с настройками стилей интерфейса
from ui.components import MessageBubble, ModelSelector, LoginWindow, LoginContainer  # Компоненты пользовательского интерфейса
from utils.cache import ChatCache                  # Модуль для кэширования истории чата
from utils.logger import AppLogger                 # Модуль для логирования работы приложения
from utils.analytics import Analytics              # Модуль для сбора и анализа статистики использования
from utils.monitor import PerformanceMonitor       # Модуль для мониторинга производительности
import asyncio                                     # Библиотека для асинхронного программирования
import time                                        # Библиотека для работы с временными метками
import json                                        # Библиотека для работы с JSON-данными
from datetime import datetime                      # Класс для работы с датой и временем

class ChatApp:
    """
    Основной класс приложения чата.
    Управляет всей логикой работы приложения, включая UI и взаимодействие с API.
    """
    def __init__(self):
        """
        Инициализация основных компонентов приложения:
        - Система кэширования для сохранения истории и аутентификационных данных
        - Система логирования для отслеживания работы
        - Система аналитики для сбора статистики
        - Система мониторинга для отслеживания производительности
        - API клиент инициализируется после аутентификации
        """
        # Инициализация основных компонентов
        self.cache = ChatCache()                   # Инициализация системы кэширования
        self.logger = AppLogger()                  # Инициализация системы логирования
        self.monitor = PerformanceMonitor()        # Инициализация системы мониторинга

        # API клиент и аналитика инициализируются после аутентификации
        self.api_client = None
        self.analytics = None

        # Создание компонента для отображения баланса API (инициализируется после аутентификации)
        self.balance_text = None

        # Создание директории для экспорта истории чата
        self.exports_dir = "exports"               # Путь к директории экспорта
        os.makedirs(self.exports_dir, exist_ok=True)  # Создание директории, если её нет

    def initialize_after_auth(self):
        """
        Инициализация компонентов, требующих API ключа после успешной аутентификации.
        """
        auth_data = self.cache.get_auth_data()
        if not auth_data:
            raise ValueError("Нет аутентификационных данных")

        # Логирование используемого ключа (для отладки - скрываем значение)
        self.logger.debug(f"Initializing with API key: {auth_data['api_key'][:10]}...")

        # Инициализация API клиента с сохраненным ключом
        self.api_client = OpenRouterClient(api_key=auth_data['api_key'])
        self.analytics = Analytics(self.cache)     # Инициализация системы аналитики

        # Создание компонента для отображения баланса API
        self.balance_text = ft.Text(
            "Баланс: н/д",                         # Начальный текст до загрузки реального баланса
            **AppStyles.BALANCE_TEXT               # Применение стилей из конфигурации
        )
        self.update_balance()                      # Первичное обновление баланса (временно отключено)

    def load_chat_history(self):
        """
        Загрузка истории чата из кэша и отображение её в интерфейсе.
        Сообщения добавляются в обратном порядке для правильной хронологии.
        """
        try:
            history = self.cache.get_chat_history()    # Получение истории из кэша
            for msg in reversed(history):              # Перебор сообщений в обратном порядке
                # Распаковка данных сообщения в отдельные переменные
                _, model, user_message, ai_response, timestamp, tokens = msg
                # Добавление пары сообщений (пользователь + AI) в интерфейс
                self.chat_history.controls.extend([
                    MessageBubble(                     # Создание пузырька сообщения пользователя
                        message=user_message,
                        is_user=True
                    ),
                    MessageBubble(                     # Создание пузырька ответа AI
                        message=ai_response,
                        is_user=False
                    )
                ])
        except Exception as e:
            # Логирование ошибки при загрузке истории
            self.logger.error(f"Ошибка загрузки истории чата: {e}")

    def update_balance(self):
        """
        Обновление отображения баланса API в интерфейсе.
        При успешном получении баланса показывает его зеленым цветом,
        при ошибке - красным с текстом 'н/д' (не доступен).
        """
        try:
            # Логирование попытки получения баланса
            self.logger.info("Запрос баланса через API")
            balance = self.api_client.get_balance()         # Запрос баланса через API
            self.logger.info(f"Баланс получен: {balance}")

            self.balance_text.value = f"Баланс: {balance}"  # Обновление текста с балансом
            self.balance_text.color = ft.Colors.GREEN_400   # Установка зеленого цвета для успешного получения
        except Exception as e:
            # Обработка ошибки получения баланса
            self.logger.error(f"Ошибка обновления баланса: {e}")
            self.balance_text.value = "Баланс: н/д"         # Установка текста ошибки
            self.balance_text.color = ft.Colors.RED_400     # Установка красного цвета для ошибки
            
    def show_main_ui(self, page: ft.Page):
        """
        Отображение основного интерфейса приложения после успешной аутентификации.
        """
        # Очистка страницы перед добавлением нового UI
        page.controls.clear()

        # Простое тестовое UI без сложных компонентов
        #test_text = ft.Text("Главный интерфейс загружен!", size=24, color=ft.Colors.GREEN_400)
        #test_button = ft.ElevatedButton("Тест", on_click=lambda e: page.update())

        #simple_column = ft.Column(
        #    controls=[test_text, test_button],
        #    alignment=ft.MainAxisAlignment.CENTER,
        #    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        #)

        #page.add(simple_column)
        #page.update()

        #return  # Прерываем выполнение, возвращаем простое UI для тестирования

        # Применение базовых настроек страницы из конфигурации стилей
        for key, value in AppStyles.PAGE_SETTINGS.items():
            setattr(page, key, value)

        AppStyles.set_window_size(page)    # Установка размеров окна приложения

        # Инициализация выпадающего списка для выбора модели AI
        models = self.api_client.available_models
        self.model_dropdown = ModelSelector(models)
        self.model_dropdown.value = models[0] if models else None

        async def send_message_click(e):
            """
            Асинхронная функция отправки сообщения.
            """
            if not self.message_input.value:
                return

            try:
                # Визуальная индикация процесса
                self.message_input.border_color = ft.Colors.BLUE_400
                page.update()

                # Сохранение данных сообщения
                start_time = time.time()
                user_message = self.message_input.value
                self.message_input.value = ""
                page.update()

                # Добавление сообщения пользователя
                self.chat_history.controls.append(
                    MessageBubble(message=user_message, is_user=True)
                )

                # Индикатор загрузки
                loading = ft.ProgressRing()
                self.chat_history.controls.append(loading)
                page.update()

                # Асинхронная отправка запроса
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.api_client.send_message(
                        user_message, 
                        self.model_dropdown.value
                    )
                )

                # Удаление индикатора загрузки
                self.chat_history.controls.remove(loading)

                # Обработка ответа
                if "error" in response:
                    response_text = f"Ошибка: {response['error']}"
                    tokens_used = 0
                    self.logger.error(f"Ошибка API: {response['error']}")
                else:
                    response_text = response["choices"][0]["message"]["content"]
                    tokens_used = response.get("usage", {}).get("total_tokens", 0)

                # Сохранение в кэш
                self.cache.save_message(
                    model=self.model_dropdown.value,
                    user_message=user_message,
                    ai_response=response_text,
                    tokens_used=tokens_used
                )

                # Добавление ответа в чат
                self.chat_history.controls.append(
                    MessageBubble(message=response_text, is_user=False)
                )

                # Обновление аналитики
                response_time = time.time() - start_time
                self.analytics.track_message(
                    model=self.model_dropdown.value,
                    message_length=len(user_message),
                    response_time=response_time,
                    tokens_used=tokens_used
                )

                # Логирование метрик
                self.monitor.log_metrics(self.logger)
                page.update()

            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения: {e}")
                self.message_input.border_color = ft.Colors.RED_500

                # Показ уведомления об ошибке
                snack = ft.SnackBar(
                    content=ft.Text(
                        str(e),
                        color=ft.Colors.RED_500,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    duration=5000,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()

        def show_error_snack(page, message: str):
            """Показ уведомления об ошибке"""
            snack = ft.SnackBar(                  # Создание уведомления
                content=ft.Text(
                    message,
                    color=ft.Colors.RED_500
                ),
                bgcolor=ft.Colors.GREY_900,
                duration=5000,
            )
            page.overlay.append(snack)            # Добавление уведомления
            snack.open = True                     # Открытие уведомления
            page.update()                         # Обновление страницы


        async def show_analytics(e):
            """Показ статистики использования"""
            stats = self.analytics.get_statistics()    # Получение статистики

            # Создание диалога статистики
            dialog = ft.AlertDialog(
                title=ft.Text("Аналитика"),
                content=ft.Column([
                    ft.Text(f"Всего сообщений: {stats['total_messages']}"),
                    ft.Text(f"Всего токенов: {stats['total_tokens']}"),
                    ft.Text(f"Среднее токенов/сообщение: {stats['tokens_per_message']:.2f}"),
                    ft.Text(f"Сообщений в минуту: {stats['messages_per_minute']:.2f}")
                ]),
                actions=[
                    ft.TextButton("Закрыть", on_click=lambda e: close_dialog(dialog)),
                ],
            )

            page.overlay.append(dialog)           # Добавление диалога
            dialog.open = True                    # Открытие диалога
            page.update()                         # Обновление страницы

        async def clear_history(e):
            """
            Очистка истории чата.
            """
            try:
                self.cache.clear_history()          # Очистка кэша
                self.analytics.clear_data()         # Очистка аналитики
                self.chat_history.controls.clear()  # Очистка истории чата
                
            except Exception as e:
                self.logger.error(f"Ошибка очистки истории: {e}")
                show_error_snack(page, f"Ошибка очистки истории: {str(e)}")


        async def confirm_clear_history(e):
            """Подтверждение очистки истории"""
            def close_dlg(e):                     # Функция закрытия диалога
                close_dialog(dialog)

            async def clear_confirmed(e):         # Функция подтверждения очистки
                await clear_history(e)
                close_dialog(dialog)
                

            # Создание диалога подтверждения
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Подтверждение удаления"),
                content=ft.Text("Вы уверены? Это действие нельзя отменить!"),
                actions=[
                    ft.TextButton("Отмена", on_click=close_dlg),
                    ft.TextButton("Очистить", on_click=clear_confirmed),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.overlay.append(dialog)
            dialog.open = True
            page.update()
            
        def close_dialog(dialog):
            """Закрытие диалогового окна"""
            dialog.open = False                   # Закрытие диалога
            page.update()                         # Обновление страницы
                                    
            if dialog in page.overlay:            # Удаление из overlay
                page.overlay.remove(dialog)
      

        async def save_dialog(e):
            """
            Сохранение истории диалога в JSON файл.
            """
            try:
                # Получение истории из кэша
                history = self.cache.get_chat_history()

                # Форматирование данных для сохранения
                dialog_data = []
                for msg in history:
                    dialog_data.append({
                        "timestamp": msg[4],
                        "model": msg[1],
                        "user_message": msg[2],
                        "ai_response": msg[3],
                        "tokens_used": msg[5]
                    })

                # Создание имени файла
                filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.exports_dir, filename)

                # Сохранение в JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dialog_data, f, ensure_ascii=False, indent=2, default=str)

                # Создание диалога успешного сохранения
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Диалог сохранен"),
                    content=ft.Column([
                        ft.Text("Путь сохранения:"),
                        ft.Text(filepath, selectable=True, weight=ft.FontWeight.BOLD),
                    ]),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: close_dialog(dialog)),
                        ft.TextButton("Открыть папку", 
                            on_click=lambda e: os.startfile(self.exports_dir)
                        ),
                    ],
                )

                page.overlay.append(dialog)
                dialog.open = True
                page.update()

            except Exception as e:
                self.logger.error(f"Ошибка сохранения: {e}")
                show_error_snack(page, f"Ошибка сохранения: {str(e)}")

    

        # Создание компонентов интерфейса
        self.message_input = ft.TextField(**AppStyles.MESSAGE_INPUT) # Поле ввода
        self.chat_history = ft.ListView(**AppStyles.CHAT_HISTORY)    # История чата

        # Загрузка существующей истории
        self.load_chat_history()

        # Создание кнопок управления
        save_button = ft.ElevatedButton(
            on_click=save_dialog,           # Привязка функции сохранения
            **AppStyles.SAVE_BUTTON         # Применение стилей
        )

        clear_button = ft.ElevatedButton(
            on_click=confirm_clear_history, # Привязка функции очистки
            **AppStyles.CLEAR_BUTTON        # Применение стилей
        )

        send_button = ft.ElevatedButton(
            on_click=send_message_click,    # Привязка функции отправки
            **AppStyles.SEND_BUTTON         # Применение стилей
        )

        analytics_button = ft.ElevatedButton(
            on_click=show_analytics,        # Привязка функции аналитики
            **AppStyles.ANALYTICS_BUTTON    # Применение стилей
        )

        # Создание layout компонентов
        
        # Создание ряда кнопок управления
        control_buttons = ft.Row(  
            controls=[                      # Размещение кнопок в ряд
                save_button,
                analytics_button,
                clear_button
            ],
            **AppStyles.CONTROL_BUTTONS_ROW # Применение стилей к ряду
        )

        # Создание строки ввода с кнопкой отправки
        input_row = ft.Row(
            controls=[                      # Размещение элементов ввода
                self.message_input,
                send_button
            ],
            **AppStyles.INPUT_ROW           # Применение стилей к строке ввода
        )

        # Создание колонки для элементов управления
        controls_column = ft.Column(
            controls=[                      # Размещение элементов управления
                input_row,
                control_buttons
            ],
            **AppStyles.CONTROLS_COLUMN     # Применение стилей к колонке
        )

        # Создание контейнера для баланса
        balance_container = ft.Container(
            content=self.balance_text,            # Размещение текста баланса
            **AppStyles.BALANCE_CONTAINER        # Применение стилей к контейнеру
        )

        # Создание колонки выбора модели
        model_selection = ft.Column(
            controls=[                            # Размещение элементов выбора модели
                self.model_dropdown.search_field,
                self.model_dropdown,
                balance_container
            ],
            **AppStyles.MODEL_SELECTION_COLUMN   # Применение стилей к колонке
        )

                # Создание основной колонки приложения
        self.main_column = ft.Column(
            controls=[                            # Размещение основных элементов
                model_selection,
                self.chat_history,
                controls_column
            ],
            **AppStyles.MAIN_COLUMN               # Применение стилей к главной колонке
        )

        # Добавление основной колонки на страницу
        page.add(self.main_column)

        # Финальное обновление страницы для рендеринга всех компонентов
        page.update()

        # Запуск монитора
        self.monitor.get_metrics()

        # Логирование запуска
        self.logger.info("Приложение запущено")

    def show_login_window(self, page: ft.Page):
        """
        Отображение окна входа в систему используя обычный контейнер вместо модального диалога.
        """
        # Создание обычного контейнера вместо модального диалога для лучшей совместимости
        login_container = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Вход в систему", size=20, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        # Элементы входа будут добавлены при создании логин компонента
                        ft.Text("Загрузка...", size=16)
                    ], spacing=20),
                    padding=30,
                    width=450,
                    height=350
                )
            ),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.GREY_900,
        )

        # Создание постоянного компонента входа
        login_component = LoginContainer(self.cache, OpenRouterClient)

        # Настройка обработчика успешного входа
        def on_login_success():
            """Обработчик успешного входа"""
            # Инициализация после аутентификации
            self.initialize_after_auth()

            # Переход к основному интерфейсу
            page.controls.clear()
            self.show_main_ui(page)

        login_component.on_success = on_login_success
        login_container.content.content.content.controls[2] = login_component
        login_component.page = page

        # Добавление на страницу
        page.add(login_container)
        page.update()

    def main(self, page: ft.Page):
        """
        Основная функция инициализации интерфейса приложения.
        Всегда показывает окно аутентификации перед основным интерфейсом.
        """
        self.show_login_window(page)

def main():
    """Точка входа в приложение"""
    app = ChatApp()                              # Создание экземпляра приложения
    # Запуск приложения
    ft.app(target=app.main)
    #ft.app(target=app.main, view=ft.WEB_BROWSER)


if __name__ == "__main__":
    main()                                       # Запуск если файл запущен напрямую
