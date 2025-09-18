# Wells Fargo AuthX - Object-Level and Functional Access Control Guide

## 🎯 **Overview**

The Wells Fargo AuthX Flask application now includes comprehensive **Object-Level** and **Functional Access Control** capabilities that provide fine-grained authorization beyond basic scope-based access control.

## 🔐 **Access Control Types**

### **1. Object-Level Access Control**
Controls access to specific resources (accounts, transactions, customers, etc.) based on:
- **Resource Type**: What type of resource (account, transaction, customer, etc.)
- **Resource ID**: Specific instance of the resource
- **Access Level**: What action (read, write, delete, admin)

### **2. Functional Access Control**
Controls access to specific functions/features based on:
- **Function Name**: Specific business function (user_management, financial_reporting, etc.)
- **User Roles**: Required roles to access the function

### **3. Ownership-Based Access Control**
Automatic access to resources owned by the user based on JWT claims.

## 📊 **Access Levels**

```python
class AccessLevel(Enum):
    READ = "read"      # View/read access
    WRITE = "write"    # Modify/update access
    DELETE = "delete"  # Delete access
    ADMIN = "admin"    # Full administrative access
```

## 🏗️ **Resource Types**

```python
class ResourceType(Enum):
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    CUSTOMER = "customer"
    LOAN = "loan"
    CARD = "card"
    DOCUMENT = "document"
    REPORT = "report"
    USER = "user"
    SYSTEM = "system"
```

## 🎭 **Role-Based Permissions**

The system includes predefined role-based permissions:

### **Admin Role**
- Full access to all resource types
- All access levels (read, write, delete, admin)

### **Manager Role**
- Read/write access to most resources
- Read access to users

### **Teller Role**
- Read/write access to accounts and transactions
- Read access to customers and cards

### **Customer Service Role**
- Read access to accounts and transactions
- Read/write access to customers and cards
- Read access to documents

### **Auditor Role**
- Read access to all resources (no write access)

## 🔧 **JWT Claims Structure**

For access control to work, your JWT tokens should include these claims:

```json
{
  "sub": "user123@wellsfargo.com",
  "client_id": "EBSSH",
  "roles": ["manager", "teller"],
  "scope": ["read", "write"],
  "permissions": [
    "account:ACC123:read",
    "account:ACC123:write",
    "transaction:TXN456:read"
  ],
  "resource_permissions": [
    {
      "resource_type": "account",
      "resource_id": "ACC123",
      "access_level": "read"
    },
    {
      "resource_type": "account", 
      "resource_id": "ACC123",
      "access_level": "write"
    }
  ],
  "functional_permissions": [
    "user_management",
    "financial_reporting",
    "account_management"
  ],
  "accounts": ["ACC123", "ACC456"],
  "cards": ["CARD789"],
  "loans": ["LOAN101"],
  "department": "IT"
}
```

## 🚀 **Usage Examples**

### **1. Object-Level Access Control**

#### **Basic Object Permission**
```python
from security import require_object_permission, ResourceType, AccessLevel

@app.route("/accounts/<account_id>")
@get_wells_authenticated_user
@require_object_permission(ResourceType.ACCOUNT, lambda: request.view_args['account_id'], AccessLevel.READ)
def get_account(account_id):
    return {"account_id": account_id}
```

#### **Helper Decorators**
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

### **2. Functional Access Control**

```python
from security import require_functional_access

@app.route("/admin/users")
@get_wells_authenticated_user
@require_functional_access("user_management", ["admin", "manager"])
def manage_users():
    return {"message": "User management access granted"}
```

### **3. Combined Access Control**

```python
@app.route("/accounts/<account_id>/transactions")
@get_wells_authenticated_user
@require_account_access(AccessLevel.READ)
@require_functional_access("transaction_viewing", ["admin", "manager", "teller"])
def get_account_transactions(account_id):
    return {"account_id": account_id, "transactions": []}
```

### **4. Ownership-Based Access**

```python
from security import check_user_owns_resource, ResourceType

@app.route("/my-accounts")
@get_wells_authenticated_user
def get_my_accounts():
    current_user = g.current_user
    user_accounts = current_user.get('accounts', [])
    
    # User automatically has access to their own accounts
    return {"accounts": user_accounts}
```

## 📋 **API Endpoints**

### **Object-Level Access Control Endpoints**

| Endpoint | Method | Access Control | Description |
|----------|--------|----------------|-------------|
| `/api/v1/access-control/accounts/<account_id>` | GET | Account READ | Get account details |
| `/api/v1/access-control/accounts/<account_id>` | PUT | Account WRITE | Update account |
| `/api/v1/access-control/accounts/<account_id>` | DELETE | Account DELETE | Delete account |
| `/api/v1/access-control/transactions/<transaction_id>` | GET | Transaction READ | Get transaction details |
| `/api/v1/access-control/customers/<customer_id>` | GET | Customer READ | Get customer details |
| `/api/v1/access-control/loans/<loan_id>` | GET | Loan READ | Get loan details |
| `/api/v1/access-control/cards/<card_id>` | GET | Card READ | Get card details |

