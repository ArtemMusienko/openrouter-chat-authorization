![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)

## What is OpenRouter?

[![ru](https://img.shields.io/badge/README_на_русском-2A2C39?style=for-the-badge&logo=github&logoColor=white)](README.ru.md)  

**OpenRouter.ai** is a single point of access to dozens of the most powerful AI models from various providers:

OpenAI, Anthropic, Google, Mistral, Grok, Gemini, Claude, Llama 3, Mixtral, and many others — all through a **single API key**.

 This is especially useful for:

- Testing and comparing different models;

- Using free tiers (many models have free tiers);

- Switching between models without changing the code.

## How is OpenRouter used in this project?

The application implements:

- Direct connection by your personal OpenRouter API key (sk-or-v1-…);

- Automatic loading of a list of all available models at startup;

- A convenient drop-down list with search by model name and ID;

- Display of the current account balance in real time;

- Fully compatible with OpenAI request format - you can replace OpenRouter with a direct connection to OpenAI/Groq/Anthropic at any time and the code will not break.

 And all this - through one key and without unnecessary registrations.

## Example of code operation

<div  align="center">

| First launch — entering the API key | The PIN code has been created |

|--------------------------------|---------------|

| ![Ввод ключа](https://github.com/user-attachments/assets/d9565c37-81df-4c22-a240-2532f0e1fc3d) | ![PIN-код](https://github.com/user-attachments/assets/c5e7f2ec-c726-4bb8-9ae6-d082bf966a4b) |

| Main Chat | Login by PIN code |

|--------------------|--------------|

| ![Вход по PIN](https://github.com/user-attachments/assets/817f066e-9871-4f3c-b34b-4aa6a0d8bf07) | ![Чат](https://github.com/user-attachments/assets/3dccc192-5cb0-4dd9-915b-2c207aa772d0) |

</div>

> More detailed instructions for using this code are located at
> the path **openrouter-chat-authorization/51-lesson/** in the files **README.md** and **INSTALL.md**.