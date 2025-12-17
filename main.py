import logging
import os
from functools import lru_cache
from typing import Dict, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Text Sentiment Analysis Service",
    description="Сервис для анализа тональности текста через Hugging Face API",
    version="1.0.0"
)

HUGGINGFACE_API_URL = os.getenv(
    "HUGGINGFACE_API_URL",
    "https://router.huggingface.co/hf-inference/models/cardiffnlp/twitter-roberta-base-sentiment-latest"
)
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30.0"))


class TextRequest(BaseModel):
    """Модель запроса"""
    text: str = Field(..., min_length=1, description="Текст для анализа тональности")


class SentimentLabel(BaseModel):
    """Модель метки тональности"""
    label: str = Field(..., description="Метка тональности")
    score: float = Field(..., ge=0.0, le=1.0, description="Вероятность метки")


class SentimentResponse(BaseModel):
    """Модель ответа"""
    text: str = Field(..., description="Исходный текст")
    labels: List[SentimentLabel] = Field(..., description="Список меток с вероятностями")
    from_cache: bool = Field(..., description="Флаг использования кеша")
    top_label: str = Field(..., description="Метка с наибольшей вероятностью")
    top_score: float = Field(..., description="Вероятность топ-метки")


def normalize_huggingface_response(api_response: List[Dict]) -> List[SentimentLabel]:
    """
    Нормализует ответ Hugging Face API к единому формату
    """
    if not api_response:
        return []

    first_item = api_response[0]
    items = api_response if not isinstance(first_item, list) else first_item

    labels: List[SentimentLabel] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = item.get("label", "")
        score = float(item.get("score", 0.0))
        labels.append(SentimentLabel(label=label, score=score))
    
    labels.sort(key=lambda x: x.score, reverse=True)
    return labels


def _call_huggingface_api(text: str) -> tuple:
    logger.info(f"Выполняется запрос к Hugging Face API для текста: {text[:50]}...")
    
    headers = {}
    if HUGGINGFACE_API_TOKEN:
        headers["Authorization"] = f"Bearer {HUGGINGFACE_API_TOKEN}"
    
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json={"inputs": text}
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Успешный ответ от Hugging Face API: {result}")
        
        if isinstance(result, list):
            return tuple(normalize_huggingface_response(result))
        elif isinstance(result, dict) and "error" in result:
            raise ValueError(f"Hugging Face API error: {result['error']}")
        else:
            return tuple(normalize_huggingface_response([result]))


@lru_cache(maxsize=128)
def _cached_sentiment_analysis(text: str) -> tuple:
    try:
        return _call_huggingface_api(text)
    except httpx.TimeoutException:
        logger.error(f"Таймаут при запросе к Hugging Face API для текста: {text[:50]}...")
        raise HTTPException(
            status_code=504,
            detail="Таймаут при обращении к Hugging Face API. Попробуйте позже."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP ошибка при запросе к Hugging Face API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка Hugging Face API: {e.response.status_code}. {e.response.text[:200]}"
        )
    except httpx.RequestError as e:
        logger.error(f"Ошибка соединения с Hugging Face API: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Не удалось подключиться к Hugging Face API. Проверьте подключение к интернету."
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к Hugging Face API: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


def get_sentiment_analysis(text: str) -> tuple[tuple, bool]:
    # Получаем статистику кеша до вызова
    cache_info_before = _cached_sentiment_analysis.cache_info()
    hits_before = cache_info_before.hits
    
    # Вызываем функцию (может вернуть из кеша или выполнить запрос)
    result = _cached_sentiment_analysis(text)
    
    # Получаем статистику кеша после вызова
    cache_info_after = _cached_sentiment_analysis.cache_info()
    hits_after = cache_info_after.hits
    
    # Если количество попаданий увеличилось, значит использовался кеш
    from_cache = hits_after > hits_before
    
    return result, from_cache


@app.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: TextRequest) -> SentimentResponse:
    logger.info(f"Получен запрос на анализ тональности для текста: {request.text[:50]}...")
    
    try:
        labels_tuple, from_cache = get_sentiment_analysis(request.text)
        labels = list(labels_tuple)
        
        if not labels:
            raise HTTPException(
                status_code=502,
                detail="Пустой ответ от Hugging Face API"
            )
        
        top_label = labels[0]
        
        response = SentimentResponse(
            text=request.text,
            labels=labels,
            from_cache=from_cache,
            top_label=top_label.label,
            top_score=top_label.score
        )
        
        cache_status = "из кеша" if from_cache else "новый запрос"
        logger.info(f"Результат анализа получен ({cache_status}): топ-метка = {top_label.label}, score = {top_label.score:.4f}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Text Sentiment Analysis Service",
        "docs": "/docs"
    }

