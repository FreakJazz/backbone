"""Product HTTP handlers - Interface layer"""
from flask import request, jsonify
from typing import Dict, Any
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backbone.infrastructure.logging import LoggerFactory, LogLevel
from backbone.interfaces.response_builders import ProcessResponseBuilder, QueryResponseBuilder, ErrorResponseBuilder
from examples.clean_api_python.application.use_cases.create_product import (
    CreateProductUseCase,
    CreateProductInput
)
from examples.clean_api_python.application.use_cases.get_products import (
    GetProductsUseCase,
    GetProductsInput
)


class ProductHandler:
    """HTTP handlers for products"""
    
    def __init__(self, create_use_case: CreateProductUseCase, get_use_case: GetProductsUseCase):
        self.create_use_case = create_use_case
        self.get_use_case = get_use_case
        self.logger = LoggerFactory.create_layer_logger(
            "product-api",
            "interfaces",
            "ProductHandler"
        )
    
    def create_product(self):
        """Handles product creation"""
        context = self._get_request_context()
        
        self.logger.log(
            LogLevel.INFO,
            "Handling create product request",
            context=context
        )
        
        # Parse request body
        try:
            data = request.get_json()
            input_data = CreateProductInput(
                name=data.get("name"),
                description=data.get("description"),
                price=float(data.get("price", 0)),
                category=data.get("category"),
                stock=int(data.get("stock", 0))
            )
        except Exception as e:
            self.logger.log(
                LogLevel.ERROR,
                "Invalid JSON payload",
                extra_data={
                    "error": str(e),
                    "error_code": 13001001
                },
                context=context
            )
            response = ErrorResponseBuilder.bad_request(
                "Invalid JSON payload",
                {"error": str(e)}
            )
            return jsonify(response), response["status"]
        
        # Execute use case
        try:
            output = self.create_use_case.execute(input_data, context)
        except Exception as e:
            self.logger.log(
                LogLevel.ERROR,
                "Use case failed",
                extra_data={
                    "error": str(e),
                    "error_code": 13001002
                },
                context=context
            )
            response = ErrorResponseBuilder.internal_server_error(
                "Failed to create product",
                {"error": str(e)}
            )
            return jsonify(response), response["status"]
        
        # Success response
        response = ProcessResponseBuilder.created(
            "Product created successfully",
            {"product": output.product.to_dict()}
        )
        
        self.logger.log(
            LogLevel.INFO,
            "Product created successfully",
            extra_data={"product_id": output.product.id},
            context=context
        )
        
        return jsonify(response), response["status"]
    
    def get_products(self):
        """Handles getting products with filters"""
        context = self._get_request_context()
        
        self.logger.log(
            LogLevel.INFO,
            "Handling get products request",
            context=context
        )
        
        # Parse query parameters
        input_data = self._parse_query_parameters()
        
        self.logger.log(
            LogLevel.DEBUG,
            "Query parameters parsed",
            extra_data={
                "category": input_data.category,
                "min_price": input_data.min_price,
                "max_price": input_data.max_price,
                "page": input_data.page,
                "page_size": input_data.page_size
            },
            context=context
        )
        
        # Execute use case
        try:
            output = self.get_use_case.execute(input_data, context)
        except Exception as e:
            self.logger.log(
                LogLevel.ERROR,
                "Use case failed",
                extra_data={
                    "error": str(e),
                    "error_code": 13001003
                },
                context=context
            )
            response = ErrorResponseBuilder.internal_server_error(
                "Failed to get products",
                {"error": str(e)}
            )
            return jsonify(response), response["status"]
        
        # Success response with pagination
        products_data = [p.to_dict() for p in output.products]
        response = QueryResponseBuilder.success_with_pagination(
            "Products retrieved successfully",
            products_data,
            output.page,
            output.page_size,
            output.total_count
        )
        
        self.logger.log(
            LogLevel.INFO,
            "Products retrieved successfully",
            extra_data={
                "count": len(output.products),
                "total_count": output.total_count,
                "page": output.page
            },
            context=context
        )
        
        return jsonify(response), response["status"]
    
    def _parse_query_parameters(self) -> GetProductsInput:
        """Parses query parameters for filtering"""
        return GetProductsInput(
            category=request.args.get("category"),
            min_price=float(request.args.get("min_price", 0)) or None,
            max_price=float(request.args.get("max_price", 0)) or None,
            in_stock=request.args.get("in_stock") == "true",
            active=request.args.get("active") != "false",
            name_pattern=request.args.get("name"),
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 10)),
            sort_by=request.args.get("sort_by", "created_at"),
            sort_order=request.args.get("sort_order", "desc")
        )
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Gets request context for logging"""
        return {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "user_id": request.headers.get("X-User-ID", "unknown"),
            "method": request.method,
            "path": request.path
        }
