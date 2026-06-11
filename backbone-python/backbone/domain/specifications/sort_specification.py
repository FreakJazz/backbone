"""
Sort Specification - Especificación para ordenamiento
"""
from typing import List, Optional, Tuple
from enum import Enum
from ..exceptions.domain_exceptions import InvalidValueObjectException


class SortDirection(str, Enum):
    """Direcciones de ordenamiento."""
    ASC = "asc"
    DESC = "desc"


class SortSpecification:
    """
    Especificación para ordenamiento de resultados.
    
    Permite especificar múltiples campos con diferentes direcciones.
    """
    
    def __init__(self, field: str, direction: SortDirection = SortDirection.ASC):
        """
        Inicializa especificación de ordenamiento.
        
        Args:
            field: Campo por el cual ordenar
            direction: Dirección del ordenamiento (asc/desc)
        """
        self.field = field
        self.direction = direction
    
    def to_expression(self) -> dict:
        """
        Convierte a formato genérico para adaptadores.
        
        Returns:
            Dict con información de ordenamiento
        """
        return {
            "field": self.field,
            "direction": self.direction.value
        }
    
    def to_sort_criteria(self) -> List[Tuple[str, str]]:
        """
        Converts to sort criteria format expected by repositories.
        
        Returns:
            List of (field, direction) tuples
        """
        return [(self.field, self.direction.value)]
    
    def __str__(self) -> str:
        return f"{self.field} {self.direction.value.upper()}"
    
    def __repr__(self) -> str:
        return f"SortSpecification(field='{self.field}', direction='{self.direction.value}')"


class MultipleSortSpecification:
    """
    Especificación para ordenamiento múltiple.
    
    Permite ordenar por múltiples campos con diferentes direcciones.
    """
    
    def __init__(self, sorts: Optional[List[SortSpecification]] = None):
        """
        Inicializa especificación de ordenamiento múltiple.
        
        Args:
            sorts: Lista de especificaciones de ordenamiento
        """
        self.sorts = sorts or []
    
    def add_sort(self, field: str, direction: SortDirection = SortDirection.ASC) -> 'MultipleSortSpecification':
        """
        Agrega un campo de ordenamiento.
        
        Args:
            field: Campo a agregar
            direction: Dirección del ordenamiento
            
        Returns:
            Self para method chaining
        """
        self.sorts.append(SortSpecification(field, direction))
        return self
    
    def to_expression(self) -> List[dict]:
        """
        Convierte a lista de expresiones de ordenamiento.
        
        Returns:
            Lista de dicts con información de ordenamiento
        """
        return [sort.to_expression() for sort in self.sorts]
    
    def to_sort_criteria(self) -> List[Tuple[str, str]]:
        """
        Converts to sort criteria format expected by repositories.
        
        Returns:
            List of (field, direction) tuples
        """
        return [(sort.field, sort.direction.value) for sort in self.sorts]
    
    def is_empty(self) -> bool:
        """Verifica si no hay ordenamientos definidos."""
        return len(self.sorts) == 0
    
    def __len__(self) -> int:
        return len(self.sorts)
    
    def __iter__(self):
        return iter(self.sorts)
    
    def __str__(self) -> str:
        return ", ".join(str(sort) for sort in self.sorts)


class SortParser:
    """
    Parser para convertir parámetros de ordenamiento a especificaciones.
    
    Formatos soportados:
    - "field" -> field ASC
    - "field,desc" -> field DESC  
    - "field,asc" -> field ASC
    """
    
    def parse_sort(self, sort_str: Optional[str]) -> Optional[MultipleSortSpecification]:
        """
        Convierte string de ordenamiento a especificación.
        
        Args:
            sort_str: String con formato "field[,direction]"
            
        Returns:
            Especificación de ordenamiento o None
            
        Examples:
            - "created_at" -> created_at ASC
            - "created_at,desc" -> created_at DESC
            - "name,asc" -> name ASC
        """
        if not sort_str or not sort_str.strip():
            return None
        
        parts = sort_str.strip().split(",")
        field = parts[0].strip()
        
        if not field:
            return None
        
        # Determinar dirección
        if len(parts) > 1:
            direction_str = parts[1].strip().lower()
            if direction_str not in ("asc", "desc"):
                raise InvalidValueObjectException(
                    message=f"Dirección de ordenamiento inválida: '{direction_str}'. Usar 'asc' o 'desc'",
                    value_object_type="SortDirection",
                    invalid_value=direction_str,
                    code=11003012
                )
            direction = SortDirection(direction_str)
        else:
            direction = SortDirection.ASC
        
        # Crear especificación
        spec = MultipleSortSpecification()
        spec.add_sort(field, direction)
        return spec
    
    def parse_multiple_sorts(self, sorts: List[str]) -> Optional[MultipleSortSpecification]:
        """
        Convierte lista de strings de ordenamiento a especificación múltiple.
        
        Args:
            sorts: Lista de strings con formato "field[,direction]"
            
        Returns:
            Especificación de ordenamiento múltiple o None
            
        Examples:
            ["created_at,desc", "name,asc"] -> ORDER BY created_at DESC, name ASC
        """
        if not sorts:
            return None
        
        spec = MultipleSortSpecification()
        
        for sort_str in sorts:
            single_spec = self.parse_sort(sort_str)
            if single_spec and not single_spec.is_empty():
                # Agregar el primer sort de la especificación single
                sort_item = single_spec.sorts[0]
                spec.add_sort(sort_item.field, sort_item.direction)
        
        return spec if not spec.is_empty() else None
    
    def validate_sort_field(self, field: str, allowed_fields: List[str]) -> bool:
        """
        Valida que el campo de ordenamiento esté permitido.
        
        Args:
            field: Campo a validar
            allowed_fields: Lista de campos permitidos
            
        Returns:
            True si el campo es válido
            
        Raises:
            InvalidValueObjectException: Si el campo no está permitido
        """
        if field not in allowed_fields:
            raise InvalidValueObjectException(
                message=f"Campo de ordenamiento no permitido: '{field}'. Campos permitidos: {allowed_fields}",
                value_object_type="SortField",
                invalid_value=field,
                code=11003013
            )
        
        return True