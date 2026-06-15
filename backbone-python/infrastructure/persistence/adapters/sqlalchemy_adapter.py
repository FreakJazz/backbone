"""
SQLAlchemy Adapter - Adaptador para SQLAlchemy ORM
"""
from typing import TypeVar, Generic, Optional, List, Any, Dict, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, update, delete, and_, or_, not_
from sqlalchemy.exc import SQLAlchemyError
from ...domain.repositories.base_repository import BaseRepository, IRepository
from ...domain.repositories.unit_of_work import BaseUnitOfWork, IUnitOfWork
from ...domain.specifications.base_specification import Specification
from ...domain.specifications.sort_specification import MultipleSortSpecification, SortDirection
from ..exceptions.infrastructure_exceptions import DatabaseException


T = TypeVar('T')  # Tipo de entidad
ID = TypeVar('ID')  # Tipo de ID


class SQLAlchemySpecificationTranslator:
    """
    Traductor de especificaciones a clausulas SQLAlchemy.
    
    Convierte especificaciones del dominio a WHERE clauses
    que SQLAlchemy puede ejecutar.
    """
    
    def __init__(self, model_class: Type):
        self.model_class = model_class
    
    def translate(self, spec: Specification[T]) -> Any:
        """
        Traduce especificación a clausula SQLAlchemy.
        
        Args:
            spec: Especificación del dominio
            
        Returns:
            Clausula WHERE de SQLAlchemy
        """
        expression = spec.to_expression()
        return self._translate_expression(expression)
    
    def _translate_expression(self, expression: Dict[str, Any]) -> Any:
        """
        Traduce expresión genérica a SQLAlchemy.
        
        Args:
            expression: Expresión del dominio
            
        Returns:
            Clausula SQLAlchemy
        """
        if "operator" in expression:
            # Es una expresión compuesta (AND, OR, NOT)
            return self._translate_composite(expression)
        else:
            # Es una expresión de filtro simple
            return self._translate_filter(expression)
    
    def _translate_composite(self, expression: Dict[str, Any]) -> Any:
        """Traduce expresión compuesta."""
        operator = expression["operator"]
        
        if operator == "AND":
            left = self._translate_expression(expression["left"])
            right = self._translate_expression(expression["right"])
            return and_(left, right)
        
        elif operator == "OR":
            left = self._translate_expression(expression["left"])
            right = self._translate_expression(expression["right"])
            return or_(left, right)
        
        elif operator == "NOT":
            spec_expr = self._translate_expression(expression["spec"])
            return not_(spec_expr)
        
        else:
            raise ValueError(f"Unsupported composite operator: {operator}")
    
    def _translate_filter(self, expression: Dict[str, Any]) -> Any:
        """Traduce expresión de filtro simple."""
        field = expression["field"]
        operator = expression["operator"]
        value = expression["value"]
        
        # Obtener columna del modelo
        if not hasattr(self.model_class, field):
            raise ValueError(f"Field '{field}' not found in model {self.model_class.__name__}")
        
        column = getattr(self.model_class, field)
        
        # Traducir operador
        if operator == "eq":
            return column == value
        elif operator == "ne":
            return column != value
        elif operator == "lt":
            return column < value
        elif operator == "lte":
            return column <= value
        elif operator == "gt":
            return column > value
        elif operator == "gte":
            return column >= value
        elif operator == "like":
            return column.ilike(f"%{value}%")
        elif operator == "in":
            return column.in_(value)
        elif operator == "between":
            return column.between(value[0], value[1])
        elif operator == "is_null":
            return column.is_(None)
        elif operator == "is_not_null":
            return column.isnot(None)
        else:
            raise ValueError(f"Unsupported filter operator: {operator}")
    
    def translate_sort(self, sort_spec: MultipleSortSpecification) -> List[Any]:
        """
        Traduce especificación de ordenamiento.
        
        Args:
            sort_spec: Especificación de ordenamiento
            
        Returns:
            Lista de clausulas ORDER BY
        """
        order_clauses = []
        
        for sort_item in sort_spec:
            field = sort_item.field
            direction = sort_item.direction
            
            if not hasattr(self.model_class, field):
                raise ValueError(f"Sort field '{field}' not found in model {self.model_class.__name__}")
            
            column = getattr(self.model_class, field)
            
            if direction == SortDirection.ASC:
                order_clauses.append(column.asc())
            else:
                order_clauses.append(column.desc())
        
        return order_clauses


