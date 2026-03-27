"""
Browser Controller Interface — Абстрактный интерфейс для управления браузером.
Платформо-независимый слой: скрапер вызывает методы, не зная о реализации.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BrowserController(ABC):
    """
    Абстрактный интерфейс управления браузером.
    
    Скрапер использует только два метода:
    - initialize() — подготовка браузера
    - scrape_product(ozon_id) — получение raw_content для товара
    """

    @abstractmethod
    def initialize(self) -> bool:
        """
        Инициализация браузера (запуск, ожидание готовности).
        
        Returns:
            bool: True если браузер готов к работе.
        """
        pass

    @abstractmethod
    def scrape_product(self, ozon_id: str) -> Dict[str, Any]:
        """
        Скрапинг страницы товара.
        
        Args:
            ozon_id: ID товара на Ozon.
            
        Returns:
            Dict с ключом "raw_content" (текст страницы).
        """
        pass

    def cleanup(self) -> None:
        """
        Очистка ресурсов (опционально).
        """
        pass
