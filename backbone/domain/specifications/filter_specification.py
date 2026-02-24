"""
Filter Specifications - Especificaciones concretas para filtros
"""
from typing import Any, List, Union
from .base_specification import Specification, T


class FilterSpecification(Specification[T]):
    """
    Especificación base para filtros de campos.
    
    Encapsula el field, operator y value de un filtro.
    """
    
    def __init__(self, field: str, operator: str, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Evalúa si la entidad satisface el filtro.
        
        Usa getattr para acceder al campo de la entidad.
        """
        try:
            field_value = getattr(candidate, self.field)
            return self._compare_values(field_value, self.value)
        except AttributeError:
            return False
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        """Override en especificaciones concretas."""
        return field_value == filter_value
    
    def to_expression(self) -> dict:
        """
        Convierte a formato genérico que los adaptadores pueden interpretar.
        """
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }


class EqualSpecification(FilterSpecification):
    """Especificación de igualdad: field = value"""
    
    def __init__(self, field: str, value: Any):
        super().__init__(field, "eq", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        return field_value == filter_value


class NotEqualSpecification(FilterSpecification):
    """Especificación de desigualdad: field != value"""
    
    def __init__(self, field: str, value: Any):
        super().__init__(field, "ne", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        return field_value != filter_value


class LessThanSpecification(FilterSpecification):
    """Especificación menor que: field < value"""
    
    def __init__(self, field: str, value: Union[int, float, str]):
        super().__init__(field, "lt", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        try:
            return field_value < filter_value
        except TypeError:
            return False


class LessThanOrEqualSpecification(FilterSpecification):
    """Especificación menor o igual que: field <= value"""
    
    def __init__(self, field: str, value: Union[int, float, str]):
        super().__init__(field, "lte", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        try:
            return field_value <= filter_value
        except TypeError:
            return False


class GreaterThanSpecification(FilterSpecification):
    """Especificación mayor que: field > value"""
    
    def __init__(self, field: str, value: Union[int, float, str]):
        super().__init__(field, "gt", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        try:
            return field_value > filter_value
        except TypeError:
            return False


class GreaterThanOrEqualSpecification(FilterSpecification):
    """Especificación mayor o igual que: field >= value"""
    
    def __init__(self, field: str, value: Union[int, float, str]):
        super().__init__(field, "gte", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        try:
            return field_value >= filter_value
        except TypeError:
            return False


class LikeSpecification(FilterSpecification):
    """Especificación LIKE: field LIKE '%value%'"""
    
    def __init__(self, field: str, value: str):
        super().__init__(field, "like", value)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        if field_value is None:
            return False
        return str(filter_value).lower() in str(field_value).lower()


class InSpecification(FilterSpecification):
    """Especificación IN: field IN (value1, value2, ...)"""
    
    def __init__(self, field: str, values: List[Any]):
        super().__init__(field, "in", values)
    
    def _compare_values(self, field_value: Any, filter_values: List[Any]) -> bool:
        return field_value in filter_values


class BetweenSpecification(FilterSpecification):
    """Especificación BETWEEN: field BETWEEN min_value AND max_value"""
    
    def __init__(self, field: str, min_value: Any, max_value: Any):
        super().__init__(field, "between", [min_value, max_value])
        self.min_value = min_value
        self.max_value = max_value
    
    def _compare_values(self, field_value: Any, filter_value: List[Any]) -> bool:
        try:
            return self.min_value <= field_value <= self.max_value
        except TypeError:
            return False


class IsNullSpecification(FilterSpecification):
    """Especificación IS NULL: field IS NULL"""
    
    def __init__(self, field: str):
        super().__init__(field, "is_null", None)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        return field_value is None


class IsNotNullSpecification(FilterSpecification):
    """Especificación IS NOT NULL: field IS NOT NULL"""
    
    def __init__(self, field: str):
        super().__init__(field, "is_not_null", None)
    
    def _compare_values(self, field_value: Any, filter_value: Any) -> bool:
        return field_value is not None


# Factory para crear especificaciones
class SpecificationFactory:
    """
    Factory para crear especificaciones basado en operadores string.
    """
    
    _operators = {
        "eq": EqualSpecification,
        "ne": NotEqualSpecification,
        "lt": LessThanSpecification,
        "lte": LessThanOrEqualSpecification,
        "gt": GreaterThanSpecification,
        "gte": GreaterThanOrEqualSpecification,
        "like": LikeSpecification,
        "in": InSpecification,
        "between": BetweenSpecification,
        "is_null": IsNullSpecification,
        "is_not_null": IsNotNullSpecification,
    }
    
    @classmethod
    def create(cls, field: str, operator: str, value: Any) -> FilterSpecification:
        """
        Crea una especificación basada en field, operator, value.
        
        Args:
            field: Nombre del campo
            operator: Operador (eq, ne, lt, gte, like, in, between, etc.)
            value: Valor para la comparación
            
        Returns:
            Especificación concreta
            
        Raises:
            ValueError: Si el operador no es soportado
        """
        if operator not in cls._operators:
            raise ValueError(f"Unsupported operator: {operator}. Supported: {list(cls._operators.keys())}")
        
        spec_class = cls._operators[operator]
        
        # Casos especiales
        if operator == "between":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("BETWEEN operator requires list/tuple with 2 values")
            return spec_class(field, value[0], value[1])
        elif operator in ("is_null", "is_not_null"):
            return spec_class(field)
        else:
            return spec_class(field, value)
    
    @classmethod
    def supported_operators(cls) -> List[str]:
        """Retorna lista de operadores soportados."""
        return list(cls._operators.keys())