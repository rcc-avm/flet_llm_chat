# Импорт необходимых библиотек и модулей
import flet as ft                  # Фреймворк для создания пользовательского интерфейса
from ui.styles import AppStyles    # Импорт стилей приложения
import asyncio                     # Библиотека для асинхронного программирования

class MessageBubble(ft.Container):
    """
    Компонент "пузырька" сообщения в чате.
    
    Наследуется от ft.Container для создания стилизованного контейнера сообщения.
    Отображает сообщения пользователя и AI с разными стилями и позиционированием.
    
    Args:
        message (str): Текст сообщения для отображения
        is_user (bool): Флаг, указывающий, является ли это сообщением пользователя
    """
    def __init__(self, message: str, is_user: bool):
        # Инициализация родительского класса Container
        super().__init__()
        
        # Настройка отступов внутри пузырька
        self.padding = 10
        
        # Настройка скругления углов пузырька
        self.border_radius = 10
        
        # Установка цвета фона в зависимости от отправителя:
        # - Синий для сообщений пользователя
        # - Серый для сообщений AI
        self.bgcolor = ft.Colors.BLUE_700 if is_user else ft.Colors.GREY_700
        
        # Установка выравнивания пузырька:
        # - Справа для сообщений пользователя
        # - Слева для сообщений AI
        self.alignment = ft.alignment.center_right if is_user else ft.alignment.center_left
        
        # Настройка внешних отступов для создания эффекта диалога:
        # - Отступ слева для сообщений пользователя
        # - Отступ справа для сообщений AI
        # - Небольшие отступы сверху и снизу для разделения сообщений
        self.margin = ft.margin.only(
            left=50 if is_user else 0,      # Отступ слева
            right=0 if is_user else 50,      # Отступ справа
            top=5,                           # Отступ сверху
            bottom=5                         # Отступ снизу
        )
        
        # Создание содержимого пузырька
        self.content = ft.Column(
            controls=[
                # Текст сообщения с настройками отображения
                ft.Text(
                    value=message,                    # Текст сообщения
                    color=ft.Colors.WHITE,            # Белый цвет текста
                    size=16,                         # Размер шрифта
                    selectable=True,                 # Возможность выделения текста
                    weight=ft.FontWeight.W_400       # Нормальная толщина шрифта
                )
            ],
            tight=True  # Плотное расположение элементов в колонке
        )


class ModelSelector(ft.Dropdown):
    """
    Выпадающий список для выбора AI модели с функцией поиска.

    Наследуется от ft.Dropdown для создания кастомного выпадающего списка
    с дополнительным полем поиска для фильтрации моделей.

    Args:
        models (list): Список доступных моделей в формате:
                      [{"id": "model-id", "name": "Model Name"}, ...]
    """
    def __init__(self, models: list):
        # Инициализация родительского класса Dropdown
        super().__init__()

        # Применение стилей из конфигурации к компоненту
        for key, value in AppStyles.MODEL_DROPDOWN.items():
            setattr(self, key, value)

        # Настройка внешнего вида выпадающего списка
        self.label = None                    # Убираем текстовую метку
        self.hint_text = "Выбор модели"      # Текст-подсказка

        # Создание списка опций из предоставленных моделей
        self.options = [
            ft.dropdown.Option(
                key=model['id'],             # ID модели как ключ
                text=model['name']           # Название модели как отображаемый текст
            ) for model in models
        ]

        # Сохранение полного списка опций для фильтрации
        self.all_options = self.options.copy()

        # Установка начального значения (первая модель из списка)
        self.value = models[0]['id'] if models else None

        # Создание поля поиска для фильтрации моделей
        self.search_field = ft.TextField(
            on_change=self.filter_options,        # Функция обработки изменений
            hint_text="Поиск модели",            # Текст-подсказка в поле поиска
            **AppStyles.MODEL_SEARCH_FIELD       # Применение стилей из конфигурации
        )

    def filter_options(self, e):
        """
        Фильтрация списка моделей на основе введенного текста поиска.

        Args:
            e: Событие изменения текста в поле поиска
        """
        # Получение текста поиска в нижнем регистре
        search_text = self.search_field.value.lower() if self.search_field.value else ""

        # Если поле поиска пустое - показываем все модели
        if not search_text:
            self.options = self.all_options
        else:
            # Фильтрация моделей по тексту поиска
            # Ищем совпадения в названии или ID модели
            self.options = [
                opt for opt in self.all_options
                if search_text in opt.text.lower() or search_text in opt.key.lower()
            ]

        # Обновление интерфейса для отображения отфильтрованного списка
        e.page.update()


