"""
Base Test Case - Framework de testing para arquitectura limpia
"""
import asyncio
import unittest
from typing import TypeVar, Generic, Type, Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock
from ...domain.repositories.base_repository import IRepository, BaseRepository
from ...domain.repositories.unit_of_work import IUnitOfWork, BaseUnitOfWork
from ...domain.specifications.base_specification import Specification
from ...domain.exceptions.domain_exceptions import DomainException
from ...application.exceptions.application_exceptions import ApplicationException
from ...infrastructure.exceptions.infrastructure_exceptions import InfrastructureException
from ..logging.structured_logger import StructuredLogger

T = TypeVar('T')
ID = TypeVar('ID')


class BaseTestCase(unittest.TestCase):
    """
    Caso base para tests unitarios.
    
    Proporciona utilidades comunes para testing de arquitectura limpia:
    - Configuración de mocks para repositorios
    - Helpers para assertions de excepciones
    - Configuración de logging para tests
    """
    
    def setUp(self):
        """Configuración base para cada test."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Mock logger para tests
        self.mock_logger = Mock(spec=StructuredLogger)
        
        # Almacenar mocks creados para cleanup
        self._mocks: List[Mock] = []
    
    def tearDown(self):
        """Limpieza después de cada test."""
        # Limpiar mocks
        for mock in self._mocks:
            mock.reset_mock()
        
        # Cerrar loop
        self.loop.close()
    
    def create_mock_repository(self, entity_class: Type[T]) -> Mock:
        """
        Crea mock de repositorio con métodos async.
        
        Args:
            entity_class: Clase de la entidad
            
        Returns:
            Mock configurado como repositorio
        """
        mock_repo = Mock(spec=IRepository)
        
        # Configurar métodos async
        mock_repo.find_by_id = AsyncMock(return_value=None)
        mock_repo.find_by_specification = AsyncMock(return_value=[])
        mock_repo.find_paginated_by_specification = AsyncMock(return_value=([], 0))
        mock_repo.count_by_specification = AsyncMock(return_value=0)
        mock_repo.save = AsyncMock()
        mock_repo.delete = AsyncMock()
        mock_repo.delete_by_specification = AsyncMock(return_value=0)
        
        self._mocks.append(mock_repo)
        return mock_repo
    
    def create_mock_unit_of_work(self) -> Mock:
        """
        Crea mock de Unit of Work.
        
        Returns:
            Mock configurado como UoW
        """
        mock_uow = Mock(spec=IUnitOfWork)
        
        # Configurar métodos async y context manager
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.commit = AsyncMock()
        mock_uow.rollback = AsyncMock()
        mock_uow.register_new = Mock()
        mock_uow.register_dirty = Mock()
        mock_uow.register_removed = Mock()
        
        self._mocks.append(mock_uow)
        return mock_uow
    
    # Helpers para assertions de excepciones por capa
    
    def assertRaisesDomainException(
        self, 
        expected_error_code: str = None,
        msg: str = None
    ):
        """
        Context manager para validar DomainException.
        
        Args:
            expected_error_code: Código de error esperado (11xxxxxx)
            msg: Mensaje personalizado
        """
        return self._assert_raises_kernel_exception(
            DomainException, 
            expected_error_code,
            msg
        )
    
    def assertRaisesApplicationException(
        self, 
        expected_error_code: str = None,
        msg: str = None
    ):
        """Context manager para validar ApplicationException."""
        return self._assert_raises_kernel_exception(
            ApplicationException,
            expected_error_code, 
            msg
        )
    
    def assertRaisesInfrastructureException(
        self, 
        expected_error_code: str = None,
        msg: str = None
    ):
        """Context manager para validar InfrastructureException."""
        return self._assert_raises_kernel_exception(
            InfrastructureException,
            expected_error_code,
            msg
        )
    
    def _assert_raises_kernel_exception(
        self,
        exception_class: Type,
        expected_error_code: str = None,
        msg: str = None
    ):
        """Helper interno para validar excepciones del kernel."""
        class ExceptionAssertion:
            def __init__(self, test_case, exc_class, expected_code, message):
                self.test_case = test_case
                self.exc_class = exc_class
                self.expected_code = expected_code
                self.message = message
                self.exception = None
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_value, traceback):
                if exc_type is None:
                    raise AssertionError(
                        f"Expected {self.exc_class.__name__} to be raised"
                    )
                
                if not issubclass(exc_type, self.exc_class):
                    return False
                
                self.exception = exc_value
                
                # Validar código de error si se especifica
                if self.expected_code:
                    actual_code = getattr(exc_value, 'error_code', None)
                    if actual_code != self.expected_code:
                        raise AssertionError(
                            f"Expected error code {self.expected_code}, "
                            f"got {actual_code}"
                        )
                
                return True
        
        return ExceptionAssertion(self, exception_class, expected_error_code, msg)
    
    # Helpers para validación de datos
    
    def assertValidPaginationResult(
        self,
        result: tuple,
        expected_items_count: int = None,
        expected_total: int = None
    ):
        """
        Valida resultado de paginación.
        
        Args:
            result: Tupla (items, total)
            expected_items_count: Cantidad esperada de items
            expected_total: Total esperado
        """
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        
        items, total = result
        
        self.assertIsInstance(items, list)
        self.assertIsInstance(total, int)
        self.assertGreaterEqual(total, 0)
        
        if expected_items_count is not None:
            self.assertEqual(len(items), expected_items_count)
        
        if expected_total is not None:
            self.assertEqual(total, expected_total)
    
    def assertValidErrorContract(
        self,
        error_contract: Dict[str, Any],
        expected_error_code: str = None
    ):
        """
        Valida contrato de error.
        
        Args:
            error_contract: Diccionario con contrato de error
            expected_error_code: Código esperado
        """
        required_fields = ["error_code", "message", "rid", "timestamp", "layer"]
        
        for field in required_fields:
            self.assertIn(field, error_contract)
            self.assertIsNotNone(error_contract[field])
        
        if expected_error_code:
            self.assertEqual(error_contract["error_code"], expected_error_code)
    
    # Helpers para async testing
    
    def run_async(self, coro):
        """
        Ejecuta corrutina en el loop del test.
        
        Args:
            coro: Corrutina a ejecutar
            
        Returns:
            Resultado de la corrutina
        """
        return self.loop.run_until_complete(coro)


class BaseIntegrationTestCase(BaseTestCase):
    """
    Caso base para tests de integración.
    
    Proporciona utilidades para tests que requieren
    infraestructura real (BD, servicios externos, etc).
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuración una sola vez para la clase."""
        super().setUpClass() if hasattr(super(), 'setUpClass') else None
        
        # Configurar recursos compartidos (BD test, etc)
        cls._setup_test_infrastructure()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza una sola vez para la clase."""
        cls._cleanup_test_infrastructure()
        super().tearDownClass() if hasattr(super(), 'tearDownClass') else None
    
    @classmethod
    def _setup_test_infrastructure(cls):
        """Override para configurar infraestructura de test."""
        pass
    
    @classmethod
    def _cleanup_test_infrastructure(cls):
        """Override para limpiar infraestructura de test."""
        pass
    
    def setUp(self):
        """Configuración para cada test de integración."""
        super().setUp()
        
        # Crear transacción para rollback después del test
        self._setup_test_transaction()
    
    def tearDown(self):
        """Limpieza después de cada test de integración."""
        self._rollback_test_transaction()
        super().tearDown()
    
    def _setup_test_transaction(self):
        """Override para configurar transacción de test."""
        pass
    
    def _rollback_test_transaction(self):
        """Override para hacer rollback de transacción."""
        pass


class BaseAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    """
    Caso base para tests async usando unittest nativo.
    
    Alternativa moderna usando IsolatedAsyncioTestCase
    de Python 3.8+.
    """
    
    async def asyncSetUp(self):
        """Configuración async para cada test."""
        self.mock_logger = Mock(spec=StructuredLogger)
        self._mocks: List[Mock] = []
    
    async def asyncTearDown(self):
        """Limpieza async después de cada test."""
        for mock in self._mocks:
            mock.reset_mock()
    
    def create_mock_repository(self, entity_class: Type[T]) -> Mock:
        """Crea mock de repositorio async."""
        mock_repo = Mock(spec=IRepository)
        
        # Configurar métodos async
        mock_repo.find_by_id = AsyncMock(return_value=None)
        mock_repo.find_by_specification = AsyncMock(return_value=[])
        mock_repo.find_paginated_by_specification = AsyncMock(return_value=([], 0))
        mock_repo.count_by_specification = AsyncMock(return_value=0)
        mock_repo.save = AsyncMock()
        mock_repo.delete = AsyncMock()
        mock_repo.delete_by_specification = AsyncMock(return_value=0)
        
        self._mocks.append(mock_repo)
        return mock_repo
    
    def create_mock_unit_of_work(self) -> Mock:
        """Crea mock de Unit of Work async."""
        mock_uow = Mock(spec=IUnitOfWork)
        
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.commit = AsyncMock()
        mock_uow.rollback = AsyncMock()
        mock_uow.register_new = Mock()
        mock_uow.register_dirty = Mock()
        mock_uow.register_removed = Mock()
        
        self._mocks.append(mock_uow)
        return mock_uow