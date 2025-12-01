![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)

## Что такое OpenRouter?

**OpenRouter.ai** — это единая точка доступа к десяткам самых мощных ИИ-моделей от разных провайдеров:  
OpenAI, Anthropic, Google, Mistral, Meta, Grok, Gemini, Claude, Llama 3, Mixtral и многим другим — через **один API-ключ**.

Особенно удобно для:
- Тестирования и сравнения разных моделей;
- Использования бесплатных лимитов (многие модели имеют free-tier);
- Переключения между моделями без изменения кода.

## Как OpenRouter используется в этом проекте?

В приложении реализовано:
- Прямое подключение по твоему личному API-ключу OpenRouter (sk-or-v1-…);
- Автоматическая загрузка списка всех доступных моделей при запуске;
- Удобный выпадающий список с поиском по названию и ID модели;
- Отображение текущего баланса аккаунта в реальном времени;
- Полностью совместимый с OpenAI формат запросов — можно в любой момент заменить OpenRouter на прямое подключение к OpenAI/Groq/Anthropic и код не сломается.

И всё это — через один ключ и без лишних регистраций.

## Пример работы кода

<div align="center">

| Первый запуск — ввод API-ключа | PIN-код создан |
|--------------------------------|---------------|
| ![Ввод ключа](https://github.com/user-attachments/assets/d9565c37-81df-4c22-a240-2532f0e1fc3d) | ![PIN-код](https://github.com/user-attachments/assets/c5e7f2ec-c726-4bb8-9ae6-d082bf966a4b) |

| Основной чат | Вход по PIN-коду |
|--------------------|--------------|
| ![Вход по PIN](https://github.com/user-attachments/assets/817f066e-9871-4f3c-b34b-4aa6a0d8bf07) | ![Чат](https://github.com/user-attachments/assets/3dccc192-5cb0-4dd9-915b-2c207aa772d0) |

</div>

> Более подробная инструкция использования этого кода расположена по
> пути **openrouter-chat-authorization/51-lesson/** в файлах
> **README.md** и **INSTALL.md**.
