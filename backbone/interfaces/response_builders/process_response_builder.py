"""
Process Response Builder - Constructor de respuestas de procesos
"""
from typing import Dict, Any, Optional, Union


class ProcessResponseBuilder:
    """
    Constructor para respuestas de procesos (WRITE/CREATE/UPDATE).
    
    Contrato de éxito:
    {
        "meta": {
            "status": 201,
            "message": "Usuario creado correctamente"
        },
        "body": {
            "id": "uuid"
        }
    }
    
    Sin dependencia de FastAPI - retorna dict puro.
    """
    
    @staticmethod
    def success(
        message: str,
        data: Optional[Union[Dict[str, Any], str, int]] = None,
        status: int = 201
    ) -> Dict[str, Any]:
        """
        Construye una respuesta exitosa de proceso.
        
        Args:
            message: Mensaje descriptivo del éxito
            data: Datos del proceso (típicamente un ID)
            status: Código de estado (201 para creación, 200 para actualización)
            
        Returns:
            Dict con formato estándar de respuesta de proceso
            
        Examples:
            # Crear usuario
            ProcessResponseBuilder.success(
                message="Usuario creado correctamente",
                data={"id": "uuid-123"},
                status=201
            )
            
            # Actualizar usuario  
            ProcessResponseBuilder.success(
                message="Usuario actualizado correctamente",
                data={"id": "uuid-123"},
                status=200
            )
            
            # Solo confirmación
            ProcessResponseBuilder.success(
                message="Operación completada",
                status=200
            )
        """
        from datetime import datetime
        from uuid import uuid4
        
        response = {
            "status": "success",
            "status_code": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4()),
            "data": data
        }
        
        return response
    
    @staticmethod
    def created(message: str, entity_id: str) -> Dict[str, Any]:
        """
        Shortcut para respuesta de creación.
        
        Args:
            message: Mensaje de éxito
            entity_id: ID de la entidad creada
            
        Returns:
            Dict con respuesta estándar de creación
        """
        return ProcessResponseBuilder.success(
            message=message,
            data={"id": entity_id},
            status=201
        )
    
    @staticmethod
    def updated(message: str, data: Optional[Dict[str, Any]] = None, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Shortcut para respuesta de actualización.
        
        Args:
            message: Mensaje de éxito
            data: Datos actualizados de la entidad (opcional)
            entity_id: ID de la entidad actualizada (opcional, para compatibilidad)
            
        Returns:
            Dict con respuesta estándar de actualización
        """
        if data is not None:
            response_data = data
        elif entity_id is not None:
            response_data = {"id": entity_id}
        else:
            response_data = None
            
        return ProcessResponseBuilder.success(
            message=message,
            data=response_data,
            status=200
        )
    
    @staticmethod
    def deleted(message: str = "Recurso eliminado correctamente", resource_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Shortcut para respuesta de eliminación.
        
        Args:
            message: Mensaje de éxito
            resource_id: ID del recurso eliminado (opcional)
            
        Returns:
            Dict con respuesta estándar de eliminación
        """
        data = {"resource_id": resource_id} if resource_id else None
        return ProcessResponseBuilder.success(
            message=message,
            data=data,
            status=200
        )
    
    @staticmethod
    def completed(message: str) -> Dict[str, Any]:
        """
        Shortcut para operaciones completadas sin datos específicos.
        
        Args:
            message: Mensaje de éxito
            
        Returns:
            Dict con respuesta estándar de operación completada
        """
        return ProcessResponseBuilder.success(
            message=message,
            status=200
        )