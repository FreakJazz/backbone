"""
Filter Parser - Parser para filtros dinámicos desde query parameters
"""
from typing import List, Dict, Any, Optional, Union
from .filter_specification import SpecificationFactory, FilterSpecification
from .base_specification import Specification, T
from ..exceptions.domain_exceptions import InvalidValueObjectException


class FilterParser:
    """
    Parser para convertir filtros de query parameters a especificaciones.
    
    Soporta dos formatos:
    1. Lista de strings: ["field,operator,value,logical_connector"]
    2. Dictionary de query params: {"field__operator": "value", "field": "value"}
    
    Ejemplos:
    - Lista: ["age,gte,18,and", "name,like,juan"]
    - Dict: {"age__gte": "18", "name__like": "juan"}
    - Dict simple: {"name": "Alice", "age__gt": "25"}
    """
    
    def __init__(self):
        self.supported_operators = SpecificationFactory.supported_operators()
        self.supported_connectors = ["and", "or"]
        # Map Django-style operators to internal operators
        self.operator_mapping = {
            "gt": "gt",
            "gte": "gte", 
            "lt": "lt",
            "lte": "lte",
            "eq": "eq",
            "ne": "ne",
            "like": "like",
            "ilike": "ilike",
            "in": "in",
            "between": "between",
            "isnull": "isnull",
            "isnotnull": "isnotnull"
        }
    
    def parse_filters(self, filters: Union[List[str], Dict[str, Any]]) -> Optional[Specification[T]]:
        """
        Convierte filtros a especificación compuesta.
        
        Args:
            filters: Lista de strings o diccionario de query params
            
        Returns:
            Especificación compuesta o None si no hay filtros
            
        Examples:
            # Formato lista
            filters = ["age,gte,18,and", "name,like,juan"]
            
            # Formato diccionario 
            filters = {"age__gte": "18", "name__like": "juan"}
            filters = {"name": "Alice", "age__gt": "25"}
        """
        if not filters:
            return None
        
        # Handle dictionary format (query parameters)
        if isinstance(filters, dict):
            return self._parse_dict_filters(filters)
        
        # Handle list format (comma-separated strings)
        return self._parse_list_filters(filters)
    
    def _parse_dict_filters(self, filters_dict: Dict[str, Any]) -> Optional[Specification[T]]:
        """
        Parse dictionary-style filters (query parameters).
        
        Supports:
        - Simple equality: {"name": "Alice"} -> name = Alice
        - Operator syntax: {"age__gte": "18"} -> age >= 18
        - Multiple filters combined with AND by default
        """
        if not filters_dict:
            return None
            
        specifications = []
        
        for field_expr, value in filters_dict.items():
            # Parse field and operator
            if "__" in field_expr:
                field, operator = field_expr.split("__", 1)
                operator = operator.lower()
            else:
                field = field_expr
                operator = "eq"  # Default to equality
            
            # Map operator if needed
            if operator in self.operator_mapping:
                operator = self.operator_mapping[operator]
            
            # Validate operator
            if operator not in self.supported_operators:
                raise InvalidValueObjectException(
                    message=f"Operador no soportado: '{operator}'. Operadores disponibles: {self.supported_operators}",
                    value_object_type="FilterOperator",
                    invalid_value=operator,
                    code=11003008
                )
            
            # Convert value to appropriate type
            parsed_value = self._parse_value(value, operator)
            
            # Create specification
            spec = SpecificationFactory.create(field, operator, parsed_value)
            specifications.append(spec)
        
        # Combine all specifications with AND
        if len(specifications) == 1:
            return specifications[0]
        
        result = specifications[0]
        for spec in specifications[1:]:
            result = result.and_(spec)
        
        return result
    
    def _parse_list_filters(self, filters: List[str]) -> Optional[Specification[T]]:
        """
        Parse list-style filters (comma-separated strings).
        
        Args:
            filters: Lista de filtros en formato "field,operator,value,connector"
            
        Returns:
            Especificación compuesta o None si no hay filtros
        """
        if not filters:
            return None
            
        specifications = []
        connectors = []
        
        for filter_str in filters:
            spec, connector = self._parse_single_filter(filter_str)
            specifications.append(spec)
            if connector:
                connectors.append(connector)
        
        # Si solo hay una especificación, la retornamos directamente
        if len(specifications) == 1:
            return specifications[0]
        
        # Combinar especificaciones con conectores
        return self._combine_specifications(specifications, connectors)
    
    def _parse_single_filter(self, filter_str: str) -> tuple[FilterSpecification, Optional[str]]:
        """
        Parsea un filtro individual.
        
        Args:
            filter_str: String con formato "field,operator,value,connector"
            
        Returns:
            Tuple con (especificación, conector)
        """
        parts = filter_str.split(",", 3)  # Máximo 4 partes
        
        if len(parts) < 3:
            raise InvalidValueObjectException(
                message=f"Filtro inválido: '{filter_str}'. Formato esperado: 'field,operator,value[,connector]'",
                value_object_type="Filter",
                invalid_value=filter_str,
                code=11003007
            )
        
        field = parts[0].strip()
        operator = parts[1].strip().lower()
        value_str = parts[2].strip()
        connector = parts[3].strip().lower() if len(parts) > 3 else None
        
        # Validar operador
        if operator not in self.supported_operators:
            raise InvalidValueObjectException(
                message=f"Operador no soportado: '{operator}'. Operadores disponibles: {self.supported_operators}",
                value_object_type="FilterOperator",
                invalid_value=operator,
                code=11003008
            )
        
        # Validar conector
        if connector and connector not in self.supported_connectors:
            raise InvalidValueObjectException(
                message=f"Conector lógico no soportado: '{connector}'. Conectores disponibles: {self.supported_connectors}",
                value_object_type="LogicalConnector",
                invalid_value=connector,
                code=11003009
            )
        
        # Convertir valor
        parsed_value = self._parse_value(value_str, operator)
        
        # Crear especificación
        specification = SpecificationFactory.create(field, operator, parsed_value)
        
        return specification, connector
    
    def _parse_value(self, value_str: str, operator: str) -> Any:
        """
        Convierte string de valor al tipo apropiado.
        
        Args:
            value_str: String con el valor
            operator: Operador para determinar tipo de conversión
            
        Returns:
            Valor convertido al tipo apropiado
        """
        if operator in ("is_null", "is_not_null"):
            return None
        
        if operator == "in":
            # Para operador IN, esperamos valores separados por |
            return [self._convert_single_value(v.strip()) for v in value_str.split("|")]
        
        if operator == "between":
            # Para operador BETWEEN, esperamos dos valores separados por |
            values = value_str.split("|")
            if len(values) != 2:
                raise InvalidValueObjectException(
                    message=f"Operador BETWEEN requiere exactamente 2 valores separados por '|': '{value_str}'",
                    value_object_type="BetweenValue",
                    invalid_value=value_str,
                    code=11003010
                )
            return [self._convert_single_value(v.strip()) for v in values]
        
        return self._convert_single_value(value_str)
    
    def _convert_single_value(self, value_str: str) -> Union[str, int, float, bool, None]:
        """
        Convierte un valor string al tipo apropiado.
        
        Args:
            value_str: String a convertir
            
        Returns:
            Valor convertido (int, float, bool, None o str)
        """
        # None/null
        if value_str.lower() in ("null", "none", ""):
            return None
        
        # Boolean
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"
        
        # Integer
        if value_str.isdigit() or (value_str.startswith("-") and value_str[1:].isdigit()):
            return int(value_str)
        
        # Float
        try:
            if "." in value_str:
                return float(value_str)
        except ValueError:
            pass
        
        # String por defecto
        return value_str
    
    def _combine_specifications(
        self, 
        specifications: List[FilterSpecification], 
        connectors: List[str]
    ) -> Specification[T]:
        """
        Combina múltiples especificaciones con conectores lógicos.
        
        Args:
            specifications: Lista de especificaciones
            connectors: Lista de conectores lógicos
            
        Returns:
            Especificación compuesta
        """
        if len(specifications) == 0:
            return None
        
        if len(specifications) == 1:
            return specifications[0]
        
        # Empezar con la primera especificación
        result = specifications[0]
        
        # Combinar con el resto usando conectores
        for i in range(1, len(specifications)):
            connector = connectors[i-1] if i-1 < len(connectors) else "and"
            
            if connector == "and":
                result = result.and_spec(specifications[i])
            elif connector == "or":
                result = result.or_spec(specifications[i])
        
        return result
    
    def validate_filter_field(self, field: str, allowed_fields: List[str]) -> bool:
        """
        Valida que el campo esté en la lista de campos permitidos.
        
        Args:
            field: Campo a validar
            allowed_fields: Lista de campos permitidos
            
        Returns:
            True si el campo es válido
            
        Raises:
            InvalidValueObjectException: Si el campo no está permitido
        """
        if field not in allowed_fields:
            raise InvalidValueObjectException(
                message=f"Campo de filtro no permitido: '{field}'. Campos permitidos: {allowed_fields}",
                value_object_type="FilterField",
                invalid_value=field,
                code=11003011
            )
        
        return True