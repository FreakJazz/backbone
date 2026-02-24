"""
Mock Repository - Implementación de repositorio para testing
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from ...domain.repositories.base_repository import BaseRepository
from ...domain.specifications.base_specification import Specification
from ...domain.specifications.sort_specification import MultipleSortSpecification


T = TypeVar('T')
ID = TypeVar('ID')


class MockRepository(BaseRepository[T, ID]):
    """
    Repositorio en memoria para testing.
    
    Simula comportamiento de repositorio real almacenando
    datos en memoria. Útil para tests unitarios que requieren
    persistencia sin dependencias externas.
    """
    
    def __init__(self, entity_class: Type[T]):
        super().__init__(entity_class)
        self._data: Dict[ID, T] = {}
        self._next_id: int = 1
        self._saved_entities: List[T] = []
        self._deleted_entities: List[T] = []
    
    def _generate_id(self) -> ID:
        """Genera ID único para nuevas entidades."""
        current_id = self._next_id
        self._next_id += 1
        return current_id
    
    def _get_entity_id(self, entity: T) -> Optional[ID]:
        """
        Extrae ID de una entidad.
        
        Override este método según la convención de ID
        de tu entidad (id, _id, etc).
        """
        # Para diccionarios, buscar claves 'id' o '_id'
        if isinstance(entity, dict):
            if 'id' in entity:
                return entity['id']
            elif '_id' in entity:
                return entity['_id']
        # Para objetos, buscar atributos 'id' o '_id'
        elif hasattr(entity, 'id'):
            return getattr(entity, 'id')
        elif hasattr(entity, '_id'):
            return getattr(entity, '_id')
        
        # Como último recurso, buscar por valor en el diccionario
        for stored_id, stored_entity in self._data.items():
            if stored_entity == entity:
                return stored_id
        return None
    
    def _set_entity_id(self, entity: T, entity_id: ID) -> None:
        """
        Asigna ID a una entidad.
        
        Override según convención de ID de tu entidad.
        """
        # Para diccionarios, asignar a clave 'id'
        if isinstance(entity, dict):
            entity['id'] = entity_id
        # Para objetos, asignar a atributo 'id' o '_id'
        elif hasattr(entity, 'id'):
            setattr(entity, 'id', entity_id)
        elif hasattr(entity, '_id'):
            setattr(entity, '_id', entity_id)
    
    def _matches_specification(self, entity: T, spec: Specification[T]) -> bool:
        """
        Evalúa si entidad cumple especificación.
        
        Implementación básica que evalúa la especificación
        contra la entidad. Para casos complejos, override.
        """
        if spec is None:
            return True
        
        try:
            # Check if specification has is_satisfied_by method (simple pattern)
            if hasattr(spec, 'is_satisfied_by'):
                return spec.is_satisfied_by(entity)
            
            # Otherwise, use backbone specification pattern with to_expression
            expression = spec.to_expression()
            return self._evaluate_expression(entity, expression)
        except Exception:
            # Si no se puede evaluar, asumir que no cumple
            return False
    
    def _evaluate_expression(self, entity: T, expression: Dict[str, Any]) -> bool:
        """Evalúa expresión contra entidad."""
        if "operator" in expression:
            # Expresión compuesta
            return self._evaluate_composite(entity, expression)
        else:
            # Expresión de filtro simple
            return self._evaluate_filter(entity, expression)
    
    def _evaluate_composite(self, entity: T, expression: Dict[str, Any]) -> bool:
        """Evalúa expresión compuesta."""
        operator = expression["operator"]
        
        if operator == "AND":
            left_result = self._evaluate_expression(entity, expression["left"])
            right_result = self._evaluate_expression(entity, expression["right"])
            return left_result and right_result
        
        elif operator == "OR":
            left_result = self._evaluate_expression(entity, expression["left"])
            right_result = self._evaluate_expression(entity, expression["right"])
            return left_result or right_result
        
        elif operator == "NOT":
            spec_result = self._evaluate_expression(entity, expression["spec"])
            return not spec_result
        
        return False
    
    def _evaluate_filter(self, entity: T, expression: Dict[str, Any]) -> bool:
        """Evalúa expresión de filtro simple."""
        field = expression["field"]
        operator = expression["operator"]
        value = expression["value"]
        
        # Obtener valor del campo de la entidad
        entity_value = self._get_field_value(entity, field)
        
        # Evaluar operador
        if operator == "eq":
            return entity_value == value
        elif operator == "ne":
            return entity_value != value
        elif operator == "lt":
            return entity_value < value
        elif operator == "lte":
            return entity_value <= value
        elif operator == "gt":
            return entity_value > value
        elif operator == "gte":
            return entity_value >= value
        elif operator == "like":
            return str(value).lower() in str(entity_value).lower()
        elif operator == "in":
            return entity_value in value
        elif operator == "between":
            return value[0] <= entity_value <= value[1]
        elif operator == "is_null":
            return entity_value is None
        elif operator == "is_not_null":
            return entity_value is not None
        
        return False
    
    def _get_field_value(self, entity: T, field: str) -> Any:
        """Obtiene valor de campo de la entidad."""
        if hasattr(entity, field):
            return getattr(entity, field)
        elif hasattr(entity, '__getitem__'):
            try:
                return entity[field]
            except (KeyError, TypeError):
                pass
        return None
    
    def _apply_sort(self, entities: List[T], sort: MultipleSortSpecification) -> List[T]:
        """Aplica ordenamiento a lista de entidades."""
        if not sort:
            return entities
        
        def sort_key(entity: T) -> tuple:
            key_parts = []
            for sort_item in sort:
                field_value = self._get_field_value(entity, sort_item.field)
                
                # Para ordenamiento descendente, negar valores numéricos
                # Para strings, podemos usar reverse=True en sorted()
                if sort_item.direction.value == "desc":
                    if isinstance(field_value, (int, float)):
                        field_value = -field_value
                    # Para strings mantenemos el valor, usaremos reverse
                
                key_parts.append(field_value)
            
            return tuple(key_parts)
        
        # Verificar si algún sort es descendente
        has_desc = any(
            sort_item.direction.value == "desc" 
            for sort_item in sort
        )
        
        return sorted(entities, key=sort_key, reverse=has_desc)
    
    # Implementación de métodos del repositorio
    
    async def find_by_id(self, entity_id: ID) -> Optional[T]:
        """Busca entidad por ID."""
        return self._data.get(entity_id)
    
    async def find_by_specification(
        self,
        spec: Specification[T],
        sort: Optional[MultipleSortSpecification] = None
    ) -> List[T]:
        """Busca entidades por especificación."""
        matching_entities = [
            entity for entity in self._data.values()
            if self._matches_specification(entity, spec)
        ]
        
        if sort:
            matching_entities = self._apply_sort(matching_entities, sort)
        
        return matching_entities
    
    async def find_paginated_by_specification(
        self,
        spec: Optional[Specification[T]],
        page: int,
        page_size: int,
        sort: Optional[MultipleSortSpecification] = None
    ) -> tuple[List[T], int]:
        """Busca entidades paginadas."""
        # Obtener todas las entidades que cumplen la especificación
        all_matching = await self.find_by_specification(spec, sort)
        
        total = len(all_matching)
        
        # Aplicar paginación
        start_index = page * page_size
        end_index = start_index + page_size
        page_entities = all_matching[start_index:end_index]
        
        return page_entities, total
    
    async def count_by_specification(
        self,
        spec: Optional[Specification[T]] = None
    ) -> int:
        """Cuenta entidades por especificación."""
        if spec is None:
            return len(self._data)
        
        matching_count = sum(
            1 for entity in self._data.values()
            if self._matches_specification(entity, spec)
        )
        
        return matching_count
    
    async def save(self, entity: T) -> T:
        """Guarda entidad."""
        entity_id = self._get_entity_id(entity)
        
        if entity_id is None:
            # Nueva entidad - generar ID
            entity_id = self._generate_id()
            self._set_entity_id(entity, entity_id)
        
        # Guardar en el diccionario
        self._data[entity_id] = entity
        
        # Registrar en historial
        self._saved_entities.append(entity)
        
        return entity
    
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """Alias for find_by_id - commonly used in tests."""
        return await self.find_by_id(entity_id)
    
    async def get_all(self) -> List[T]:
        """Returns all entities - commonly used in tests."""
        return list(self._data.values())
    
    async def find(
        self, 
        spec: Specification[T],
        sort: Optional[MultipleSortSpecification] = None
    ) -> List[T]:
        """Alias for find_by_specification - commonly used in tests."""
        return await self.find_by_specification(spec, sort)
    
    async def delete(self, entity: T) -> None:
        """Elimina entidad."""
        entity_id = self._get_entity_id(entity)
        
        if entity_id is not None and entity_id in self._data:
            del self._data[entity_id]
            self._deleted_entities.append(entity)
    
    async def delete_by_id(self, entity_id: ID) -> bool:
        """Delete entity by ID - commonly used in tests."""
        if entity_id in self._data:
            entity = self._data[entity_id]
            del self._data[entity_id]
            self._deleted_entities.append(entity)
            return True
        return False
    async def delete_by_specification(
        self,
        spec: Specification[T]
    ) -> int:
        """Elimina entidades por especificación."""
        entities_to_delete = await self.find_by_specification(spec)
        
        for entity in entities_to_delete:
            await self.delete(entity)
        
        return len(entities_to_delete)
    
    # Métodos específicos para testing
    
    def clear(self) -> None:
        """Limpia todos los datos del repositorio."""
        self._data.clear()
        self._next_id = 1
        self._saved_entities.clear()
        self._deleted_entities.clear()
    
    def seed_data(self, entities: List[T]) -> None:
        """
        Siembra datos iniciales en el repositorio.
        
        Args:
            entities: Lista de entidades a agregar
        """
        for entity in entities:
            entity_id = self._get_entity_id(entity)
            if entity_id is None:
                entity_id = self._generate_id()
                self._set_entity_id(entity, entity_id)
            
            self._data[entity_id] = entity
    
    def get_all_data(self) -> List[T]:
        """Retorna todas las entidades almacenadas."""
        return list(self._data.values())
    
    def get_saved_entities(self) -> List[T]:
        """Retorna entidades guardadas durante el test."""
        return self._saved_entities.copy()
    
    def get_deleted_entities(self) -> List[T]:
        """Retorna entidades eliminadas durante el test."""
        return self._deleted_entities.copy()
    
    def count_total(self) -> int:
        """Cuenta total de entidades almacenadas."""
        return len(self._data)