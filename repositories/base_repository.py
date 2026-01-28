"""
Repositorio base genérico con paginación y filtros para todos los servicios.
Implementa el patrón Repository con operaciones CRUD estándar.
"""
from typing import TypeVar, Generic, List, Tuple, Dict, Any, Optional, Type
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from loguru import logger

T = TypeVar('T')  # Tipo del modelo SQLAlchemy


class BaseRepository(Generic[T]):
    """
    Repositorio base genérico con operaciones CRUD y paginación.
    
    Uso:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)
    
    Características:
    - CRUD completo (create, find, update, delete)
    - Paginación automática con filtros
    - Búsqueda por múltiples campos
    - Ordenamiento dinámico
    - Manejo de errores estandarizado
    """
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Inicializa el repositorio base.
        
        Args:
            session: Sesión asíncrona de SQLAlchemy
            model: Clase del modelo SQLAlchemy
        """
        self.session = session
        self.model = model
    
    async def create(self, data: dict, error_code: int) -> T:
        """
        Crea una nueva entidad.
        
        Args:
            data: Diccionario con datos de la entidad
            error_code: Código de error para excepciones
            
        Returns:
            Entidad creada
            
        Raises:
            Exception con error_code en caso de fallo
        """
        try:
            entity = self.model(**data)
            self.session.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
            logger.info(f"{self.model.__name__} created: {entity.id}")
            return entity
        except (IntegrityError, SQLAlchemyError) as e:
            await self.session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise Exception(f"Error code: {error_code}")
    
    async def find_by_id(self, entity_id: Any, error_code: int) -> Optional[T]:
        """
        Busca entidad por ID.
        
        Args:
            entity_id: ID de la entidad
            error_code: Código de error para excepciones
            
        Returns:
            Entidad encontrada o None
        """
        try:
            stmt = select(self.model).where(self.model.id == entity_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding {self.model.__name__}: {e}")
            raise Exception(f"Error code: {error_code}")
    
    async def find_paginated(
        self,
        page: int = 0,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        search_fields: Optional[List[str]] = None,
        error_code: int = 500
    ) -> Tuple[List[T], int]:
        """
        Lista entidades con paginación, filtros y búsqueda.
        
        Args:
            page: Número de página (0-indexed)
            page_size: Elementos por página (max 100)
            filters: Diccionario con filtros opcionales:
                - search: Búsqueda por texto
                - {campo}: Filtro por campo específico
                - sort_by: Campo para ordenar (default: created_at)
                - sort_order: asc/desc (default: desc)
            search_fields: Lista de campos donde buscar texto
            error_code: Código de error para excepciones
            
        Returns:
            Tuple[List[T], int]: (entidades, total)
            
        Example:
            users, total = await repo.find_paginated(
                page=0,
                page_size=10,
                filters={"role": "passenger", "is_active": True, "search": "john"},
                search_fields=["first_name", "last_name", "email"]
            )
        """
        try:
            # Validar page_size
            page_size = min(page_size, 100)
            offset = page * page_size
            
            # Inicializar filtros
            filters = filters or {}
            search = filters.pop('search', None)
            sort_by = filters.pop('sort_by', 'created_at')
            sort_order = filters.pop('sort_order', 'desc')
            
            # Query base
            query = select(self.model)
            
            # Aplicar filtros de búsqueda por texto
            if search and search_fields:
                search_conditions = []
                search_pattern = f"%{search}%"
                
                for field_name in search_fields:
                    if hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        search_conditions.append(field.ilike(search_pattern))
                
                if search_conditions:
                    query = query.where(or_(*search_conditions))
            
            # Aplicar filtros específicos
            for field_name, value in filters.items():
                if value is not None and hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    query = query.where(field == value)
            
            # Count total (antes de paginación)
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0
            
            # Ordenamiento
            if hasattr(self.model, sort_by):
                order_column = getattr(self.model, sort_by)
                if sort_order.lower() == 'asc':
                    query = query.order_by(order_column.asc())
                else:
                    query = query.order_by(order_column.desc())
            
            # Paginación
            query = query.limit(page_size).offset(offset)
            
            # Ejecutar
            result = await self.session.execute(query)
            entities = list(result.scalars().all())
            
            logger.info(
                f"Listed {len(entities)} {self.model.__name__}s "
                f"(page {page}, total {total})"
            )
            
            return entities, total
            
        except SQLAlchemyError as e:
            logger.error(f"Error listing {self.model.__name__}s: {e}")
            raise Exception(f"Error code: {error_code}")
    
    async def update(
        self,
        entity_id: Any,
        data: dict,
        error_code: int
    ) -> Optional[T]:
        """
        Actualiza una entidad.
        
        Args:
            entity_id: ID de la entidad
            data: Datos a actualizar
            error_code: Código de error
            
        Returns:
            Entidad actualizada o None
        """
        try:
            entity = await self.find_by_id(entity_id, error_code)
            if not entity:
                return None
            
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            await self.session.commit()
            await self.session.refresh(entity)
            logger.info(f"{self.model.__name__} updated: {entity_id}")
            return entity
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise Exception(f"Error code: {error_code}")
    
    async def delete(self, entity_id: Any, error_code: int, soft: bool = True) -> bool:
        """
        Elimina una entidad (soft o hard delete).
        
        Args:
            entity_id: ID de la entidad
            error_code: Código de error
            soft: True para soft delete (is_active=False), False para eliminar físicamente
            
        Returns:
            True si se eliminó
        """
        try:
            entity = await self.find_by_id(entity_id, error_code)
            if not entity:
                return False
            
            if soft and hasattr(entity, 'is_active'):
                entity.is_active = False
                if hasattr(entity, 'deleted_at'):
                    from datetime import datetime
                    entity.deleted_at = datetime.utcnow()
                await self.session.commit()
            else:
                await self.session.delete(entity)
                await self.session.commit()
            
            logger.info(f"{self.model.__name__} deleted: {entity_id}")
            return True
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise Exception(f"Error code: {error_code}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta entidades con filtros opcionales.
        
        Args:
            filters: Filtros opcionales
            
        Returns:
            Total de entidades
        """
        try:
            query = select(func.count(self.model.id))
            
            # Aplicar filtros
            if filters:
                for field_name, value in filters.items():
                    if value is not None and hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        query = query.where(field == value)
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}s: {e}")
            return 0
