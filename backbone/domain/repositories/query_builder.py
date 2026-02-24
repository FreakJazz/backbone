"""
Query Builder - Constructor de queries abstrato
"""
from typing import Dict, Any, List, Optional, Union
from ..specifications.base_specification import Specification
from ..specifications.sort_specification import MultipleSortSpecification


class QueryBuilder:
    """
    Constructor de queries abstracto que puede ser interpretado
    por diferentes adaptadores de persistencia.
    
    Encapsula la lógica de construcción de queries de manera
    independiente del motor de base de datos.
    """
    
    def __init__(self, entity_type: type):
        self.entity_type = entity_type
        self._filters: List[Specification] = []
        self._sorts: Optional[MultipleSortSpecification] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._select_fields: Optional[List[str]] = None
        self._joins: List[Dict[str, Any]] = []
    
    def filter(self, spec: Specification) -> 'QueryBuilder':
        """
        Agrega un filtro (especificación).
        
        Args:
            spec: Especificación a agregar
            
        Returns:
            Self para method chaining
        """
        self._filters.append(spec)
        return self
    
    def sort(self, sort_spec: MultipleSortSpecification) -> 'QueryBuilder':
        """
        Establece el ordenamiento.
        
        Args:
            sort_spec: Especificación de ordenamiento
            
        Returns:
            Self para method chaining
        """
        self._sorts = sort_spec
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """
        Establece el límite de resultados.
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Self para method chaining
        """
        self._limit = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """
        Establece el offset de resultados.
        
        Args:
            offset: Número de resultados a saltar
            
        Returns:
            Self para method chaining
        """
        self._offset = offset
        return self
    
    def select(self, fields: List[str]) -> 'QueryBuilder':
        """
        Especifica campos a seleccionar.
        
        Args:
            fields: Lista de nombres de campos
            
        Returns:
            Self para method chaining
        """
        self._select_fields = fields
        return self
    
    def join(
        self, 
        entity_type: type, 
        condition: str,
        join_type: str = "inner"
    ) -> 'QueryBuilder':
        """
        Agrega un JOIN.
        
        Args:
            entity_type: Tipo de entidad a joinear
            condition: Condición del join
            join_type: Tipo de join (inner, left, right, outer)
            
        Returns:
            Self para method chaining
        """
        self._joins.append({
            "entity_type": entity_type,
            "condition": condition,
            "join_type": join_type
        })
        return self
    
    def paginate(self, page: int, page_size: int) -> 'QueryBuilder':
        """
        Configura paginación.
        
        Args:
            page: Página actual (0-indexed)
            page_size: Elementos por página
            
        Returns:
            Self para method chaining
        """
        self._offset = page * page_size
        self._limit = page_size
        return self
    
    def to_query_definition(self) -> Dict[str, Any]:
        """
        Convierte el builder a definición de query genérica.
        
        Los adaptadores específicos interpretarán esta definición
        para generar queries específicas (SQL, MongoDB, etc.).
        
        Returns:
            Dict con la definición de la query
        """
        return {
            "entity_type": self.entity_type,
            "filters": [f.to_expression() for f in self._filters],
            "sorts": self._sorts.to_expression() if self._sorts else None,
            "limit": self._limit,
            "offset": self._offset,
            "select_fields": self._select_fields,
            "joins": self._joins
        }
    
    def clear(self) -> 'QueryBuilder':
        """
        Limpia todos los filtros y configuraciones.
        
        Returns:
            Self para method chaining
        """
        self._filters.clear()
        self._sorts = None
        self._limit = None
        self._offset = None
        self._select_fields = None
        self._joins.clear()
        return self
    
    def clone(self) -> 'QueryBuilder':
        """
        Crea una copia del QueryBuilder.
        
        Returns:
            Nueva instancia del QueryBuilder con la misma configuración
        """
        new_builder = QueryBuilder(self.entity_type)
        new_builder._filters = self._filters.copy()
        new_builder._sorts = self._sorts
        new_builder._limit = self._limit
        new_builder._offset = self._offset
        new_builder._select_fields = self._select_fields.copy() if self._select_fields else None
        new_builder._joins = self._joins.copy()
        return new_builder
    
    @property
    def has_filters(self) -> bool:
        """Verifica si tiene filtros configurados."""
        return len(self._filters) > 0
    
    @property
    def has_sorting(self) -> bool:
        """Verifica si tiene ordenamiento configurado."""
        return self._sorts is not None and not self._sorts.is_empty()
    
    @property
    def has_pagination(self) -> bool:
        """Verifica si tiene paginación configurada."""
        return self._limit is not None or self._offset is not None
    
    @property
    def has_field_selection(self) -> bool:
        """Verifica si tiene selección específica de campos."""
        return self._select_fields is not None and len(self._select_fields) > 0
    
    @property 
    def has_joins(self) -> bool:
        """Verifica si tiene joins configurados."""
        return len(self._joins) > 0