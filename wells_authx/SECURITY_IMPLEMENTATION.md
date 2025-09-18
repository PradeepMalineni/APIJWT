# Wells Fargo AuthX - Security Implementation Guide

## 🎯 **Overview**

This document describes the comprehensive security implementation for the Wells Fargo AuthX Flask application, including all the security features that have been integrated into your actual routes.

## 🔐 **Security Features Implemented**

### **1. Authentication**
- **JWT Token Validation**: All protected endpoints require valid Wells Fargo AuthX JWT tokens
- **Bearer Token Support**: Standard `Authorization: Bearer <token>` header format
- **Token Claims Extraction**: Full JWT claims available in route handlers

### **2. Authorization**
- **Scope-based Access Control**: Traditional OAuth2 scope checking
- **Functional Access Control**: Feature-based permissions (jira_access, apigee_management, etc.)
- **Role-based Access Control**: Predefined role permissions (admin, manager, developer, etc.)

### **3. Security Headers**
- **Modern Security Headers**: CSP, Permissions Policy, X-Frame-Options, etc.
- **Correlation ID Tracking**: Request tracking for debugging and auditing
- **Server Information Hiding**: Removes server headers for security

### **4. Input Validation**
- **Parameter Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Standardized error responses with proper HTTP status codes

## 📊 **Route Security Implementation**

### **Health Check Endpoint**
```python
@app.route("/adcs-health/", methods=["GET"])
def health_check():
    # No authentication required - public endpoint
```

**Security Level**: Public (No authentication required)

### **Apigee Proxy Update Endpoint**
```python
@app.route("/apigee_proxy_update/<issue_key>", methods=["GET"])
@get_wells_authenticated_user
@require_functional_access("apigee_management", ["admin", "manager", "developer"])
def apigee_proxy_update_route(issue_key: str):
```

**Security Features**:
- ✅ **Authentication Required**: JWT token validation
- ✅ **Functional Access Control**: Requires `apigee_management` functional permission
- ✅ **Role-based Access**: Only admin, manager, or developer roles allowed
- ✅ **Comprehensive Logging**: Transaction ID, correlation ID, user context
- ✅ **Error Handling**: Graceful error handling with proper HTTP status codes

### **JIRA Ticket Check Endpoint**
```python
@app.route("/check_ticket/<issue_key>", methods=["GET"])
@get_wells_authenticated_user
@require_functional_access("jira_access", ["admin", "manager", "developer", "tester"])
def check_jira_route(issue_key: str):
```

**Security Features**:
- ✅ **Authentication Required**: JWT token validation
- ✅ **Functional Access Control**: Requires `jira_access` functional permission
- ✅ **Role-based Access**: admin, manager, developer, or tester roles allowed
- ✅ **Comprehensive Logging**: Full request context logging

### **JIRA Ticket Handling Endpoint**
```python
@app.route("/jira_ticket", methods=["POST"])
@get_wells_authenticated_user
@require_functional_access("jira_management", ["admin", "manager", "developer"])
@require_wells_scope("write")
def handle_ticket_route():
```

**Security Features**:
- ✅ **Authentication Required**: JWT token validation
- ✅ **Functional Access Control**: Requires `jira_management` functional permission
- ✅ **Role-based Access**: admin, manager, or developer roles allowed
- ✅ **Scope-based Access**: Requires `write` scope
- ✅ **File Upload Security**: Logs file information without exposing content
- ✅ **Form Data Validation**: Validates form data and files

### **Get Tickets by Label Endpoint**
```python
@app.route("/get_tickets_by_label/<label>", methods=["GET"])
@get_wells_authenticated_user
@require_functional_access("jira_query", ["admin", "manager", "developer", "tester", "customer_service"])
def get_tickets_by_label_route(label: str):
```

**Security Features**:
- ✅ **Authentication Required**: JWT token validation
- ✅ **Functional Access Control**: Requires `jira_query` functional permission
- ✅ **Role-based Access**: Multiple roles allowed including customer_service
- ✅ **Query Parameter Validation**: Validates and logs query parameters

### **Ticket Status Processing Endpoint**
```python
@app.route("/ticket_current_status/<ticket_id>", methods=["GET"])
@get_wells_authenticated_user
@require_functional_access("jira_status", ["admin", "manager", "developer", "tester"])
def process_ticket_labels_route(ticket_id: str):
```

**Security Features**:
- ✅ **Authentication Required**: JWT token validation
- ✅ **Functional Access Control**: Requires `jira_status` functional permission
- ✅ **Role-based Access**: admin, manager, developer, or tester roles allowed

## 🔧 **JWT Token Requirements**

Your JWT tokens should include these claims for the security features to work:

```json
{
  "sub": "user123@wellsfargo.com",
  "client_id": "EBSSH",
  "iss": "https://wellsfargo.com/oauth2",
  "aud": "api.wellsfargo.com",
  "scope": ["read", "write"],
  "roles": ["admin", "manager", "developer"],
  "functional_permissions": [
    "apigee_management",
    "jira_access",
    "jira_management",
    "jira_query",
    "jira_status"
  ],
  "department": "IT",
  "exp": 1640995200,
  "iat": 1640908800
}
```

## 📋 **Functional Permissions Required**

