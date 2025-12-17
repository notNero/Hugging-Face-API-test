# Text Sentiment Analysis Service

Сервис для анализа тональности текста на основе FastAPI и Hugging Face API.

## Установка и подготовка к работе в случае запуска локально

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

Или создайте файл `.env` вручную с содержимым из `env.example`.

### Как получить API ключ

1. Зарегистрируйте аккаунт или войдите в профиль на Hugging Face

2. Перейдите в раздел Settings → Access Tokens.

3. Создайте новый токен, указав нужные права доступа (в этом случае достаточно read).

4. Укажите токен Hugging Face API в `.env`:

```bash
HUGGINGFACE_API_TOKEN=your_api_token
```

### Запуск

Запустите сервер:

```bash
uvicorn main:app --reload
```

Сервер будет доступен по адресу: http://localhost:8000

### Пример работы решения

Пример работы решения можно получить, введя в отдельный от сервера терминал команду

```bash
python .\test_example.py     
```

### Тесты

Тесты можно запустить введя в корневой директории команду

```bash
pytest test_main.py -v
```
## В случае запуска через Docker

1. Ввести команды
```bash
docker build -t hugging_face_api_test .
```
```bash
docker run -d \
  --name hugging_face_api_test \
  --env-file .env.example \
  -p 8000:8000 \
  hugging_face_api_test
```
2. Теперь тесты сервиса в Swagger доступны по ссылке:
http://localhost:8000/docs

## API Endpoints

### POST /analyze

Анализирует тональность текста.

**Пример Запроса:**
```json
{
  "text": "I love this product!"
}
```

**Ответ:**
```json
{
  "text": "I love this product!",
  "labels": [
    {
      "label": "positive",
      "score": 0.9876
    },
    {
      "label": "neutral",
      "score": 0.0102
    },
    {
      "label": "negative",
      "score": 0.0022
    }
  ],
  "from_cache": false,
  "top_label": "positive",
  "top_score": 0.9876
}
```

### GET /

Корневой endpoint с информацией о сервисе.

## Использование

### Пример с curl:

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a great day!"}'
```

### Пример с Python:

```bash
import requests
import json

BASE_URL = "http://localhost:8000"
url = f"{BASE_URL}/analyze"

response = requests.post(
    url,
    json={"text": "This is a great day!"}
)
print(response.json())
```

## Кеширование

Сервис использует `functools.lru_cache` для кеширования результатов. 

- Максимальный размер кеша: 128 записей
- При повторном запросе с тем же текстом результат возвращается из кеша
- В поле `from_cache` ответа указывается, был ли использован кеш

## Логирование

Все запросы и ошибки логируются в консоль с уровнем INFO и выше. Формат логов:

```bash
2025-12-16 21:30:32 - __main__ - INFO - Получен запрос на анализ тональности для текста: This is a great day!...
2025-12-16 21:30:33 - __main__ - INFO - Успешный ответ от Hugging Face API: [...]
```

## Обработка ошибок

Сервис обрабатывает следующие типы ошибок:

- **Таймауты** (504): Превышено время ожидания ответа от API
- **HTTP ошибки** (502): Ошибки от Hugging Face API
- **Ошибки соединения** (503): Проблемы с подключением к интернету
- **Внутренние ошибки** (500): Неожиданные ошибки сервера

## Конфигурация

Настройки можно изменить через переменные окружения в файле `.env`:

- `HUGGINGFACE_API_URL` - URL модели Hugging Face (В этом случае модель анализа тональности)
- `HUGGINGFACE_API_TOKEN` - Токен для доступа к API
- `REQUEST_TIMEOUT` - Таймаут запроса в секундах (30.0 секунд)

## Документация API

Интерактивная документация с возможностью тестов доступна, после запуска сервера, по адресам:

- Swagger UI: http://localhost:8000/docs

