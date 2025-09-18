# Wells Fargo AuthX Flask Application

A production-ready Flask application for Wells Fargo AuthX integration using Apigee authentication with **dependency injection** and **improved architecture**.

## 🚀 **Key Improvements (Senior Python Developer Review)**

### ✅ **Fixed Critical Issues**
- **Python 3.9+ Compatibility**: Fixed tuple syntax for older Python versions
- **AsyncIO Management**: Replaced dangerous event loop creation with proper async handling
- **Security Headers**: Removed deprecated X-XSS-Protection, added modern CSP and Permissions Policy
- **Input Validation**: Added comprehensive parameter validation and sanitization
- **Error Handling**: Proper import error handling and graceful degradation

### 🏗️ **Architecture Improvements**
- **Dependency Injection**: Full DI container for better testability and maintainability
- **Protocol-based Design**: Type-safe interfaces using Python protocols
- **Separation of Concerns**: Clean separation between authentication, configuration, and routing
- **Circular Import Prevention**: Restructured imports to avoid circular dependencies

## Features

- **Apigee Authentication**: JWT token validation using Wells Fargo AuthX Apigee
- **Flask Integration**: Native Flask decorators and Blueprints
- **Scope-based Authorization**: Fine-grained access control
- **Object-Level Access Control**: Resource-specific permissions (accounts, transactions, customers, etc.)
- **Functional Access Control**: Feature-based permissions (user management, financial reporting, etc.)
- **Role-based Authorization**: Predefined role permissions (admin, manager, teller, etc.)
- **Ownership-based Access**: Automatic access to user-owned resources
- **Production Ready**: Modern security headers, comprehensive error handling, and structured logging
- **Dependency Injection**: Testable architecture with proper DI container
- **Input Validation**: Comprehensive parameter validation and sanitization
- **Standalone**: Can run independently without the main COP Guard application

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the template and set your environment variables:

```bash
cp config.env.template .env
```

Edit `.env` with your configuration:

```env
WELLS_AUTH_ENVIRONMENT=dev
WELLS_AUTH_APIGEE_JWKS_URL=https://your-jwks-url
WELLS_AUTH_APIGEE_CLIENT_ID=your-client-id
BEHIND_PROXY=false
```

### 3. Run the Application

```bash
python main.py
```

Or using the run script:

```bash
python run.py
```

The application will start on `http://localhost:8000`

## API Endpoints

### Authentication Endpoints

- `POST /api/v1/wells-auth/validate` - Validate JWT token
- `POST /api/v1/wells-auth/validate/apigee` - Validate JWT token (Apigee specific)
- `POST /api/v1/wells-auth/validate-token` - Unified validation endpoint with format options

### Wells Fargo AuthX Endpoints

- `POST /api/v1/wells-auth/validate` - Validate JWT token
- `GET /api/v1/wells-auth/info` - Get AuthX configuration info
- `GET /api/v1/wells-auth/health` - Health check for AuthX integration

### Business Application Endpoints

- `GET /adcs-health/` - Application health check (public)
- `GET /apigee_proxy_update/<issue_key>` - Apigee proxy update (requires apigee_management permission)
- `GET /check_ticket/<issue_key>` - Check JIRA ticket (requires jira_access permission)
- `POST /jira_ticket` - Handle JIRA ticket (requires jira_management permission + write scope)
- `GET /get_tickets_by_label/<label>` - Get tickets by label (requires jira_query permission)
- `GET /ticket_current_status/<ticket_id>` - Process ticket status (requires jira_status permission)

### Security Information Endpoints

- `GET /user/permissions` - Get user permissions
- `POST /security/test-permission` - Test specific permission
- `GET /config` - Configuration info (non-sensitive)

## Usage Examples

### Basic Token Validation

```bash
curl -X POST http://localhost:8000/api/v1/wells-auth/validate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Protected Endpoint Access

```bash
curl -X GET http://localhost:8000/api/v1/wells-auth/protected \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Unified Validation with Format

```bash
curl -X POST "http://localhost:8000/api/v1/wells-auth/validate-token?format=minimal" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Flask Decorators

### Authentication Decorator

```python
from security import get_wells_authenticated_user

@app.route("/protected")
@get_wells_authenticated_user
def protected_route():
    user = g.current_user
    return {"user_id": user.get('sub')}
```

### Scope-based Authorization

```python
from security import get_wells_authenticated_user, require_wells_scope

@app.route("/admin")
@get_wells_authenticated_user
@require_wells_scope("admin")
def admin_route():
    return {"message": "Admin access granted"}
```

### Helper Functions

```python
from security import get_wells_client_id, get_wells_user_id, get_wells_user_scopes

# Get client ID
client_id = get_wells_client_id()

# Get user ID
user_id = get_wells_user_id()

# Get user scopes
scopes = get_wells_user_scopes()
```

## Access Control

### Object-Level Access Control

```python
from security import require_object_permission, ResourceType, AccessLevel

@app.route("/accounts/<account_id>")
@get_wells_authenticated_user
@require_object_permission(ResourceType.ACCOUNT, lambda: request.view_args['account_id'], AccessLevel.READ)
def get_account(account_id):
    return {"account_id": account_id}
```

### Functional Access Control

```python
from security import require_functional_access

@app.route("/admin/users")
@get_wells_authenticated_user
@require_functional_access("user_management", ["admin", "manager"])
def manage_users():
    return {"message": "User management access granted"}
```

### Helper Decorators

```python
from security import require_account_access, require_transaction_access