class LoginWindow(ft.AlertDialog):
    """
    Окно аутентификации (входа в систему).

    Модальное диалоговое окно для аутентификации пользователей.
    Поддерживает два режима:
    - Первый вход: ввод API ключа и генерация PIN
    - Повторный вход: ввод PIN-кода

    Args:
        cache (ChatCache): Экземпляр класса кэширования для хранения данных аутентификации
        api_client_class: Класс клиента API для валидации ключа
    """

    def __init__(self, cache, api_client_class):
        # Сохранение ссылок на кэш и класс API клиента
        self.cache = cache
        self.api_client_class = api_client_class

        # Флаги состояния
        self.auth_data_exists = bool(self.cache.get_auth_data())  # Проверяем, есть ли сохраненные данные
        self.is_first_login = not self.auth_data_exists
        self.reset_mode = False  # Режим сброса ключа
        self.pin_generated = False  # Флаг, что PIN был сгенерирован и показан

        # Создание элементов интерфейса
        self.create_ui_elements()

        # Инициализация родительского класса AlertDialog
        super().__init__(
            modal=False,                   # Немодальный диалог для лучшей совместимости
            title=ft.Text("Вход в систему"),  # Заголовок диалогового окна
            content=self.content_column,   # Основное содержимое
            actions=self.get_actions(),    # Кнопки действий
            actions_alignment=ft.MainAxisAlignment.END,  # Выравнивание кнопок по правому краю
        )

    def create_ui_elements(self):
        """
        Создание элементов пользовательского интерфейса диалогового окна.
        """
        # Поле ввода API ключа для первого входа или сброса
        self.api_key_field = ft.TextField(
            label="Введите ключ API OpenRouter.ai",
            hint_text="sk-or-v1-xxxxxxxxxxxx",
            password=True,  # Скрытый ввод (точки вместо символов)
            width=400,
            max_length=100,
        )

        # Поле ввода PIN-кода для повторных входов
        self.pin_field = ft.TextField(
            label="Введите ваш PIN-код",
            hint_text="4 цифры",
            password=True,  # Скрытый ввод
            width=400,
            max_length=4,
            input_filter=ft.NumbersOnlyInputFilter(),  # Только цифры
        )

        # Поле отображения сгенерированного PIN
        self.pin_display_field = ft.TextField(
            label="Ваш PIN-код для будущих входов",
            read_only=True,
            width=400,
            text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD),
        )

        # Текстовое поле для отображения информации и ошибок
        self.info_text = ft.Text("", color=ft.colors.BLUE_400, size=14)

        # Создание колонки с элементами в зависимости от режима
        self.content_column = ft.Column(
            controls=self.get_content_controls(),
            tight=True,
            spacing=10,
        )

    def get_content_controls(self):
        """
        Получение списка элементов управления в зависимости от текущего режима.

        Returns:
            list: Список элементов управления для отображения
        """
        controls = []

        if self.pin_generated:
            # PIN сгенерирован и отображен
            controls.extend([
                self.pin_display_field,
                self.info_text,
            ])
        elif self.is_first_login or self.reset_mode:
            # Режим первого входа или сброса: показываем поле API ключа
            controls.extend([
                self.api_key_field,
                self.info_text,
            ])
        else:
            # Режим повторного входа: показываем поле PIN
            controls.extend([
                self.pin_field,
                self.info_text,
            ])

        return controls

    def get_actions(self):
        """
        Получение списка кнопок действий в зависимости от состояния.

        Returns:
            list: Список кнопок действий
        """
        if self.pin_generated:
            # Когда PIN показан, кнопка OK для закрытия
            return [
                ft.TextButton("OK", on_click=self.close_dialog),
            ]
        elif self.is_first_login or self.reset_mode:
            # Режим первого входа: кнопки войти и сброс (если данные существуют)
            actions = [ft.TextButton("Войти", on_click=self.handle_login)]
            if self.auth_data_exists:
                actions.append(ft.TextButton("Сбросить ключ", on_click=self.toggle_reset_mode))
            return actions
        else:
            # Режим PIN входа: кнопки войти и сброс
            return [
                ft.TextButton("Войти", on_click=self.handle_login),
                ft.TextButton("Сбросить ключ", on_click=self.toggle_reset_mode),
            ]

    def update_actions(self):
        """
        Обновление кнопок действий.
        """
        self.actions = self.get_actions()

    def update_content(self):
        """
        Обновление содержимого диалогового окна после изменения режима.
        """
        # Обновление списка элементов управления
        self.content_column.controls = self.get_content_controls()
        # Сброс информационного текста
        self.info_text.value = ""

    def toggle_reset_mode(self, e):
        """
        Переключение в режим сброса API ключа.

        Args:
            e: Событие нажатия кнопки
        """
        self.reset_mode = not self.reset_mode
        self.pin_generated = False  # Сброс флага PIN
        self.update_content()
        self.update_actions()
        self.page.update()

    def handle_login(self, e):
        """
        Обработка попытки входа в систему.

        Args:
            e: Событие нажатия кнопки входа
        """
        try:
            if self.is_first_login or self.reset_mode:
                # Обработка первого входа или сброса ключа
                self.handle_first_login()
            else:
                # Обработка повторного входа с PIN
                self.handle_pin_login()
        except Exception as ex:
            # Обработка ошибок входа
            self.info_text.value = f"Ошибка: {str(ex)}"
            self.info_text.color = ft.colors.RED_400

    def handle_first_login(self):
        """
        Обработка первого входа системы (ввод API ключа).
        """
        api_key = self.api_key_field.value

        if not api_key:
            self.info_text.value = "Введите API ключ"
            self.info_text.color = ft.colors.RED_400
            return

        # Валидация API ключа через баланс
        if not self.validate_api_key(api_key):
            self.info_text.value = "Неверный API ключ или недостаточно кредитов"
            self.info_text.color = ft.colors.RED_400
            return

        # Генерация PIN-кода на основе API ключа
        pin = self.cache.generate_pin(api_key)

        # Сохранение данных аутентификации
        self.cache.save_auth_data(api_key, pin)

        # Отображение PIN в специальном поле
        self.pin_display_field.value = pin
        self.pin_generated = True

        # Информационное сообщение
        self.info_text.value = "PIN успешно создан и сохранен! Используйте его для будущих входов."
        self.info_text.color = ft.colors.GREEN_400

        # Обновление интерфейса
        self.update_content()
        self.update_actions()
        self.page.update()

    def close_dialog(self, e):
        """
        Закрытие диалогового окна.
        """
        self.open = False
        if self.page:
            self.page.update()

    def handle_pin_login(self):
        """
        Обработка входа с использованием PIN-кода.
        """
        entered_pin = self.pin_field.value

        if not entered_pin or len(entered_pin) != 4:
            self.info_text.value = "Введите 4-значный PIN"
            self.info_text.color = ft.colors.RED_400
            return

        # Проверка PIN
        if not self.cache.verify_pin(entered_pin):
            self.info_text.value = "Неверный PIN"
            self.info_text.color = ft.colors.RED_400
            return

        # Успешный вход
        self.info_text.value = "Вход выполнен успешно!"
        self.info_text.color = ft.colors.GREEN_400

        # Немедленное закрытие окна через механизм close_after_delay с 0 задержкой
        self.page.run_task(self.close_after_delay, 0)

    def validate_api_key(self, api_key):
        """
        Валидация API ключа через проверку баланса.

        Args:
            api_key (str): API ключ для валидации

        Returns:
            bool: True если ключ валиден и баланс положительный
        """
        try:
            # Создание временного экземпляра API клиента с введенным ключом
            temp_client = self.api_client_class(api_key=api_key)
            balance = temp_client.get_balance()

            # Проверка, что баланс положительный (не ошибка и содержит $)
            return balance != "Ошибка" and "$" in balance
        except Exception:
            return False

    async def close_after_delay(self, delay_seconds):
        """
        Закрытие диалогового окна после задержки.

        Args:
            delay_seconds (int): Задержка в секундах перед закрытием
        """
        await asyncio.sleep(delay_seconds)
        self.open = False
        if self.page:
            self.page.update()


