"""
Setup script for Backbone Clean Architecture Framework
"""
from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Backbone - Clean Architecture Framework for Python"

# Read requirements
def read_requirements(filename):
    req_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="backbone",
    version="1.0.0",
    author="FreakJazz",
    author_email="freakjazz@example.com",
    description="Clean Architecture Framework with Event-Driven Microservices for Python",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/FreakJazz/backbone",
    project_urls={
        "Documentation": "https://github.com/FreakJazz/backbone#readme",
        "Bug Reports": "https://github.com/FreakJazz/backbone/issues",
        "Source": "https://github.com/FreakJazz/backbone",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Framework :: AsyncIO",
        "Typing :: Typed",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "typing-extensions>=4.0.0",
        "aiofiles>=25.1.0",
    ],
    extras_require={
        "sqlalchemy": [
            "sqlalchemy>=1.4.0",
            "sqlalchemy[asyncio]>=1.4.0",
        ],
        "mongodb": [
            "motor>=3.0.0",
            "pymongo>=4.0.0",
        ],
        "logging": [
            "loguru>=0.6.0",
        ],
        "testing": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
        "all": [
            # SQLAlchemy
            "sqlalchemy>=1.4.0",
            "sqlalchemy[asyncio]>=1.4.0",
            # MongoDB
            "motor>=3.0.0", 
            "pymongo>=4.0.0",
            # Logging
            "loguru>=0.6.0",
            # Testing
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
        "dev": [
            # All dependencies
            "sqlalchemy>=1.4.0",
            "sqlalchemy[asyncio]>=1.4.0",
            "motor>=3.0.0",
            "pymongo>=4.0.0", 
            "loguru>=0.6.0",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            # Development tools
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "clean-architecture",
        "hexagonal-architecture", 
        "domain-driven-design",
        "repository-pattern",
        "unit-of-work",
        "specification-pattern",
        "framework",
        "async",
        "python",
        "enterprise",
        "scalable",
        "maintainable"
    ],
    entry_points={
        "console_scripts": [
            "backbone-init=backbone.cli:init_project",
        ],
    },
)