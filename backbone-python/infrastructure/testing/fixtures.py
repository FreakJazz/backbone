"""
Test Fixtures - Factories y builders para datos de prueba
"""
from typing import TypeVar, Generic, Type, Any, Dict, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid


T = TypeVar('T')


@dataclass
class FixtureConfig:
    """Configuración para fixtures."""
    auto_generate_ids: bool = True
    default_datetime: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_start: int = 1


class BaseFixtureFactory(Generic[T]):
    """
    Factory base para crear fixtures de entidades.
    
    Permite crear instancias de entidades con valores
    predeterminados y sobrescribir campos específicos.
    """
    
    def __init__(
        self,
        entity_class: Type[T],
        defaults: Dict[str, Any] = None,
        config: FixtureConfig = None
    ):
        self.entity_class = entity_class
        self.defaults = defaults or {}
        self.config = config or FixtureConfig()
        self._sequence_counters: Dict[str, int] = {}
    
    def create(self, **overrides) -> T:
        """
        Crea instancia de entidad con valores por defecto.
        
        Args:
            **overrides: Campos a sobrescribir
            
        Returns:
            Instancia de la entidad
        """
        # Combinar defaults con overrides
        data = {**self.defaults, **overrides}
        
        # Aplicar valores por defecto del factory
        data = self._apply_factory_defaults(data)
        
        # Crear instancia
        return self._create_instance(data)
    
    def create_batch(self, count: int, **overrides) -> List[T]:
        """
        Crea múltiples instancias.
        
        Args:
            count: Cantidad de instancias
            **overrides: Campos base a sobrescribir
            
        Returns:
            Lista de instancias
        """
        return [
            self.create(**overrides)
            for _ in range(count)
        ]
    
    def _apply_factory_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica valores por defecto del factory."""
        # Generar ID si no existe y está configurado
        if self.config.auto_generate_ids:
            if 'id' not in data and hasattr(self.entity_class, 'id'):
                data['id'] = self._generate_id()
            elif '_id' not in data and hasattr(self.entity_class, '_id'):
                data['_id'] = self._generate_id()
        
        # Timestamp por defecto para campos de fecha
        datetime_fields = ['created_at', 'updated_at', 'timestamp']
        for field_name in datetime_fields:
            if (
                field_name not in data and 
                hasattr(self.entity_class, field_name)
            ):
                data[field_name] = self.config.default_datetime
        
        return data
    
    def _generate_id(self) -> Any:
        """Genera ID único."""
        # Por defecto usar UUID string
        return str(uuid.uuid4())
    
    def _create_instance(self, data: Dict[str, Any]) -> T:
        """
        Crea instancia de la entidad.
        
        Override para casos especiales de construcción.
        """
        try:
            # Intentar construcción directa
            return self.entity_class(**data)
        except TypeError:
            # Si falla, intentar construcción por atributos
            instance = self.entity_class()
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            return instance
    
    def sequence(self, field_name: str, template: str = None) -> Callable[[int], Any]:
        """
        Crea secuencia para un campo.
        
        Args:
            field_name: Nombre del campo
            template: Template para generar valor (ej: "user_{}")
            
        Returns:
            Función que genera valores secuenciales
        """
        if field_name not in self._sequence_counters:
            self._sequence_counters[field_name] = self.config.sequence_start
        
        def sequence_generator():
            current = self._sequence_counters[field_name]
            self._sequence_counters[field_name] += 1
            
            if template:
                return template.format(current)
            return current
        
        return sequence_generator


class FixtureBuilder(Generic[T]):
    """
    Builder para construcción fluida de fixtures.
    
    Permite construir entidades paso a paso con
    una interfaz fluida.
    """
    
    def __init__(self, factory: BaseFixtureFactory[T]):
        self.factory = factory
        self._data: Dict[str, Any] = {}
    
    def with_field(self, field_name: str, value: Any) -> 'FixtureBuilder[T]':
        """
        Asigna valor a un campo.
        
        Args:
            field_name: Nombre del campo
            value: Valor a asignar
            
        Returns:
            Builder para encadenamiento
        """
        self._data[field_name] = value
        return self
    
    def with_id(self, id_value: Any) -> 'FixtureBuilder[T]':
        """Asigna ID específico."""
        return self.with_field('id', id_value)
    
    def with_random_id(self) -> 'FixtureBuilder[T]':
        """Asigna ID aleatorio."""
        return self.with_field('id', str(uuid.uuid4()))
    
    def with_timestamp(
        self,
        field_name: str = 'created_at',
        timestamp: datetime = None
    ) -> 'FixtureBuilder[T]':
        """Asigna timestamp."""
        timestamp = timestamp or datetime.now(timezone.utc)
        return self.with_field(field_name, timestamp)
    
    def build(self) -> T:
        """Construye la entidad."""
        return self.factory.create(**self._data)
    
    def build_batch(self, count: int) -> List[T]:
        """Construye múltiples entidades."""
        return [
            self.factory.create(**self._data)
            for _ in range(count)
        ]


class TestDataBuilder:
    """
    Builder central para coordinar creación de datos de prueba.
    
    Mantiene factories registrados y permite crear
    escenarios complejos de datos relacionados.
    """
    
    def __init__(self):
        self._factories: Dict[str, BaseFixtureFactory] = {}
        self._scenarios: Dict[str, Callable] = {}
    
    def register_factory(
        self,
        name: str,
        entity_class: Type[T],
        defaults: Dict[str, Any] = None
    ) -> BaseFixtureFactory[T]:
        """
        Registra factory para tipo de entidad.
        
        Args:
            name: Nombre del factory
            entity_class: Clase de entidad
            defaults: Valores por defecto
            
        Returns:
            Factory creado
        """
        factory = BaseFixtureFactory(entity_class, defaults)
        self._factories[name] = factory
        return factory
    
    def get_factory(self, name: str) -> BaseFixtureFactory:
        """Obtiene factory por nombre."""
        if name not in self._factories:
            raise ValueError(f"Factory '{name}' not registered")
        return self._factories[name]
    
    def create(self, factory_name: str, **overrides) -> Any:
        """Crea entidad usando factory registrado."""
        factory = self.get_factory(factory_name)
        return factory.create(**overrides)
    
    def create_batch(self, factory_name: str, count: int, **overrides) -> List[Any]:
        """Crea múltiples entidades."""
        factory = self.get_factory(factory_name)
        return factory.create_batch(count, **overrides)
    
    def builder(self, factory_name: str) -> FixtureBuilder:
        """Obtiene builder para factory."""
        factory = self.get_factory(factory_name)
        return FixtureBuilder(factory)
    
    def register_scenario(self, name: str, builder_func: Callable) -> None:
        """
        Registra escenario de datos complejos.
        
        Args:
            name: Nombre del escenario
            builder_func: Función que construye el escenario
        """
        self._scenarios[name] = builder_func
    
    def build_scenario(self, name: str, **params) -> Dict[str, Any]:
        """
        Construye escenario registrado.
        
        Args:
            name: Nombre del escenario
            **params: Parámetros para el escenario
            
        Returns:
            Diccionario con datos del escenario
        """
        if name not in self._scenarios:
            raise ValueError(f"Scenario '{name}' not registered")
        
        builder_func = self._scenarios[name]
        return builder_func(self, **params)


# Ejemplo de uso y configuración de factories comunes

def create_user_factory() -> BaseFixtureFactory:
    """Factory de ejemplo para entidad User."""
    
    class User:
        def __init__(
            self,
            id: str = None,
            name: str = None,
            email: str = None,
            created_at: datetime = None,
            is_active: bool = True
        ):
            self.id = id
            self.name = name
            self.email = email
            self.created_at = created_at
            self.is_active = is_active
    
    defaults = {
        'name': 'Test User',
        'email': 'test@example.com',
        'is_active': True
    }
    
    return BaseFixtureFactory(User, defaults)


def setup_test_data_builder() -> TestDataBuilder:
    """Configura builder con factories comunes."""
    builder = TestDataBuilder()
    
    # Registrar factories
    builder.register_factory('user', create_user_factory().entity_class, {
        'name': 'Test User',
        'email': 'test@example.com',
        'is_active': True
    })
    
    # Registrar escenarios
    def user_with_posts_scenario(builder: TestDataBuilder, user_count: int = 1):
        """Escenario: usuarios con posts."""
        users = builder.create_batch('user', user_count)
        
        # posts = []
        # for user in users:
        #     user_posts = builder.create_batch('post', 3, user_id=user.id)
        #     posts.extend(user_posts)
        
        return {
            'users': users,
            # 'posts': posts
        }
    
    builder.register_scenario('users_with_posts', user_with_posts_scenario)
    
    return builder