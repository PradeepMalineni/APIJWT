# Wells Fargo AuthX Project Structure

## 📁 **Project Organization**

```
wells_authx/
├── 📁 security/                    # Security-related modules
│   ├── __init__.py                 # Security module exports
│   ├── container.py                # Dependency injection container
│   ├── deps.py                     # Flask decorators and authentication
│   └── wells_authenticator.py      # Wells Fargo authenticator wrapper
├── 📁 tests/                       # Test files and examples
│   ├── __init__.py                 # Test module
│   ├── test_app.py                 # Basic application tests
│   ├── test_dependency_injection.py # DI container tests
│   └── example_usage.py            # Usage examples
├── 📁 __pycache__/                 # Python cache files
├── __init__.py                     # Main module exports
├── config.py                       # Configuration management
├── main.py                         # Flask application entry point
├── routes.py                       # API routes and endpoints
├── run.py                          # Application runner script
├── run_tests.py                    # Test runner script
├── requirements.txt                # Python dependencies
├── config.env.template             # Environment configuration template
├── README.md                       # Project documentation
└── PROJECT_STRUCTURE.md            # This file
```

## 🎯 **Entry Points**

### **Main Application**
- **`main.py`** - Primary Flask application entry point
- **`run.py`** - Simple application runner script

### **Testing**
- **`run_tests.py`** - Comprehensive test runner
- **`tests/test_app.py`** - Basic application tests
- **`tests/test_dependency_injection.py`** - DI container tests

## 🔒 **Security Module** (`security/`)

### **Purpose**
Contains all security-related functionality including authentication, authorization, and dependency injection.

### **Files**
- **`container.py`** - Dependency injection container with protocol-based design
- **`deps.py`** - Flask decorators for authentication and authorization
- **`wells_authenticator.py`** - Wells Fargo authenticator wrapper

### **Key Exports**
```python
from security import (
    DependencyContainer,    # DI container class
    container,              # Global DI container instance
    get_wells_authenticated_user,  # Authentication decorator
    require_wells_scope,    # Authorization decorator
    WellsAuthenticator      # Authenticator class
)
```

## 🧪 **Tests Module** (`tests/`)

### **Purpose**
Contains all test files, examples, and testing utilities.

### **Files**
- **`test_app.py`** - Basic application functionality tests
- **`test_dependency_injection.py`** - Comprehensive DI container tests
- **`example_usage.py`** - Usage examples and patterns

## ⚙️ **Configuration**

### **`config.py`**
- Pydantic-based configuration management
- Environment variable support
- Validation and type checking

### **`config.env.template`**
- Template for environment configuration
- Copy to `.env` and customize for your environment

## 🚀 **Usage**

### **Running the Application**
```bash
# Direct execution
python main.py

# Using runner script
python run.py

# With custom configuration
WELLS_AUTH_ENVIRONMENT=prod python main.py
```

### **Running Tests**
```bash
# Run all tests
python run_tests.py

# Run specific test modules
python -m pytest tests/ -v

# Run basic tests only
python tests/test_app.py
```

### **Importing in Your Code**
```python
# Import from main module
from wells_authx import WellsAuthenticator, WellsAuthConfig, container

# Import from security module
from wells_authx.security import get_wells_authenticated_user, require_wells_scope

# Import configuration
from wells_authx.config import WellsAuthConfig
```

## 🔧 **Development**

### **Adding New Security Features**
1. Add new files to `security/` directory
2. Update `security/__init__.py` to export new functionality
3. Add tests to `tests/` directory
4. Update documentation

### **Adding New Tests**
1. Add test files to `tests/` directory
2. Follow naming convention: `test_*.py`
3. Update `run_tests.py` if needed
4. Ensure tests can be run independently

### **Configuration Changes**
1. Update `config.py` for new configuration options
2. Update `config.env.template` for new environment variables
3. Update documentation and examples

## 📋 **Best Practices**

### **File Organization**
- Keep security-related code in `security/` directory
- Keep all tests in `tests/` directory
- Keep only entry points in root directory
- Use descriptive file names

### **Import Structure**
- Use relative imports within modules
- Export public APIs through `__init__.py` files
- Avoid circular imports
- Use dependency injection for testability

### **Testing**
- Write tests for all public APIs
- Use dependency injection for mocking
- Test both success and failure scenarios
- Keep tests independent and isolated

## 🎯 **Benefits of This Structure**

1. **Clear Separation**: Security, tests, and main code are clearly separated
2. **Easy Testing**: All tests are in one place with proper organization
3. **Maintainable**: Easy to find and modify specific functionality
4. **Scalable**: Easy to add new features without cluttering the root
5. **Professional**: Follows Python packaging best practices
6. **Testable**: Dependency injection makes testing straightforward
