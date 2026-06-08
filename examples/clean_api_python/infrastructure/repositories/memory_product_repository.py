"""Memory product repository - Infrastructure layer"""
from typing import List, Optional
import sys
import os
from datetime import datetime
import time

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.domain.specifications import FilterSpecification, SortSpecification
from backbone.infrastructure.logging import LoggerFactory, LogLevel
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.domain.repositories.product_repository import ProductRepository


class MemoryProductRepository(ProductRepository):
    """In-memory product repository implementation"""
    
    def __init__(self):
        self.products = {}
        self.logger = LoggerFactory.create_layer_logger(
            "product-api",
            "infrastructure",
            "MemoryProductRepository"
        )
    
    def create(self, product: Product) -> None:
        """Creates a new product"""
        start = time.time()
        
        if product.id in self.products:
            duration_ms = int((time.time() - start) * 1000)
            self.logger.error(
                "Product already exists",
                extra_data={
                    "product_id": product.id,
                    "duration_ms": duration_ms,
                    "error_code": 12001001
                }
            )
            raise ValueError(f"Product with ID {product.id} already exists")
        
        self.products[product.id] = product
        
        duration_ms = int((time.time() - start) * 1000)
        self.logger.info(
            "Product created",
            extra_data={
                "product_id": product.id,
                "duration_ms": duration_ms
            }
        )
    
    def find_by_id(self, id: str) -> Optional[Product]:
        """Finds a product by ID"""
        start = time.time()
        
        product = self.products.get(id)
        duration_ms = int((time.time() - start) * 1000)
        
        if not product:
            self.logger.warning(
                "Product not found",
                extra_data={
                    "product_id": id,
                    "duration_ms": duration_ms
                }
            )
            return None
        
        self.logger.debug(
            "Product found",
            extra_data={
                "product_id": id,
                "duration_ms": duration_ms
            }
        )
        
        return product
    
    def find_all(self) -> List[Product]:
        """Finds all products"""
        start = time.time()
        
        products = list(self.products.values())
        
        duration_ms = int((time.time() - start) * 1000)
        self.logger.info(
            "All products retrieved",
            extra_data={
                "count": len(products),
                "duration_ms": duration_ms
            }
        )
        
        return products
    
    def find_by_criteria(
        self,
        filters: Optional[List[FilterSpecification]] = None,
        sorts: Optional[List[SortSpecification]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Product]:
        """Finds products matching criteria with Specification Pattern"""
        start = time.time()
        
        # Log simulated SQL query
        sql_parts = ["SELECT * FROM products"]
        args = []
        
        if filters:
            where_clauses = []
            for f in filters:
                where_clauses.append(f"{f.field} {f.operator} ?")
                args.append(f.value)
            sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        if sorts:
            order_by = ", ".join([f"{s.field} {s.direction}" for s in sorts])
            sql_parts.append(f"ORDER BY {order_by}")
        
        offset = (page - 1) * page_size
        sql_parts.append(f"LIMIT {page_size} OFFSET {offset}")
        
        sql = " ".join(sql_parts)
        
        self.logger.debug(
            "Executing query with criteria",
            extra_data={
                "sql": sql,
                "args": args
            }
        )
        
        # En memoria: aplicar filtros manualmente
        results = list(self.products.values())
        
        # Aplicar filtros
        if filters:
            for filter_spec in filters:
                results = self._apply_filter(results, filter_spec)
        
        # Aplicar ordenamiento
        if sorts:
            for sort_spec in sorts:
                results = self._apply_sort(results, sort_spec)
        
        # Aplicar paginación
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        results = results[start_idx:end_idx]
        
        duration_ms = int((time.time() - start) * 1000)
        
        # Log de query completo
        self.logger.debug(
            "Query executed",
            extra_data={
                "sql": sql,
                "args": args,
                "duration_ms": duration_ms,
                "rows_returned": len(results)
            }
        )
        
        self.logger.info(
            "Products found by criteria",
            extra_data={
                "count": len(results),
                "duration_ms": duration_ms
            }
        )
        
        return results
    
    def count(self, filters: Optional[List[FilterSpecification]] = None) -> int:
        """Counts products matching criteria"""
        start = time.time()
        
        results = list(self.products.values())
        
        if filters:
            for filter_spec in filters:
                results = self._apply_filter(results, filter_spec)
        
        count = len(results)
        
        duration_ms = int((time.time() - start) * 1000)
        self.logger.debug(
            "Count query executed",
            extra_data={
                "count": count,
                "duration_ms": duration_ms
            }
        )
        
        return count
    
    def update(self, product: Product) -> None:
        """Updates a product"""
        start = time.time()
        
        if product.id not in self.products:
            duration_ms = int((time.time() - start) * 1000)
            self.logger.error(
                "Product not found for update",
                extra_data={
                    "product_id": product.id,
                    "duration_ms": duration_ms,
                    "error_code": 12001002
                }
            )
            raise ValueError("Product not found")
        
        product.updated_at = datetime.now()
        self.products[product.id] = product
        
        duration_ms = int((time.time() - start) * 1000)
        self.logger.info(
            "Product updated",
            extra_data={
                "product_id": product.id,
                "duration_ms": duration_ms
            }
        )
    
    def delete(self, id: str) -> None:
        """Deletes a product by ID"""
        start = time.time()
        
        if id not in self.products:
            duration_ms = int((time.time() - start) * 1000)
            self.logger.error(
                "Product not found for deletion",
                extra_data={
                    "product_id": id,
                    "duration_ms": duration_ms,
                    "error_code": 12001003
                }
            )
            raise ValueError("Product not found")
        
        del self.products[id]
        
        duration_ms = int((time.time() - start) * 1000)
        self.logger.info(
            "Product deleted",
            extra_data={
                "product_id": id,
                "duration_ms": duration_ms
            }
        )
    
    def exists_by_id(self, id: str) -> bool:
        """Checks if a product exists"""
        return id in self.products
    
    def _apply_filter(self, products: List[Product], filter_spec: FilterSpecification) -> List[Product]:
        """Applies a filter to products"""
        result = []
        for product in products:
            value = getattr(product, filter_spec.field)
            
            if filter_spec.operator == "=":
                if value == filter_spec.value:
                    result.append(product)
            elif filter_spec.operator == ">":
                if value > filter_spec.value:
                    result.append(product)
            elif filter_spec.operator == ">=":
                if value >= filter_spec.value:
                    result.append(product)
            elif filter_spec.operator == "<":
                if value < filter_spec.value:
                    result.append(product)
            elif filter_spec.operator == "<=":
                if value <= filter_spec.value:
                    result.append(product)
            elif filter_spec.operator == "LIKE":
                pattern = filter_spec.value.replace("%", "")
                if pattern.lower() in str(value).lower():
                    result.append(product)
        
        return result
    
    def _apply_sort(self, products: List[Product], sort_spec: SortSpecification) -> List[Product]:
        """Applies sorting to products"""
        reverse = sort_spec.direction.lower() == "desc"
        return sorted(products, key=lambda p: getattr(p, sort_spec.field), reverse=reverse)