@app.route("/accounts/<account_id>")
@get_wells_authenticated_user
@require_account_access(AccessLevel.READ)
def get_account(account_id):
    return {"account_id": account_id}

@app.route("/transactions/<transaction_id>")
@get_wells_authenticated_user
@require_transaction_access(AccessLevel.WRITE)
def update_transaction(transaction_id):
    return {"transaction_id": transaction_id}
```

### Combined Access Control

```python
@app.route("/accounts/<account_id>/transactions")
@get_wells_authenticated_user
@require_account_access(AccessLevel.READ)
@require_functional_access("transaction_viewing", ["admin", "manager", "teller"])
def get_account_transactions(account_id):
    return {"account_id": account_id, "transactions": []}
```

## Dependency Injection

### Using the DI Container

```python
from security import container, WellsAuthenticator
from config import WellsAuthConfig

# Configure dependencies
config = WellsAuthConfig(environment="test")
authenticator = WellsAuthenticator(config)

# Set in container
container.set_config(config)
container.set_authenticator(authenticator)

# Use in your code
authenticator = container.get_authenticator()
config = container.get_config()
```

### Testing with Dependency Injection

```python
import pytest
from security import DependencyContainer
from unittest.mock import Mock

def test_with_mock_authenticator():
    # Create test container
    test_container = DependencyContainer()
    
    # Create mock authenticator
    mock_auth = Mock()
    mock_auth.authenticate_token.return_value = ({"sub": "test"}, None)
    
    # Set mock in container
    test_container.set_authenticator(mock_auth)
    
    # Test your code
    authenticator = test_container.get_authenticator()
    claims, error = await authenticator.authenticate_token("test_token")
    
    assert claims["sub"] == "test"
    assert error is None
```

## Configuration

The application uses Pydantic for configuration management with environment variable support:

```python
class WellsAuthConfig(BaseSettings):
    apigee_jwks_url: Optional[str] = None
    apigee_client_id: str = "EBSSH"
    environment: str = "dev"  # dev, sit, prod
    auto_refresh: bool = True
    validate_claims: bool = True
    validate_certificate: bool = True
```

## Error Handling

The application provides consistent error responses:

```json
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Authorization header required"
}
```

## Security Features

- **Modern Security Headers**: 
  - Content Security Policy (CSP)
  - Permissions Policy (formerly Feature Policy)
  - X-Content-Type-Options, X-Frame-Options
  - Strict-Transport-Security (configurable for proxy setups)
- **Input Validation**: Comprehensive parameter validation with regex patterns
- **CORS Support**: Configurable cross-origin resource sharing
- **Correlation IDs**: Request tracking for debugging
- **Server Information Hiding**: Removes server headers for security

## Development

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test modules
python -m pytest tests/ -v

# Run basic tests only
python tests/test_app.py

# Run dependency injection tests
python tests/test_dependency_injection.py

# Run access control tests
python tests/test_access_control.py

# Run security routes tests
python tests/test_security_routes.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Production Deployment

### Environment Variables

Set these environment variables for production:

```env
WELLS_AUTH_ENVIRONMENT=prod
WELLS_AUTH_APIGEE_JWKS_URL=https://prod-jwks-url
WELLS_AUTH_APIGEE_CLIENT_ID=prod-client-id
HOST=0.0.0.0
PORT=8000
BEHIND_PROXY=true
LOG_LEVEL=info
```

### WSGI Server

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'ebssh_python_auth'**
   - Install the Wells Fargo AuthX package if you have access
   - Or use the mock authenticator for testing

2. **Configuration not found**
   - Ensure `.env` file exists and is properly configured
   - Check environment variable names and values

3. **Authentication failures**
   - Verify JWT token format and validity
   - Check JWKS URL accessibility
   - Ensure client ID matches configuration

4. **AsyncIO RuntimeError**
   - The new implementation handles event loops properly
   - If you encounter issues, check your Python version (3.9+)

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=debug
python main.py
```

## Project Structure

```
wells_authx/
├── 📁 security/                    # Security-related modules
│   ├── __init__.py                 # Security module exports
│   ├── container.py                # Dependency injection container
│   ├── deps.py                     # Flask decorators and authentication
│   ├── wells_authenticator.py      # Wells Fargo authenticator wrapper
│   └── access_control.py           # Object-level and functional access control
├── 📁 tests/                       # Test files and examples
│   ├── __init__.py                 # Test module
│   ├── test_app.py                 # Basic application tests
│   ├── test_dependency_injection.py # DI container tests
│   ├── test_access_control.py      # Access control tests
│   ├── test_security_routes.py     # Security routes tests
│   └── example_usage.py            # Usage examples
├── __init__.py                     # Main module exports
├── config.py                       # Configuration management
├── main.py                         # Flask application entry point
├── routes.py                       # Main application routes with security
├── run.py                          # Application runner script
├── run_tests.py                    # Test runner script
├── requirements.txt                # Python dependencies
├── config.env.template             # Environment configuration template
├── README.md                       # Project documentation
├── PROJECT_STRUCTURE.md            # Detailed structure documentation
├── ACCESS_CONTROL_GUIDE.md         # Access control documentation
└── SECURITY_IMPLEMENTATION.md      # Security implementation guide
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask App     │    │   DI Container   │    │  Authenticator  │
│   (main.py)     │◄──►│  (security/)     │◄──►│ (security/)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Routes        │    │   Configuration  │    │   PyAuthenticator│
│  (routes.py)    │    │   (config.py)    │    │   (external)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## License

This application is part of the COP Guard project and follows the same licensing terms.