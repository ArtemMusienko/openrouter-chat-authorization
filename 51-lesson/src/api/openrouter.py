# Импорт необходимых библиотек
import requests                                    # Библиотека для выполнения HTTP-запросов к API OpenRouter
import os                                          # Библиотека для работы с переменными окружения
from dotenv import load_dotenv                     # Загрузка переменных из .env файла
from utils.logger import AppLogger                 # Собственный логгер для отслеживания работы клиента

load_dotenv()                                      # Загрузка .env при импорте модуля

class OpenRouterClient:
    """
    Клиент для работы с OpenRouter API.
    
    Обеспечивает:
    - Получение списка доступных моделей
    - Отправку сообщений выбранной модели
    - Получение текущего баланса аккаунта
    - Автоматическую обработку ошибок авторизации (401)
    """
    def __init__(self, api_key=None):
        """
        Инициализация клиента.
        
        Args:
            api_key (str, optional): API-ключ (может быть передан напрямую или взят из .env)
        """
        self.logger = AppLogger()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")

        if not self.api_key:
            raise ValueError("API key not provided")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.logger.info("OpenRouterClient initialized successfully")
        self.available_models = self.get_models()      # Загружаем модели сразу при инициализации

    def get_models(self):
        """
        Получение списка доступных моделей через API.
        
        Returns:
            list: Список словарей с id и name моделей
        """
        self.logger.debug("Fetching available models")
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()            # Вызовет исключение при 401/403/5xx
            models_data = response.json()
            self.logger.info(f"Retrieved {len(models_data['data'])} models")
            return [{"id": m["id"], "name": m["name"]} for m in models_data["data"]]
        except Exception as e:
            self.logger.warning(f"Failed to fetch models, using defaults: {e}")
            # Резервный список популярных моделей (на случай отсутствия интернета или ошибки API)
            return [
                {"id": "openchat/openchat-3.5", "name": "OpenChat"},
                {"id": "google/gemma-2-27b-it", "name": "Gemma 2 27B"},
                {"id": "mistralai/mixtral-8x22b-instruct", "name": "Mixtral 8x22B"},
                {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
                {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"}
            ]

    def send_message(self, message: str, model: str):
        """
        Отправка сообщения выбранной модели.
        
        Args:
            message (str): Текст сообщения пользователя
            model (str): ID выбранной модели
        
        Returns:
            dict: Ответ от API в формате OpenAI
        """
        data = {
            "model": model,
            "messages": [{"role": "user", "content": message}]
        }
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"API request failed: {e}", exc_info=True)
            return {"error": str(e)}

    def get_balance(self):
        """
        Получение текущего баланса аккаунта.
        
        Returns:
            str: Остаток средств в формате $X.XX или "н/д"
        """
        try:
            response = requests.get(f"{self.base_url}/credits", headers=self.headers)
            response.raise_for_status()
            data = response.json().get('data', {})
            remaining = data.get('total_credits', 0) - data.get('total_usage', 0)
            return f"${remaining:.2f}"
        except Exception as e:
            self.logger.warning(f"Failed to get balance: {e}")
            return "н/д"