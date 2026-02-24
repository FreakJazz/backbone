"""
Base Specification - Patrón Specification para filtros dinámicos
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Union

T = TypeVar('T')  # Tipo de entidad


class Specification(ABC, Generic[T]):
    """
    Specification abstracto para implementar el patrón Specification.
    
    Permite crear filtros complejos y reutilizables que se pueden
    combinar usando operadores lógicos (AND, OR, NOT).
    
    Cada especificación sabe cómo validar una entidad y también
    cómo convertirse a query de base de datos.
    """
    
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Verifica si la entidad satisface la especificación.
        
        Args:
            candidate: Entidad a evaluar
            
        Returns:
            True si satisface la especificación
        """
        pass
    
    @abstractmethod
    def to_expression(self) -> Any:
        """
        Convierte la especificación a expresión de query.
        
        La implementación específica dependerá del adaptador:
        - SQLAlchemy: retorna clausula WHERE
        - MongoDB: retorna dict con filtro
        - ElasticSearch: retorna query DSL
        
        Returns:
            Expresión de query específica del adaptador
        """
        pass
    
    def and_spec(self, other: 'Specification[T]') -> 'CompositeSpecification[T]':
        """Combina con otra especificación usando AND."""
        return AndSpecification(self, other)
    
    def and_(self, other: 'Specification[T]') -> 'CompositeSpecification[T]':
        """Alias for and_spec - combines with another specification using AND."""
        return self.and_spec(other)
    
    def or_spec(self, other: 'Specification[T]') -> 'CompositeSpecification[T]':
        """Combina con otra especificación usando OR."""
        return OrSpecification(self, other)
    
    def or_(self, other: 'Specification[T]') -> 'CompositeSpecification[T]':
        """Alias for or_spec - combines with another specification using OR."""
        return self.or_spec(other)
    
    def not_spec(self) -> 'CompositeSpecification[T]':
        """Negación de la especificación."""
        return NotSpecification(self)
    
    # Operadores sobrecargados para syntax sugar
    def __and__(self, other: 'Specification[T]') -> 'CompositeSpecification[T]':
        return self.and_spec(other)
    
    def __or__(self, other: 'Specification[T]') -> 'CompositeSpecification[T]':
        return self.or_spec(other)
    
    def __invert__(self) -> 'CompositeSpecification[T]':
        return self.not_spec()


class CompositeSpecification(Specification[T]):
    """
    Especificación compuesta que combina múltiples especificaciones.
    """
    
    def __init__(self, left: Specification[T], right: Specification[T] = None):
        self.left = left
        self.right = right


class AndSpecification(CompositeSpecification[T]):
    """Especificación AND - ambas deben ser verdaderas."""
    
    def is_satisfied_by(self, candidate: T) -> bool:
        return (self.left.is_satisfied_by(candidate) and 
                self.right.is_satisfied_by(candidate))
    
    def to_expression(self) -> Any:
        # La implementación específica será en los adaptadores
        return {
            "operator": "AND",
            "left": self.left.to_expression(),
            "right": self.right.to_expression()
        }


class OrSpecification(CompositeSpecification[T]):
    """Especificación OR - al menos una debe ser verdadera."""
    
    def is_satisfied_by(self, candidate: T) -> bool:
        return (self.left.is_satisfied_by(candidate) or 
                self.right.is_satisfied_by(candidate))
    
    def to_expression(self) -> Any:
        return {
            "operator": "OR",
            "left": self.left.to_expression(),
            "right": self.right.to_expression()
        }


class NotSpecification(CompositeSpecification[T]):
    """Especificación NOT - negación de la especificación."""
    
    def __init__(self, spec: Specification[T]):
        super().__init__(spec)
        self.spec = spec
    
    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.spec.is_satisfied_by(candidate)
    
    def to_expression(self) -> Any:
        return {
            "operator": "NOT",
            "spec": self.spec.to_expression()
        }