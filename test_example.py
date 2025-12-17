"""
Пример использования API сервиса анализа тональности
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_analyze_sentiment():
    """Тестирует endpoint анализа тональности"""
    url = f"{BASE_URL}/analyze"
    
    # Первый запрос (новый)
    print("=== Первый запрос ===")
    response1 = requests.post(
        url,
        json={"text": "This task is really enjoyable! I love it!"}
    )
    print(f"Status: {response1.status_code}")
    print(f"Response: {json.dumps(response1.json(), indent=2)}")
    print()
    
    # Второй запрос с тем же текстом (из кеша)
    print("=== Второй запрос (тот же текст) ===")
    response2 = requests.post(
        url,
        json={"text": "This task is really enjoyable! I love it!"}
    )
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}")
    print()
    
    # Третий запрос с другим текстом
    print("=== Третий запрос (другой текст) ===")
    response3 = requests.post(
        url,
        json={"text": "This is terrible. I hate it."}
    )
    print(f"Status: {response3.status_code}")
    print(f"Response: {json.dumps(response3.json(), indent=2)}")
    print()

if __name__ == "__main__":
    try:
        test_analyze_sentiment()
    except requests.exceptions.ConnectionError:
        print("Ошибка: Не удалось подключиться к серверу.")
        print("Убедитесь, что сервер запущен: uvicorn main:app --reload")
    except Exception as e:
        print(f"Ошибка: {e}")