### **Functional Access Control Endpoints**

| Endpoint | Method | Access Control | Description |
|----------|--------|----------------|-------------|
| `/api/v1/access-control/admin/users` | GET | user_management + admin/manager role | User management |
| `/api/v1/access-control/reports/financial` | GET | financial_reporting + admin/manager/auditor role | Financial reporting |
| `/api/v1/access-control/system/config` | GET | system_administration + admin role | System configuration |

### **Combined Access Control Endpoints**

| Endpoint | Method | Access Control | Description |
|----------|--------|----------------|-------------|
| `/api/v1/access-control/accounts/<account_id>/transactions` | GET | Account READ + transaction_viewing function | Get account transactions |
| `/api/v1/access-control/customers/<customer_id>/accounts` | GET | Customer READ + account_management function | Get customer accounts |

### **Information Endpoints**

| Endpoint | Method | Access Control | Description |
|----------|--------|----------------|-------------|
| `/api/v1/access-control/permissions` | GET | Authentication only | Get user permissions |
| `/api/v1/access-control/test-permission` | POST | Authentication only | Test specific permission |
| `/api/v1/access-control/my-accounts` | GET | Authentication only | Get user's own accounts |
| `/api/v1/access-control/my-cards` | GET | Authentication only | Get user's own cards |

## 🧪 **Testing Access Control**

### **1. Test User Permissions**
```bash
curl -X GET "http://localhost:8000/api/v1/access-control/permissions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **2. Test Specific Permission**
```bash
curl -X POST "http://localhost:8000/api/v1/access-control/test-permission" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "account",
    "resource_id": "ACC123",
    "access_level": "read"
  }'
```

### **3. Test Object-Level Access**
```bash
curl -X GET "http://localhost:8000/api/v1/access-control/accounts/ACC123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **4. Test Functional Access**
```bash
curl -X GET "http://localhost:8000/api/v1/access-control/admin/users" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔒 **Permission Evaluation Order**

The access control system evaluates permissions in this order:

1. **Direct Permissions**: Exact match in `permissions` or `resource_permissions` claims
2. **Wildcard Permissions**: `*` resource ID with matching type and access level
3. **Role-Based Permissions**: Based on user roles and predefined role permissions
4. **Custom Policies**: Ownership-based and department-based policies
5. **Default Deny**: If no permission is found, access is denied

## 🎯 **Custom Policies**

You can add custom access control policies:

```python
from security import access_control_policy

def custom_policy(user_claims, permission):
    """Custom policy function."""
    # Your custom logic here
    return True  # or False

# Add the policy
access_control_policy.add_policy("custom_policy", custom_policy)
```

## 📊 **Response Examples**

### **Successful Access**
```json
{
  "code": "200",
  "status": "success",
  "message": "Account access granted",
  "account": {
    "account_id": "ACC123",
    "account_type": "checking",
    "balance": 15000.00,
    "permission_used": "account:ACC123:read"
  }
}
```

### **Access Denied**
```json
{
  "code": "403",
  "status": "access_denied",
  "error_message": "Access denied to account:ACC123 with read permission"
}
```

### **Permission Test Result**
```json
{
  "code": "200",
  "status": "success",
  "message": "Permission test completed",
  "permission": "account:ACC123:read",
  "has_permission": true,
  "user_id": "user123@wellsfargo.com"
}
```

## 🚀 **Best Practices**

### **1. JWT Token Design**
- Include all necessary permission claims
- Use structured `resource_permissions` for complex scenarios
- Include ownership information (`accounts`, `cards`, etc.)

### **2. Decorator Usage**
- Use helper decorators when possible (`@require_account_access`)
- Combine object-level and functional access control as needed
- Always authenticate first (`@get_wells_authenticated_user`)

### **3. Error Handling**
- Access control decorators return standardized error responses
- Log access control decisions for auditing
- Use correlation IDs for request tracking

### **4. Performance**
- Permissions are evaluated in order of specificity
- Cache permission results when possible
- Use wildcard permissions for broad access patterns

## 🔧 **Configuration**

The access control system is configured through the JWT claims. No additional configuration is required, but you can customize:

- Role-based permissions in `AccessControlPolicy._check_role_permissions()`
- Custom policies via `access_control_policy.add_policy()`
- Resource types and access levels as needed

## 📚 **Integration**

The access control system integrates seamlessly with the existing Wells Fargo AuthX authentication:

1. **Authentication**: JWT token validation via `@get_wells_authenticated_user`
2. **Authorization**: Access control via object-level and functional decorators
3. **Logging**: All access control decisions are logged with correlation IDs
4. **Error Handling**: Standardized error responses for access denied scenarios

This provides a comprehensive, enterprise-grade access control system for the Wells Fargo AuthX Flask application.
