from abc import ABC, abstractmethod
from typing import List, Dict


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, query: str) -> List[Dict]:
        """Scrape product data based on search query"""
        pass
