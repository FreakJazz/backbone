"""
Unit of Work - Patrón Unit of Work para transacciones
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IUnitOfWork(ABC):
    """
    Contrato para Unit of Work.
    
    Maneja transacciones y coordina el guardado de múltiples
    agregados de manera atómica.
    
    Características:
    - Transacciones atómicas
    - Registro de cambios
    - Commit/Rollback
    - Context manager support
    """
    
    @abstractmethod
    async def __aenter__(self):
        """Inicia la unidad de trabajo."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza la unidad de trabajo."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """
        Confirma todos los cambios pendientes.
        
        Persiste todas las modificaciones realizadas durante
        la unidad de trabajo de manera atómica.
        """
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """
        Revierte todos los cambios pendientes.
        
        Descarta todas las modificaciones realizadas durante
        la unidad de trabajo.
        """
        pass
    
    @abstractmethod
    def register_new(self, entity: Any) -> None:
        """
        Registra una entidad nueva para insertar.
        
        Args:
            entity: Entidad nueva a insertar
        """
        pass
    
    @abstractmethod
    def register_dirty(self, entity: Any) -> None:
        """
        Registra una entidad modificada para actualizar.
        
        Args:
            entity: Entidad modificada a actualizar
        """
        pass
    
    @abstractmethod
    def register_removed(self, entity: Any) -> None:
        """
        Registra una entidad para eliminar.
        
        Args:
            entity: Entidad a eliminar
        """
        pass
    
    @abstractmethod
    def register_clean(self, entity: Any) -> None:
        """
        Registra una entidad como limpia (sin cambios).
        
        Args:
            entity: Entidad sin cambios
        """
        pass


class IRepositoryRegistry(ABC):
    """
    Registro de repositorios para Unit of Work.
    
    Permite al UoW acceder a repositorios específicos
    manteniendo el desacoplamiento.
    """
    
    @abstractmethod
    def get_repository(self, entity_type: type) -> Any:
        """
        Obtiene repositorio para un tipo de entidad.
        
        Args:
            entity_type: Clase de la entidad
            
        Returns:
            Repositorio correspondiente
        """
        pass
    
    @abstractmethod
    def register_repository(self, entity_type: type, repository: Any) -> None:
        """
        Registra un repositorio para un tipo de entidad.
        
        Args:
            entity_type: Clase de la entidad
            repository: Repositorio a registrar
        """
        pass


class BaseUnitOfWork(IUnitOfWork):
    """
    Implementación base de Unit of Work.
    
    Proporciona funcionalidad común que pueden extender
    los adaptadores específicos.
    """
    
    def __init__(self):
        self._new_entities = []
        self._dirty_entities = []
        self._removed_entities = []
        self._clean_entities = []
        self._committed = False
        self._rolled_back = False
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit con rollback automático si hay excepción."""
        if exc_type is not None and not self._rolled_back:
            await self.rollback()
        elif not self._committed and not self._rolled_back:
            # Auto-commit si no hubo excepciones y no se hizo commit explícito
            await self.commit()
    
    def register_new(self, entity: Any) -> None:
        """Registra entidad nueva."""
        if entity not in self._new_entities:
            self._new_entities.append(entity)
        
        # Remover de otros registros si está presente
        self._remove_from_other_lists(entity, self._new_entities)
    
    def register_dirty(self, entity: Any) -> None:
        """Registra entidad modificada."""
        if entity not in self._dirty_entities and entity not in self._new_entities:
            self._dirty_entities.append(entity)
        
        # Remover de clean si estaba ahí
        if entity in self._clean_entities:
            self._clean_entities.remove(entity)
    
    def register_removed(self, entity: Any) -> None:
        """Registra entidad para eliminar."""
        if entity not in self._removed_entities:
            self._removed_entities.append(entity)
        
        # Remover de otros registros
        self._remove_from_other_lists(entity, self._removed_entities)
    
    def register_clean(self, entity: Any) -> None:
        """Registra entidad limpia."""
        if (entity not in self._clean_entities and 
            entity not in self._new_entities and
            entity not in self._dirty_entities and
            entity not in self._removed_entities):
            self._clean_entities.append(entity)
    
    def _remove_from_other_lists(self, entity: Any, except_list: list) -> None:
        """Remueve entidad de otras listas excepto la especificada."""
        all_lists = [
            self._new_entities,
            self._dirty_entities, 
            self._removed_entities,
            self._clean_entities
        ]
        
        for entity_list in all_lists:
            if entity_list is not except_list and entity in entity_list:
                entity_list.remove(entity)
    
    @property
    def has_changes(self) -> bool:
        """Verifica si hay cambios pendientes."""
        return (len(self._new_entities) > 0 or 
                len(self._dirty_entities) > 0 or 
                len(self._removed_entities) > 0)
    
    @property
    def new_entities(self) -> list:
        """Entidades nuevas registradas."""
        return self._new_entities.copy()
    
    @property
    def dirty_entities(self) -> list:
        """Entidades modificadas registradas."""
        return self._dirty_entities.copy()
    
    @property
    def removed_entities(self) -> list:
        """Entidades a eliminar registradas."""
        return self._removed_entities.copy()
    
    def clear_tracking(self) -> None:
        """Limpia el tracking de entidades."""
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
        self._clean_entities.clear()
        self._committed = False
        self._rolled_back = False


class UnitOfWorkManager:
    """
    Manager para manejar múltiples Unit of Work.
    
    Útil para casos donde necesitas coordinar múltiples
    contextos de persistencia (ej: diferentes bases de datos).
    """
    
    def __init__(self):
        self._units_of_work: Dict[str, IUnitOfWork] = {}
        self._current_transaction_id: Optional[str] = None
    
    def register_unit_of_work(self, name: str, uow: IUnitOfWork) -> None:
        """
        Registra un Unit of Work.
        
        Args:
            name: Nombre identificador del UoW
            uow: Instancia del Unit of Work
        """
        self._units_of_work[name] = uow
    
    def get_unit_of_work(self, name: str) -> Optional[IUnitOfWork]:
        """
        Obtiene un Unit of Work por nombre.
        
        Args:
            name: Nombre del UoW
            
        Returns:
            Unit of Work o None si no existe
        """
        return self._units_of_work.get(name)
    
    async def commit_all(self) -> None:
        """Hace commit de todos los Unit of Work registrados."""
        for name, uow in self._units_of_work.items():
            try:
                await uow.commit()
            except Exception as e:
                # Si falla uno, hacer rollback de todos
                await self.rollback_all()
                raise e
    
    async def rollback_all(self) -> None:
        """Hace rollback de todos los Unit of Work registrados."""
        for name, uow in self._units_of_work.items():
            try:
                await uow.rollback()
            except Exception:
                # Continuar con rollback de otros incluso si uno falla
                continue
    
    def clear(self) -> None:
        """Limpia todos los Unit of Work registrados."""
        self._units_of_work.clear()
        self._current_transaction_id = None