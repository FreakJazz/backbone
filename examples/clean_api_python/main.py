"""Clean API Example with Python Backbone Framework"""
from flask import Flask, jsonify
from flask_restx import Api, Resource, fields, Namespace
from datetime import datetime
import sys
import os

# Add backbone to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backbone.infrastructure.logging import LoggerFactory, LogLevel
from examples.clean_api_python.application.use_cases.create_product import CreateProductUseCase
from examples.clean_api_python.application.use_cases.get_products import GetProductsUseCase
from examples.clean_api_python.domain.entities.product import Product
from examples.clean_api_python.infrastructure.repositories.memory_product_repository import MemoryProductRepository
from examples.clean_api_python.interfaces.http.handlers.product_handler import ProductHandler
from examples.clean_api_python.interfaces.http.middleware.logging_middleware import logging_middleware


def create_app():
    """Creates and configures the Flask app"""
    app = Flask(__name__)
    app.config['RESTX_MASK_SWAGGER'] = False
    
    # Initialize Flask-RESTX API
    api = Api(
        app,
        version='1.0',
        title='Product API',
        description='Clean Architecture API Example with Backbone Framework',
        doc='/docs',
        prefix='/api'
    )
    
    print("🚀 Starting Clean API Example - Python")
    print("=" * 40)
    
    # Setup logger
    logger = LoggerFactory.create_logger("product-api")
    logger.info(
        "Initializing application",
        extra_data={"version": "1.0.0", "env": "development"}
    )
    
    # Setup dependencies (Dependency Injection)
    product_repo = MemoryProductRepository()
    
    # Seed data
    seed_data(product_repo, logger)
    
    # Create use cases
    create_product_use_case = CreateProductUseCase(product_repo)
    get_products_use_case = GetProductsUseCase(product_repo)
    
    # Create handlers
    product_handler = ProductHandler(create_product_use_case, get_products_use_case)
    
    # Define models for Swagger documentation
    product_model = api.model('Product', {
        'id': fields.String(required=True, description='Product ID'),
        'name': fields.String(required=True, description='Product name'),
        'description': fields.String(description='Product description'),
        'price': fields.Float(required=True, description='Product price'),
        'category': fields.String(required=True, description='Product category'),
        'stock': fields.Integer(required=True, description='Product stock quantity'),
        'active': fields.Boolean(description='Product active status'),
        'created_at': fields.String(description='Creation timestamp'),
        'updated_at': fields.String(description='Last update timestamp')
    })
    
    create_product_model = api.model('CreateProduct', {
        'name': fields.String(required=True, description='Product name', example='Laptop Dell XPS 15'),
        'description': fields.String(required=True, description='Product description', example='High performance laptop'),
        'price': fields.Float(required=True, description='Product price', example=1500.00),
        'category': fields.String(required=True, description='Product category', example='Electronics'),
        'stock': fields.Integer(required=True, description='Product stock quantity', example=50)
    })
    
    # Create namespace
    ns = api.namespace('products', description='Product operations')
    
    @ns.route('')
    class ProductList(Resource):
        @ns.doc('list_products', 
            params={
                'category': 'Filter by category',
                'min_price': 'Minimum price filter',
                'max_price': 'Maximum price filter',
                'in_stock': 'Filter by stock availability (true/false)',
                'name': 'Search by name pattern',
                'page': 'Page number (default 1)',
                'page_size': 'Page size (default 10)',
                'sort_by': 'Sort field (default created_at)',
                'sort_order': 'Sort order: asc or desc (default desc)'
            }
        )
        @ns.marshal_with(product_model, as_list=True)
        def get(self):
            """Get products with optional filters"""
            return product_handler.get_products()
        
        @ns.doc('create_product')
        @ns.expect(create_product_model)
        @ns.marshal_with(product_model)
        def post(self):
            """Create a new product"""
            return product_handler.create_product()
    
    # Health endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "product-api"
        }), 200
    
    logger.info(
        "Application initialized successfully",
        extra_data={"routes": ["/api/products", "/health", "/docs"]}
    )
    
    return app



def seed_data(repo, logger):
    """Seeds initial data for demo"""
    logger.info("Seeding demo data...")
    
    products = [
        Product(
            id="1",
            name="Laptop Dell XPS 15",
            description="High performance laptop with 16GB RAM",
            price=1500.00,
            category="Electronics",
            stock=50,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Product(
            id="2",
            name="iPhone 14 Pro",
            description="Latest iPhone with advanced camera",
            price=1200.00,
            category="Electronics",
            stock=100,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Product(
            id="3",
            name="Office Chair Ergonomic",
            description="Comfortable ergonomic office chair",
            price=350.00,
            category="Furniture",
            stock=30,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Product(
            id="4",
            name="Standing Desk",
            description="Adjustable height standing desk",
            price=600.00,
            category="Furniture",
            stock=20,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Product(
            id="5",
            name="Wireless Mouse",
            description="Ergonomic wireless mouse",
            price=45.00,
            category="Electronics",
            stock=200,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    for product in products:
        try:
            repo.create(product)
        except Exception as e:
            logger.warning(
                "Failed to seed product",
                extra_data={"product_id": product.id, "error": str(e)}
            )
    
    logger.info(
        "Demo data seeded successfully",
        extra_data={"count": len(products)}
    )


if __name__ == "__main__":
    app = create_app()
    
    print("\n✅ Server running on http://localhost:5000")
    print("\n📝 API Endpoints:")
    print("  POST   http://localhost:5000/api/products")
    print("  GET    http://localhost:5000/api/products")
    print("  GET    http://localhost:5000/health")
    print("\n🔍 Example with filters:")
    print('  curl "http://localhost:5000/api/products?category=Electronics&min_price=500&max_price=2000&page=1&page_size=10"')
    print("\n💡 Press Ctrl+C to stop\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
