# Импорт необходимых библиотек
import sqlite3                                     # Библиотека для работы с SQLite базой данных
from datetime import datetime                      # Класс для работы с датой и временем
import threading                                   # Библиотека для потокобезопасной работы с базой

class ChatCache:
    """
    Класс для кэширования истории чата и данных аутентификации в SQLite.
    
    Обеспечивает:
    - Потокобезопасное хранение сообщений и аналитики
    - Хранение API-ключа и PIN-кода
    - Очистку истории и аутентификации
    """
    def __init__(self):
        """
        Инициализация системы кэширования.
        
        Создаёт файл базы данных и необходимые таблицы.
        """
        self.db_name = 'chat_cache.db'
        self.local = threading.local()         # Потокобезопасное хранилище соединений
        self.create_tables()

    def get_connection(self):
        """
        Получение соединения с базой для текущего потока.
        
        Returns:
            sqlite3.Connection: Объект соединения
        """
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_name, check_same_thread=False)
        return self.local.connection

    def create_tables(self):
        """
        Создание всех необходимых таблиц в базе данных.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица сообщений чата
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                user_message TEXT,
                ai_response TEXT,
                timestamp DATETIME,
                tokens_used INTEGER
            )
        ''')

        # Таблица аналитики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                model TEXT,
                message_length INTEGER,
                response_time FLOAT,
                tokens_used INTEGER
            )
        ''')

        # Таблица аутентификации (ключ + PIN)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth (
                id INTEGER PRIMARY KEY,
                api_key TEXT NOT NULL,
                pin TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def save_message(self, model, user_message, ai_response, tokens_used):
        """
        Сохранение сообщения в историю чата.
        
        Args:
            model (str): ID модели
            user_message (str): Сообщение пользователя
            ai_response (str): Ответ модели
            tokens_used (int): Количество использованных токенов
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (model, user_message, ai_response, timestamp, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (model, user_message, ai_response, datetime.now(), tokens_used))
        conn.commit()

    def get_chat_history(self, limit=100):
        """
        Получение последних сообщений из истории.
        
        Args:
            limit (int): Максимальное количество сообщений
        
        Returns:
            list: Список кортежей с данными сообщений
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM messages 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def save_analytics(self, timestamp, model, message_length, response_time, tokens_used):
        """
        Сохранение данных аналитики.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics_messages 
            (timestamp, model, message_length, response_time, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, model, message_length, response_time, tokens_used))
        conn.commit()

    def get_analytics_history(self):
        """Получение всей истории аналитики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, model, message_length, response_time, tokens_used FROM analytics_messages ORDER BY timestamp ASC')
        return cursor.fetchall()

    def clear_history(self):
        """Полная очистка истории чата и аналитики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        cursor.execute('DELETE FROM analytics_messages')
        conn.commit()

    def set_api_key_and_pin(self, api_key: str, pin: str):
        """
        Сохранение API-ключа и PIN-кода.
        
        Args:
            api_key (str): Ключ от OpenRouter
            pin (str): 4-значный PIN-код
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth")  # Очищаем старую запись (хранится только одна)
        cursor.execute("INSERT INTO auth (api_key, pin) VALUES (?, ?)", (api_key, pin))
        conn.commit()

    def get_api_key_and_pin(self):
        """
        Получение сохранённых данных аутентификации.
        
        Returns:
            tuple: (api_key, pin) или (None, None)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT api_key, pin FROM auth")
        row = cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)

    def clear_auth(self):
        """Полный сброс аутентификации (удаление ключа и PIN)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth")
        conn.commit()