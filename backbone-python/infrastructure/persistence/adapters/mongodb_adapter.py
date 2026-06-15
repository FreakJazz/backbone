"""
MongoDB Adapter - Adaptador para MongoDB con Motor (PyMongo Async)
"""
from typing import TypeVar, Generic, Optional, List, Any, Dict, Type, Union
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId
import re
from ...domain.repositories.base_repository import BaseRepository, IRepository
from ...domain.repositories.unit_of_work import BaseUnitOfWork, IUnitOfWork
from ...domain.specifications.base_specification import Specification
from ...domain.specifications.sort_specification import MultipleSortSpecification, SortDirection
from ..exceptions.infrastructure_exceptions import DatabaseException


T = TypeVar('T')
ID = TypeVar('ID')


class MongoDBSpecificationTranslator:
    """
    Traductor de especificaciones a queries MongoDB.
    
    Convierte especificaciones del dominio a filtros
    que MongoDB puede ejecutar.
    """
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    def translate(self, spec: Specification[T]) -> Dict[str, Any]:
        """
        Traduce especificación a filtro MongoDB.
        
        Args:
            spec: Especificación del dominio
            
        Returns:
            Diccionario de filtro MongoDB
        """
        expression = spec.to_expression()
        return self._translate_expression(expression)
    
    def _translate_expression(self, expression: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traduce expresión genérica a MongoDB.
        
        Args:
            expression: Expresión del dominio
            
        Returns:
            Filtro MongoDB
        """
        if "operator" in expression:
            # Es una expresión compuesta (AND, OR, NOT)
            return self._translate_composite(expression)
        else:
            # Es una expresión de filtro simple
            return self._translate_filter(expression)
    
    def _translate_composite(self, expression: Dict[str, Any]) -> Dict[str, Any]:
        """Traduce expresión compuesta."""
        operator = expression["operator"]
        
        if operator == "AND":
            left = self._translate_expression(expression["left"])
            right = self._translate_expression(expression["right"])
            return {"$and": [left, right]}
        
        elif operator == "OR":
            left = self._translate_expression(expression["left"])
            right = self._translate_expression(expression["right"])
            return {"$or": [left, right]}
        
        elif operator == "NOT":
            spec_expr = self._translate_expression(expression["spec"])
            return {"$not": spec_expr}
        
        else:
            raise ValueError(f"Unsupported composite operator: {operator}")
    
    def _translate_filter(self, expression: Dict[str, Any]) -> Dict[str, Any]:
        """Traduce expresión de filtro simple."""
        field = expression["field"]
        operator = expression["operator"]
        value = expression["value"]
        
        # Manejar conversión de ObjectId para _id
        if field == "_id" and isinstance(value, str):
            try:
                value = ObjectId(value)
            except InvalidId:
                pass  # Dejar como string si no es un ObjectId válido
        
        # Traducir operador
        if operator == "eq":
            return {field: value}
        elif operator == "ne":
            return {field: {"$ne": value}}
        elif operator == "lt":
            return {field: {"$lt": value}}
        elif operator == "lte":
            return {field: {"$lte": value}}
        elif operator == "gt":
            return {field: {"$gt": value}}
        elif operator == "gte":
            return {field: {"$gte": value}}
        elif operator == "like":
            # Usar regex para LIKE
            pattern = re.escape(str(value))
            return {field: {"$regex": pattern, "$options": "i"}}
        elif operator == "in":
            return {field: {"$in": value}}
        elif operator == "between":
            return {field: {"$gte": value[0], "$lte": value[1]}}
        elif operator == "is_null":
            return {field: None}
        elif operator == "is_not_null":
            return {field: {"$ne": None}}
        else:
            raise ValueError(f"Unsupported filter operator: {operator}")
    
    def translate_sort(self, sort_spec: MultipleSortSpecification) -> List[tuple[str, int]]:
        """
        Traduce especificación de ordenamiento.
        
        Args:
            sort_spec: Especificación de ordenamiento
            
        Returns:
            Lista de tuplas (field, direction) para MongoDB
        """
        sort_list = []
        
        for sort_item in sort_spec:
            field = sort_item.field
            direction = sort_item.direction
            
            mongo_direction = ASCENDING if direction == SortDirection.ASC else DESCENDING
            sort_list.append((field, mongo_direction))
        
        return sort_list


class MongoDBRepository(BaseRepository[T, ID]):
    """
    Implementación de repositorio usando MongoDB.
    
    Adaptador que implementa los contratos del dominio
    usando MongoDB como motor de persistencia.
    """
    
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        collection_name: str,
        entity_class: Type[T]
    ):
        super().__init__(entity_class)
        self.database = database
        self.collection_name = collection_name
        self.collection: AsyncIOMotorCollection = database[collection_name]
        self.translator = MongoDBSpecificationTranslator(collection_name)
    
    def _to_entity(self, doc: Dict[str, Any]) -> T:
        """
        Convierte documento MongoDB a entidad.
        
        Por defecto asume que la entidad puede construirse
        directamente desde el documento. Override si necesitas
        mapeo específico.
        """
        if doc is None:
            return None
        
        # Convertir ObjectId a string si existe
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        
        return self.entity_class(**doc) if hasattr(self.entity_class, '__init__') else doc
    
    def _to_document(self, entity: T) -> Dict[str, Any]:
        """
        Convierte entidad a documento MongoDB.
        
        Por defecto asume que la entidad tiene un método dict()
        o es un diccionario. Override si necesitas mapeo específico.
        """
        if hasattr(entity, 'dict'):
            # Pydantic model
            doc = entity.dict()
        elif hasattr(entity, '__dict__'):
            # Python object
            doc = entity.__dict__.copy()
        else:
            # Dictionary or other
            doc = dict(entity)
        
        # Convertir string ID a ObjectId si es necesario
        if "_id" in doc and isinstance(doc["_id"], str):
            try:
                doc["_id"] = ObjectId(doc["_id"])
            except InvalidId:
                pass  # Dejar como string si no es un ObjectId válido
        
        return doc
    
    async def find_by_id(self, entity_id: ID) -> Optional[T]:
        """Busca entidad por ID."""
        try:
            # Convertir a ObjectId si es string
            query_id = entity_id
            if isinstance(entity_id, str):
                try:
                    query_id = ObjectId(entity_id)
                except InvalidId:
                    pass  # Dejar como string
            
            doc = await self.collection.find_one({"_id": query_id})
            return self._to_entity(doc)
            
        except PyMongoError as e:
            raise DatabaseException(
                message=f"Error finding entity by ID: {entity_id}",
                operation="find_by_id",
                table=self.collection_name,
                original_error=str(e)
            )
    
    async def find_by_specification(
        self,
        spec: Specification[T],
        sort: Optional[MultipleSortSpecification] = None
    ) -> List[T]:
        """Busca entidades por especificación."""
        try:
            filter_dict = {}
            if spec:
                filter_dict = self.translator.translate(spec)
            
            cursor = self.collection.find(filter_dict)
            
            # Aplicar ordenamiento
            if sort:
                sort_list = self.translator.translate_sort(sort)
                cursor = cursor.sort(sort_list)
            
            docs = await cursor.to_list(length=None)
            return [self._to_entity(doc) for doc in docs]
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error finding entities by specification",
                operation="find_by_specification",
                table=self.collection_name,
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
            filter_dict = {}
            if spec:
                filter_dict = self.translator.translate(spec)
            
            # Contar total
            total = await self.collection.count_documents(filter_dict)
            
            # Query de datos con paginación
            cursor = self.collection.find(filter_dict)
            
            # Aplicar ordenamiento
            if sort:
                sort_list = self.translator.translate_sort(sort)
                cursor = cursor.sort(sort_list)
            
            # Aplicar paginación
            offset = page * page_size
            cursor = cursor.skip(offset).limit(page_size)
            
            docs = await cursor.to_list(length=page_size)
            entities = [self._to_entity(doc) for doc in docs]
            
            return entities, total
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error finding paginated entities",
                operation="find_paginated_by_specification",
                table=self.collection_name,
                original_error=str(e)
            )
    
    async def count_by_specification(
        self,
        spec: Optional[Specification[T]] = None
    ) -> int:
        """Cuenta entidades por especificación."""
        try:
            filter_dict = {}
            if spec:
                filter_dict = self.translator.translate(spec)
            
            return await self.collection.count_documents(filter_dict)
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error counting entities",
                operation="count_by_specification",
                table=self.collection_name,
                original_error=str(e)
            )
    
    async def save(self, entity: T) -> T:
        """Guarda entidad."""
        try:
            doc = self._to_document(entity)
            
            # Si tiene _id, es update, sino es insert
            if "_id" in doc and doc["_id"] is not None:
                # Update
                entity_id = doc.pop("_id")
                result = await self.collection.replace_one(
                    {"_id": entity_id},
                    doc,
                    upsert=True
                )
                doc["_id"] = entity_id
            else:
                # Insert
                result = await self.collection.insert_one(doc)
                doc["_id"] = result.inserted_id
            
            return self._to_entity(doc)
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error saving entity",
                operation="save",
                table=self.collection_name,
                original_error=str(e)
            )
    
    async def delete(self, entity: T) -> None:
        """Elimina entidad."""
        try:
            doc = self._to_document(entity)
            if "_id" not in doc:
                raise ValueError("Entity must have _id to be deleted")
            
            await self.collection.delete_one({"_id": doc["_id"]})
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error deleting entity",
                operation="delete",
                table=self.collection_name,
                original_error=str(e)
            )
    
    async def delete_by_specification(
        self,
        spec: Specification[T]
    ) -> int:
        """Elimina entidades por especificación."""
        try:
            filter_dict = self.translator.translate(spec)
            result = await self.collection.delete_many(filter_dict)
            return result.deleted_count
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error deleting entities by specification",
                operation="delete_by_specification",
                table=self.collection_name,
                original_error=str(e)
            )


class MongoDBUnitOfWork(BaseUnitOfWork):
    """
    Implementación de Unit of Work para MongoDB.
    
    MongoDB no tiene transacciones ACID como las bases de datos
    relacionales, pero podemos simular el comportamiento usando
    operaciones batch y tracking de cambios.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__()
        self.database = database
        self._session = None
        self._repositories: Dict[str, MongoDBRepository] = {}
    
    def get_repository(
        self,
        collection_name: str,
        entity_class: Type[T]
    ) -> MongoDBRepository[T, Any]:
        """
        Obtiene repositorio para colección específica.
        
        Args:
            collection_name: Nombre de la colección
            entity_class: Clase de la entidad
            
        Returns:
            Repositorio MongoDB
        """
        if collection_name not in self._repositories:
            self._repositories[collection_name] = MongoDBRepository(
                self.database,
                collection_name,
                entity_class
            )
        return self._repositories[collection_name]
    
    async def __aenter__(self):
        """Inicia sesión MongoDB si está disponible."""
        # MongoDB Atlas y replica sets soportan transacciones
        # Para instancias standalone, trabajamos sin transacciones
        try:
            self._session = await self.database.client.start_session()
            await self._session.__aenter__()
        except Exception:
            # No todas las configuraciones de MongoDB soportan sesiones
            self._session = None
        
        return await super().__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza sesión MongoDB."""
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            if self._session:
                await self._session.__aexit__(exc_type, exc_val, exc_tb)
    
    async def commit(self) -> None:
        """Confirma cambios."""
        try:
            # Usar transacción si está disponible
            if self._session:
                async with self._session.start_transaction():
                    await self._perform_operations()
            else:
                # Sin transacciones, ejecutar operaciones directamente
                await self._perform_operations()
            
            self._committed = True
            self.clear_tracking()
            
        except PyMongoError as e:
            raise DatabaseException(
                message="Error committing unit of work",
                operation="commit",
                original_error=str(e)
            )
    
    async def rollback(self) -> None:
        """Revierte cambios."""
        # MongoDB sin transacciones no puede hacer rollback real
        # Solo limpiamos el tracking
        self._rolled_back = True
        self.clear_tracking()
    
    async def _perform_operations(self) -> None:
        """Ejecuta todas las operaciones pendientes."""
        # Para MongoDB, necesitamos determinar la colección de cada entidad
        # Esto puede requerir metadatos adicionales o convenciones
        
        # Operaciones agrupadas por colección
        collections_ops = {}
        
        for entity in self._new_entities:
            collection_name = self._get_collection_name(entity)
            if collection_name not in collections_ops:
                collections_ops[collection_name] = {"inserts": [], "updates": [], "deletes": []}
            
            # Para MongoDB, save() maneja tanto insert como update
            repo = self._get_repository_for_entity(entity)
            await repo.save(entity)
        
        for entity in self._dirty_entities:
            repo = self._get_repository_for_entity(entity)
            await repo.save(entity)
        
        for entity in self._removed_entities:
            repo = self._get_repository_for_entity(entity)
            await repo.delete(entity)
    
    def _get_collection_name(self, entity: T) -> str:
        """
        Obtiene nombre de colección para una entidad.
        
        Override este método para implementar tu estrategia
        de mapeo entidad -> colección.
        """
        # Estrategia por defecto: usar nombre de clase en minúsculas
        return entity.__class__.__name__.lower()
    
    def _get_repository_for_entity(self, entity: T) -> MongoDBRepository:
        """Obtiene repositorio para una entidad."""
        collection_name = self._get_collection_name(entity)
        entity_class = entity.__class__
        return self.get_repository(collection_name, entity_class)