"""
Base Repository - Contratos de repositorio (domain layer)
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Any, Dict
from ..specifications.base_specification import Specification
from ..specifications.sort_specification import MultipleSortSpecification


T = TypeVar('T')  # Tipo de entidad
ID = TypeVar('ID')  # Tipo de ID


class IReadOnlyRepository(ABC, Generic[T, ID]):
    """
    Contrato para repositorio de solo lectura.
    
    Define operaciones de consulta sin mutación de datos.
    Útil para queries, reportes y casos de uso de solo consulta.
    """
    
    @abstractmethod
    async def find_by_id(self, entity_id: ID) -> Optional[T]:
        """
        Busca entidad por ID.
        
        Args:
            entity_id: ID de la entidad
            
        Returns:
            Entidad encontrada o None
        """
        pass
    
    @abstractmethod
    async def find_by_specification(
        self,
        spec: Specification[T],
        sort: Optional[MultipleSortSpecification] = None
    ) -> List[T]:
        """
        Busca entidades que cumplan la especificación.
        
        Args:
            spec: Especificación a evaluar
            sort: Ordenamiento opcional
            
        Returns:
            Lista de entidades que cumplen la especificación
        """
        pass
    
    @abstractmethod
    async def find_paginated_by_specification(
        self,
        spec: Optional[Specification[T]],
        page: int,
        page_size: int,
        sort: Optional[MultipleSortSpecification] = None
    ) -> tuple[List[T], int]:
        """
        Busca entidades paginadas que cumplan la especificación.
        
        Args:
            spec: Especificación a evaluar (None = todas)
            page: Página actual (0-indexed)
            page_size: Elementos por página
            sort: Ordenamiento opcional
            
        Returns:
            Tuple con (entidades, total_count)
        """
        pass
    
    @abstractmethod
    async def count_by_specification(
        self,
        spec: Optional[Specification[T]] = None
    ) -> int:
        """
        Cuenta entidades que cumplan la especificación.
        
        Args:
            spec: Especificación a evaluar (None = todas)
            
        Returns:
            Número de entidades
        """
        pass
    
    @abstractmethod
    async def exists_by_specification(
        self,
        spec: Specification[T]
    ) -> bool:
        """
        Verifica si existe al menos una entidad que cumpla la especificación.
        
        Args:
            spec: Especificación a evaluar
            
        Returns:
            True si existe al menos una entidad
        """
        pass


class IRepository(IReadOnlyRepository[T, ID]):
    """
    Contrato para repositorio completo (lectura y escritura).
    
    Extiende IReadOnlyRepository con operaciones de mutación.
    Implementa el patrón Repository para encapsular acceso a datos.
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Guarda una entidad (create o update).
        
        Args:
            entity: Entidad a guardar
            
        Returns:
            Entidad guardada (con ID asignado si es nueva)
        """
        pass
    
    @abstractmethod
    async def save_all(self, entities: List[T]) -> List[T]:
        """
        Guarda múltiples entidades.
        
        Args:
            entities: Lista de entidades a guardar
            
        Returns:
            Lista de entidades guardadas
        """
        pass
    
    @abstractmethod
    async def delete(self, entity: T) -> None:
        """
        Elimina una entidad.
        
        Args:
            entity: Entidad a eliminar
        """
        pass
    
    @abstractmethod
    async def delete_by_id(self, entity_id: ID) -> bool:
        """
        Elimina entidad por ID.
        
        Args:
            entity_id: ID de la entidad
            
        Returns:
            True si se eliminó, False si no existía
        """
        pass
    
    @abstractmethod
    async def delete_by_specification(
        self,
        spec: Specification[T]
    ) -> int:
        """
        Elimina entidades que cumplan la especificación.
        
        Args:
            spec: Especificación para filtrar
            
        Returns:
            Número de entidades eliminadas
        """
        pass


class ISpecificationRepository(IRepository[T, ID]):
    """
    Repositorio extendido con capacidades avanzadas de especificación.
    
    Para casos de uso que requieren queries complejas y optimizadas.
    """
    
    @abstractmethod
    async def find_first_by_specification(
        self,
        spec: Specification[T],
        sort: Optional[MultipleSortSpecification] = None
    ) -> Optional[T]:
        """
        Busca la primera entidad que cumpla la especificación.
        
        Args:
            spec: Especificación a evaluar
            sort: Ordenamiento opcional
            
        Returns:
            Primera entidad encontrada o None
        """
        pass
    
    @abstractmethod
    async def update_by_specification(
        self,
        spec: Specification[T],
        update_data: Dict[str, Any]
    ) -> int:
        """
        Actualiza entidades que cumplan la especificación.
        
        Args:
            spec: Especificación para filtrar
            update_data: Datos a actualizar
            
        Returns:
            Número de entidades actualizadas
        """
        pass


# Base classes para implementaciones concretas
class BaseReadOnlyRepository(IReadOnlyRepository[T, ID]):
    """
    Clase base para implementaciones de repositorio de solo lectura.
    
    Proporciona funcionalidad común que pueden reutilizar
    los adaptadores específicos (SQLAlchemy, MongoDB, etc.)
    """
    
    def __init__(self, entity_class: type):
        self.entity_class = entity_class
    
    async def exists_by_specification(self, spec: Specification[T]) -> bool:
        """Implementación por defecto usando count."""
        count = await self.count_by_specification(spec)
        return count > 0


class BaseRepository(BaseReadOnlyRepository[T, ID], IRepository[T, ID]):
    """
    Clase base para implementaciones de repositorio completo.
    """
    
    async def save_all(self, entities: List[T]) -> List[T]:
        """Implementación por defecto usando save individual."""
        saved_entities = []
        for entity in entities:
            saved_entity = await self.save(entity)
            saved_entities.append(saved_entity)
        return saved_entities
    
    async def delete_by_id(self, entity_id: ID) -> bool:
        """Implementación por defecto usando find + delete."""
        entity = await self.find_by_id(entity_id)
        if entity:
            await self.delete(entity)
            return True
        return False