class SQLAlchemyRepository(BaseRepository[T, ID]):
    """
    Implementación de repositorio usando SQLAlchemy.
    
    Adaptador que implementa los contratos del dominio
    usando SQLAlchemy como motor de persistencia.
    """
    
    def __init__(
        self, 
        session: AsyncSession, 
        model_class: Type[T],
        entity_class: Type[T] = None
    ):
        super().__init__(entity_class or model_class)
        self.session = session
        self.model_class = model_class
        self.translator = SQLAlchemySpecificationTranslator(model_class)
    
    async def find_by_id(self, entity_id: ID) -> Optional[T]:
        """Busca entidad por ID."""
        try:
            result = await self.session.get(self.model_class, entity_id)
            return result
        except SQLAlchemyError as e:
            raise DatabaseException(
                message=f"Error finding entity by ID: {entity_id}",
                operation="find_by_id",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )
    
    async def find_by_specification(
        self,
        spec: Specification[T],
        sort: Optional[MultipleSortSpecification] = None
    ) -> List[T]:
        """Busca entidades por especificación."""
        try:
            query = select(self.model_class)
            
            # Aplicar filtros
            if spec:
                where_clause = self.translator.translate(spec)
                query = query.where(where_clause)
            
            # Aplicar ordenamiento
            if sort:
                order_clauses = self.translator.translate_sort(sort)
                query = query.order_by(*order_clauses)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error finding entities by specification",
                operation="find_by_specification",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )
    
    async def find_paginated_by_specification(
        self,
        spec: Optional[Specification[T]],
        page: int,
        page_size: int,
        sort: Optional[MultipleSortSpecification] = None
    ) -> tuple[List[T], int]:
        """Busca entidades paginadas."""
        try:
            # Query base para contar
            count_query = select(func.count()).select_from(self.model_class)
            data_query = select(self.model_class)
            
            # Aplicar filtros
            if spec:
                where_clause = self.translator.translate(spec)
                count_query = count_query.where(where_clause)
                data_query = data_query.where(where_clause)
            
            # Contar total
            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0
            
            # Aplicar ordenamiento
            if sort:
                order_clauses = self.translator.translate_sort(sort)
                data_query = data_query.order_by(*order_clauses)
            
            # Aplicar paginación
            offset = page * page_size
            data_query = data_query.limit(page_size).offset(offset)
            
            # Ejecutar query de datos
            data_result = await self.session.execute(data_query)
            entities = list(data_result.scalars().all())
            
            return entities, total
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error finding paginated entities",
                operation="find_paginated_by_specification",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )
    
    async def count_by_specification(
        self,
        spec: Optional[Specification[T]] = None
    ) -> int:
        """Cuenta entidades por especificación."""
        try:
            query = select(func.count()).select_from(self.model_class)
            
            if spec:
                where_clause = self.translator.translate(spec)
                query = query.where(where_clause)
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error counting entities",
                operation="count_by_specification",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )
    
    async def save(self, entity: T) -> T:
        """Guarda entidad."""
        try:
            # SQLAlchemy detecta automáticamente si es insert o update
            self.session.add(entity)
            await self.session.flush()  # Para obtener el ID si es nuevo
            await self.session.refresh(entity)
            return entity
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error saving entity",
                operation="save",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )
    
    async def delete(self, entity: T) -> None:
        """Elimina entidad."""
        try:
            await self.session.delete(entity)
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error deleting entity",
                operation="delete",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )
    
    async def delete_by_specification(
        self,
        spec: Specification[T]
    ) -> int:
        """Elimina entidades por especificación."""
        try:
            where_clause = self.translator.translate(spec)
            query = delete(self.model_class).where(where_clause)
            
            result = await self.session.execute(query)
            return result.rowcount or 0
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error deleting entities by specification",
                operation="delete_by_specification",
                table=self.model_class.__tablename__,
                original_error=str(e)
            )


class SQLAlchemyUnitOfWork(BaseUnitOfWork):
    """
    Implementación de Unit of Work para SQLAlchemy.
    
    Maneja transacciones SQLAlchemy y coordina el guardado
    de múltiples entidades.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session
        self._transaction = None
    
    async def __aenter__(self):
        """Inicia transacción."""
        self._transaction = await self.session.begin()
        return await super().__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza transacción."""
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            if self._transaction:
                if exc_type is not None and not self._rolled_back:
                    await self._transaction.rollback()
                elif not self._committed and not self._rolled_back:
                    await self._transaction.commit()
    
    async def commit(self) -> None:
        """Confirma cambios."""
        try:
            # Procesar entidades registradas
            for entity in self._new_entities:
                self.session.add(entity)
            
            for entity in self._dirty_entities:
                # SQLAlchemy detecta cambios automáticamente si la entidad
                # está en la sesión, sino la agregamos
                self.session.add(entity)
            
            for entity in self._removed_entities:
                await self.session.delete(entity)
            
            # Commit de la transacción
            if self._transaction:
                await self._transaction.commit()
            else:
                await self.session.commit()
            
            self._committed = True
            self.clear_tracking()
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error committing unit of work",
                operation="commit",
                original_error=str(e)
            )
    
    async def rollback(self) -> None:
        """Revierte cambios."""
        try:
            if self._transaction:
                await self._transaction.rollback()
            else:
                await self.session.rollback()
            
            self._rolled_back = True
            self.clear_tracking()
            
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Error rolling back unit of work",
                operation="rollback",
                original_error=str(e)
            )