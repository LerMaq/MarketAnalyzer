from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BrowserController(ABC):
    @abstractmethod
    def initialize(self) -> bool:
        """Подготовить браузер к работе."""
        raise NotImplementedError

    @abstractmethod
    def scrape_product(self, ozon_id: int | str, review_count: int) -> dict[str, Any]:
        """Собрать данные со страницы товара."""
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        """Очистить ресурсы при завершении."""
        raise NotImplementedError