class LoginContainer(ft.Container):
    """
    Контейнер аутентификации (входа в систему) в виде обычного компонента UI.

    Регулярный контейнер без модального поведения для лучшей совместимости между
    desktop и browser режимами Flet.

    Args:
        cache (ChatCache): Экземпляр класса кэширования для хранения данных аутентификации
        api_client_class: Класс клиента API для валидации ключа
    """

    def __init__(self, cache, api_client_class):
        # Сохранение ссылок на кэш и класс API клиента
        self.cache = cache
        self.api_client_class = api_client_class

        # Флаги состояния
        self.auth_data_exists = bool(self.cache.get_auth_data())  # Проверяем, есть ли сохраненные данные
        self.is_first_login = not self.auth_data_exists
        self.reset_mode = False  # Режим сброса ключа
        self.pin_generated = False  # Флаг, что PIN был сгенерирован и показан

        # Колбэк для успешного входа
        self.on_success = None

        # Создание элементов интерфейса
        self.create_ui_elements()

        # Инициализация Контейнера
        super().__init__(
            content=ft.Column(
                controls=self.get_content_controls(),
                spacing=15,
                alignment=ft.MainAxisAlignment.START
            ),
            padding=20,
            width=400,
            height=300
        )

    def create_ui_elements(self):
        """
        Создание элементов пользовательского интерфейса контейнера.
        """
        # Текстовое поле для отображения информации и ошибок
        self.info_text = ft.Text("", color=ft.colors.BLUE_400, size=14)

        # Поле ввода API ключа для первого входа или сброса
        self.api_key_field = ft.TextField(
            label="Введите ключ API OpenRouter.ai",
            hint_text="sk-or-v1-xxxxxxxxxxxx",
            password=True,  # Скрытый ввод (точки вместо символов)
            width=350,
            max_length=100,
        )

        # Поле ввода PIN-кода для повторных входов
        self.pin_field = ft.TextField(
            label="Введите ваш PIN-код",
            hint_text="4 цифры",
            password=True,  # Скрытый ввод
            width=350,
            max_length=4,
            input_filter=ft.NumbersOnlyInputFilter(),  # Только цифры
        )

        # Поле отображения сгенерированного PIN
        self.pin_display_field = ft.TextField(
            label="Ваш PIN-код для будущих входов",
            read_only=True,
            width=350,
            text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD),
        )

        # Кнопки
        self.login_button = ft.ElevatedButton(
            text="Войти",
            on_click=self.handle_login,
            width=150,
            height=40
        )
        self.reset_button = ft.ElevatedButton(
            text="Сбросить ключ",
            on_click=self.toggle_reset_mode,
            width=150,
            height=40,
            visible=self.auth_data_exists
        )

    def get_content_controls(self):
        """
        Получение списка элементов управления в зависимости от текущего режима.

        Returns:
            list: Список элементов управления для отображения
        """
        controls = []

        if self.pin_generated:
            # PIN сгенерирован и отображен
            controls.extend([
                self.pin_display_field,
                self.info_text,
                ft.Row([
                    ft.ElevatedButton(
                        "OK",
                        on_click=self.close_container,
                        width=150,
                        height=40
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ])
        elif self.is_first_login or self.reset_mode:
            # Режим первого входа или сброса: показываем поле API ключа
            controls.extend([
                self.api_key_field,
                self.info_text,
                ft.Row([
                    self.login_button,
                    self.reset_button
                ], alignment=ft.MainAxisAlignment.CENTER)
            ])
        else:
            # Режим повторного входа: показываем поле PIN
            controls.extend([
                self.pin_field,
                self.info_text,
                ft.Row([
                    self.login_button,
                    self.reset_button
                ], alignment=ft.MainAxisAlignment.CENTER)
            ])

        return controls

    def update_content(self):
        """
        Обновление содержимого контейнера после изменения режима.
        """
        # Обновление списка элементов управления
        self.content.controls = self.get_content_controls()
        # Сброс информационного текста
        self.info_text.value = ""

    def toggle_reset_mode(self, e):
        """
        Переключение в режим сброса API ключа.

        Args:
            e: Событие нажатия кнопки
        """
        self.reset_mode = not self.reset_mode
        self.pin_generated = False  # Сброс флага PIN
        self.update_content()
        if self.page:
            self.page.update()

    def close_container(self, e):
        """
        Закрытие контейнера (вызывается после показа PIN).
        """
        if self.on_success:
            self.on_success()

    def handle_login(self, e):
        """
        Обработка попытки входа в систему.

        Args:
            e: Событие нажатия кнопки входа
        """
        try:
            if self.is_first_login or self.reset_mode:
                # Обработка первого входа или сброса ключа
                self.handle_first_login()
            else:
                # Обработка повторного входа с PIN
                self.handle_pin_login()
        except Exception as ex:
            # Обработка ошибок входа
            self.info_text.value = f"Ошибка: {str(ex)}"
            self.info_text.color = ft.colors.RED_400

    def handle_first_login(self):
        """
        Обработка первого входа системы (ввод API ключа).
        """
        api_key = self.api_key_field.value

        if not api_key:
            self.info_text.value = "Введите API ключ"
            self.info_text.color = ft.colors.RED_400
            return

        # Валидация API ключа через баланс
        if not self.validate_api_key(api_key):
            self.info_text.value = "Неверный API ключ или недостаточно кредитов"
            self.info_text.color = ft.colors.RED_400
            return

        # Генерация PIN-кода на основе API ключа
        pin = self.cache.generate_pin(api_key)

        # Сохранение данных аутентификации
        self.cache.save_auth_data(api_key, pin)

        # Отображение PIN в специальном поле
        self.pin_display_field.value = pin
        self.pin_generated = True

        # Информационное сообщение
        self.info_text.value = "PIN успешно создан и сохранен! Используйте его для будущих входов."
        self.info_text.color = ft.colors.GREEN_400

        # Обновление интерфейса
        self.update_content()
        if self.page:
            self.page.update()

    def handle_pin_login(self):
        """
        Обработка входа с использованием PIN-кода.
        """
        entered_pin = self.pin_field.value

        if not entered_pin or len(entered_pin) != 4:
            self.info_text.value = "Введите 4-значный PIN"
            self.info_text.color = ft.colors.RED_400
            return

        # Проверка PIN
        if not self.cache.verify_pin(entered_pin):
            self.info_text.value = "Неверный PIN"
            self.info_text.color = ft.colors.RED_400
            return

        # Успешный вход
        self.info_text.value = "Вход выполнен успешно!"
        self.info_text.color = ft.colors.GREEN_400

        # Вызов колбэка успешного входа
        if self.on_success:
            self.on_success()

    def validate_api_key(self, api_key):
        """
        Валидация API ключа через проверку баланса.

        Args:
            api_key (str): API ключ для валидации

        Returns:
            bool: True если ключ валиден и баланс положительный
        """
        try:
            # Создание временного экземпляра API клиента с введенным ключом
            temp_client = self.api_client_class(api_key=api_key)
            balance = temp_client.get_balance()

            # Проверка, что баланс положительный (не ошибка и содержит $)
            return balance != "Ошибка" and "$" in balance
        except Exception:
            return False
