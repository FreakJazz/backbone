"""Product repository interface - Domain layer"""
from abc import ABC, abstractmethod
from typing import List, Optional
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.domain.specifications import FilterSpecification, SortSpecification
from examples.clean_api_python.domain.entities.product import Product


class ProductRepository(ABC):
    """Product repository interface"""
    
    @abstractmethod
    def create(self, product: Product) -> None:
        """Creates a new product"""
        pass
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[Product]:
        """Finds a product by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Product]:
        """Finds all products"""
        pass
    
    @abstractmethod
    def find_by_criteria(
        self,
        filters: Optional[List[FilterSpecification]] = None,
        sorts: Optional[List[SortSpecification]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Product]:
        """Finds products matching criteria with Specification Pattern"""
        pass
    
    @abstractmethod
    def count(self, filters: Optional[List[FilterSpecification]] = None) -> int:
        """Counts products matching criteria"""
        pass
    
    @abstractmethod
    def update(self, product: Product) -> None:
        """Updates a product"""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> None:
        """Deletes a product by ID"""
        pass
    
    @abstractmethod
    def exists_by_id(self, id: str) -> bool:
        """Checks if a product exists"""
        pass
