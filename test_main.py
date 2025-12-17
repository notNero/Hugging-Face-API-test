import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_analyze_sentiment_success():
    """Smoke-тест: успешный запрос к /analyze"""
    response = client.post("/analyze", json={"text": "I love this!"})
    
    # Проверяем, что сервер ответил 200
    assert response.status_code == 200
    
    data = response.json()
    
    # Проверяем структуру ответа
    assert "text" in data
    assert "labels" in data
    assert "from_cache" in data
    assert "top_label" in data
    assert "top_score" in data
    
    # Проверяем, что labels — непустой список
    assert isinstance(data["labels"], list)
    assert len(data["labels"]) > 0
    
    # Проверяем формат первой метки
    first_label = data["labels"][0]
    assert "label" in first_label
    assert "score" in first_label
    assert isinstance(first_label["score"], float)
    assert 0.0 <= first_label["score"] <= 1.0
    
    # top_label должен совпадать с label первой (наиболее вероятной) метки
    assert data["top_label"] == first_label["label"]
    assert data["top_score"] == first_label["score"]


def test_analyze_sentiment_empty_text():
    """Smoke-тест: ошибка при пустом тексте (валидация Pydantic)"""
    response = client.post("/analyze", json={"text": ""})
    
    # Pydantic должен вернуть 422 при нарушении min_length=1
    assert response.status_code == 422
    
    error_detail = response.json()
    assert "detail" in error_detail