| Endpoint | Functional Permission | Required Roles |
|----------|----------------------|----------------|
| `/apigee_proxy_update/<issue_key>` | `apigee_management` | admin, manager, developer |
| `/check_ticket/<issue_key>` | `jira_access` | admin, manager, developer, tester |
| `/jira_ticket` | `jira_management` | admin, manager, developer |
| `/get_tickets_by_label/<label>` | `jira_query` | admin, manager, developer, tester, customer_service |
| `/ticket_current_status/<ticket_id>` | `jira_status` | admin, manager, developer, tester |

## 🎯 **Additional Security Endpoints**

### **User Permissions Endpoint**
```python
@app.route("/user/permissions", methods=["GET"])
@get_wells_authenticated_user
def get_user_permissions():
```

**Purpose**: Get current user's permissions and access information
**Security**: Authentication required only

### **Permission Testing Endpoint**
```python
@app.route("/security/test-permission", methods=["POST"])
@get_wells_authenticated_user
def test_permission():
```

**Purpose**: Test specific permissions for the current user
**Security**: Authentication required only

## 🔒 **Security Response Examples**

### **Successful Access**
```json
{
  "code": "200",
  "status": "success",
  "message": "JIRA ticket check completed",
  "transaction_id": "abc123-def456-ghi789",
  "correlation_id": "xyz789-uvw456-rst123",
  "user_id": "user123@wellsfargo.com",
  "access_granted": true,
  "data": {
    "ticket_status": "open",
    "assignee": "john.doe"
  }
}
```

### **Authentication Required**
```json
{
  "code": "401",
  "status": "auth_error",
  "error_message": "Authorization header required"
}
```

### **Access Denied - Insufficient Role**
```json
{
  "code": "403",
  "status": "access_denied",
  "error_message": "Access denied to function 'jira_management'. Required roles: ['admin', 'manager', 'developer']"
}
```

### **Access Denied - Insufficient Scope**
```json
{
  "code": "403",
  "status": "auth_error",
  "error_message": "Insufficient scope. Required: write"
}
```

## 🚀 **Testing the Security Implementation**

### **1. Test Authentication**
```bash
# Without token (should fail)
curl -X GET "http://localhost:8000/check_ticket/TICKET-123"

# With valid token (should succeed)
curl -X GET "http://localhost:8000/check_ticket/TICKET-123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **2. Test Functional Access Control**
```bash
# Test with user who has jira_access permission
curl -X GET "http://localhost:8000/check_ticket/TICKET-123" \
  -H "Authorization: Bearer VALID_JWT_TOKEN"

# Test with user who lacks jira_access permission (should fail)
curl -X GET "http://localhost:8000/check_ticket/TICKET-123" \
  -H "Authorization: Bearer INVALID_PERMISSIONS_TOKEN"
```

### **3. Test Role-based Access**
```bash
# Test with admin role (should succeed)
curl -X POST "http://localhost:8000/jira_ticket" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "summary=Test ticket"

# Test with customer_service role (should fail)
curl -X POST "http://localhost:8000/jira_ticket" \
  -H "Authorization: Bearer CUSTOMER_SERVICE_TOKEN" \
  -F "summary=Test ticket"
```

### **4. Test Scope-based Access**
```bash
# Test with write scope (should succeed)
curl -X POST "http://localhost:8000/jira_ticket" \
  -H "Authorization: Bearer WRITE_SCOPE_TOKEN" \
  -F "summary=Test ticket"

# Test with read-only scope (should fail)
curl -X POST "http://localhost:8000/jira_ticket" \
  -H "Authorization: Bearer READ_ONLY_TOKEN" \
  -F "summary=Test ticket"
```

## 📊 **Security Logging**

All security events are logged with comprehensive context:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "JIRA ticket check requested",
  "correlation_id": "xyz789-uvw456-rst123",
  "transaction_id": "abc123-def456-ghi789",
  "issue_key": "TICKET-123",
  "user_sub": "user123@wellsfargo.com",
  "user_roles": ["admin", "manager"],
  "endpoint": "/check_ticket",
  "access_granted": true
}
```

## 🔧 **Configuration**

The security implementation uses the existing Wells Fargo AuthX configuration:

```env
WELLS_AUTH_ENVIRONMENT=dev
WELLS_AUTH_APIGEE_JWKS_URL=https://your-jwks-url
WELLS_AUTH_APIGEE_CLIENT_ID=EBSSH
BEHIND_PROXY=false
LOG_LEVEL=info
```

## 🎯 **Benefits of This Implementation**

1. **Comprehensive Security**: Multiple layers of security (auth, functional, role-based, scope-based)
2. **Fine-grained Control**: Specific permissions for different operations
3. **Audit Trail**: Complete logging of all security events
4. **Error Handling**: Graceful error handling with proper HTTP status codes
5. **Correlation Tracking**: Request tracking for debugging and monitoring
6. **Production Ready**: Enterprise-grade security implementation
7. **Flexible**: Easy to add new permissions and roles as needed

## 📚 **Integration with Existing Services**

The security implementation integrates seamlessly with your existing service functions:

- **`src.services.jira_service`**: All JIRA-related functions
- **`src.services.file_service`**: Apigee proxy update function

All service functions receive the transaction ID and can use it for logging and tracking. The security layer adds user context and access control without modifying the existing service logic.

This implementation provides enterprise-grade security for your Wells Fargo AuthX Flask application while maintaining compatibility with your existing service architecture.
