"""Object-Level and Functional Access Control for Wells Fargo AuthX Flask application."""

import logging
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
from enum import Enum

from flask import request, jsonify, g

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access levels for object-level permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(Enum):
    """Resource types for object-level access control."""
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    CUSTOMER = "customer"
    LOAN = "loan"
    CARD = "card"
    DOCUMENT = "document"
    REPORT = "report"
    USER = "user"
    SYSTEM = "system"


class Permission:
    """Represents a permission for access control."""
    
    def __init__(self, resource_type: ResourceType, resource_id: str, access_level: AccessLevel):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.access_level = access_level
    
    def __str__(self):
        return f"{self.resource_type.value}:{self.resource_id}:{self.access_level.value}"
    
    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return (self.resource_type == other.resource_type and
                self.resource_id == other.resource_id and
                self.access_level == other.access_level)
    
    def __hash__(self):
        return hash((self.resource_type, self.resource_id, self.access_level))


class AccessControlPolicy:
    """Access control policy engine."""
    
    def __init__(self):
        self.policies = {}
        self.default_deny = True
    
    def add_policy(self, policy_name: str, policy_func: Callable[[Dict[str, Any], Permission], bool]):
        """Add a custom policy function."""
        self.policies[policy_name] = policy_func
    
    def check_permission(self, user_claims: Dict[str, Any], permission: Permission) -> bool:
        """
        Check if user has permission for a specific resource.
        
        Args:
            user_claims: JWT claims from authenticated user
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Extract user permissions from claims
            user_permissions = self._extract_user_permissions(user_claims)
            
            # Check direct permission match
            if permission in user_permissions:
                logger.info(f"Direct permission match: {permission}")
                return True
            
            # Check wildcard permissions
            if self._check_wildcard_permissions(user_permissions, permission):
                logger.info(f"Wildcard permission match: {permission}")
                return True
            
            # Check role-based permissions
            if self._check_role_permissions(user_claims, permission):
                logger.info(f"Role-based permission match: {permission}")
                return True
            
            # Check custom policies
            if self._check_custom_policies(user_claims, permission):
                logger.info(f"Custom policy permission match: {permission}")
                return True
            
            logger.warning(f"Permission denied: {permission}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def _extract_user_permissions(self, user_claims: Dict[str, Any]) -> List[Permission]:
        """Extract permissions from user claims."""
        permissions = []
        
        # Extract from 'permissions' claim
        if 'permissions' in user_claims:
            for perm_str in user_claims['permissions']:
                try:
                    perm = self._parse_permission_string(perm_str)
                    if perm:
                        permissions.append(perm)
                except Exception as e:
                    logger.warning(f"Invalid permission format: {perm_str}, error: {e}")
        
        # Extract from 'resource_permissions' claim (more structured)
        if 'resource_permissions' in user_claims:
            for resource_perm in user_claims['resource_permissions']:
                try:
                    perm = self._parse_resource_permission(resource_perm)
                    if perm:
                        permissions.append(perm)
                except Exception as e:
                    logger.warning(f"Invalid resource permission format: {resource_perm}, error: {e}")
        
        return permissions
    
    def _parse_permission_string(self, perm_str: str) -> Optional[Permission]:
        """Parse permission string in format 'resource_type:resource_id:access_level'."""
        try:
            parts = perm_str.split(':')
            if len(parts) != 3:
                return None
            
            resource_type = ResourceType(parts[0])
            resource_id = parts[1]
            access_level = AccessLevel(parts[2])
            
            return Permission(resource_type, resource_id, access_level)
        except (ValueError, KeyError):
            return None
    
    def _parse_resource_permission(self, resource_perm: Dict[str, Any]) -> Optional[Permission]:
        """Parse structured resource permission."""
        try:
            resource_type = ResourceType(resource_perm['resource_type'])
            resource_id = resource_perm['resource_id']
            access_level = AccessLevel(resource_perm['access_level'])
            
            return Permission(resource_type, resource_id, access_level)
        except (KeyError, ValueError):
            return None
    
    def _check_wildcard_permissions(self, user_permissions: List[Permission], required_permission: Permission) -> bool:
        """Check for wildcard permissions (e.g., account:*:read)."""
        for user_perm in user_permissions:
            # Check if user has wildcard permission for this resource type and access level
            if (user_perm.resource_type == required_permission.resource_type and
                user_perm.resource_id == "*" and
                user_perm.access_level == required_permission.access_level):
                return True
            
            # Check if user has admin access to this resource type
            if (user_perm.resource_type == required_permission.resource_type and
                user_perm.resource_id == "*" and
                user_perm.access_level == AccessLevel.ADMIN):
                return True
        
        return False
    
    def _check_role_permissions(self, user_claims: Dict[str, Any], permission: Permission) -> bool:
        """Check role-based permissions."""
        user_roles = user_claims.get('roles', [])
        
        # Define role-based permissions
        role_permissions = {
            'admin': {
                ResourceType.ACCOUNT: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.TRANSACTION: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.CUSTOMER: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.LOAN: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.CARD: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.DOCUMENT: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.REPORT: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.USER: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN],
                ResourceType.SYSTEM: [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.DELETE, AccessLevel.ADMIN]
            },
            'manager': {
                ResourceType.ACCOUNT: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.TRANSACTION: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.CUSTOMER: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.LOAN: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.CARD: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.DOCUMENT: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.REPORT: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.USER: [AccessLevel.READ]
            },
            'teller': {
                ResourceType.ACCOUNT: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.TRANSACTION: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.CUSTOMER: [AccessLevel.READ],
                ResourceType.CARD: [AccessLevel.READ]
            },
            'customer_service': {
                ResourceType.ACCOUNT: [AccessLevel.READ],
                ResourceType.TRANSACTION: [AccessLevel.READ],
                ResourceType.CUSTOMER: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.CARD: [AccessLevel.READ, AccessLevel.WRITE],
                ResourceType.DOCUMENT: [AccessLevel.READ]
            },
            'auditor': {
                ResourceType.ACCOUNT: [AccessLevel.READ],
                ResourceType.TRANSACTION: [AccessLevel.READ],
                ResourceType.CUSTOMER: [AccessLevel.READ],
                ResourceType.LOAN: [AccessLevel.READ],
                ResourceType.CARD: [AccessLevel.READ],
                ResourceType.DOCUMENT: [AccessLevel.READ],
                ResourceType.REPORT: [AccessLevel.READ]
            }
        }
        
        for role in user_roles:
            if role in role_permissions:
                role_perm = role_permissions[role]
                if (permission.resource_type in role_perm and
                    permission.access_level in role_perm[permission.resource_type]):
                    return True
        
        return False
    
    def _check_custom_policies(self, user_claims: Dict[str, Any], permission: Permission) -> bool:
        """Check custom policy functions."""
        for policy_name, policy_func in self.policies.items():
            try:
                if policy_func(user_claims, permission):
                    logger.info(f"Custom policy '{policy_name}' granted permission: {permission}")
                    return True
            except Exception as e:
                logger.error(f"Error in custom policy '{policy_name}': {e}")
        
        return False


# Global access control policy instance
access_control_policy = AccessControlPolicy()


def require_object_permission(resource_type: ResourceType, resource_id: Union[str, Callable], access_level: AccessLevel):
    """
    Decorator factory for object-level access control.
    
    Args:
        resource_type: Type of resource (e.g., ResourceType.ACCOUNT)
        resource_id: Resource ID (string or callable to extract from request)
        access_level: Required access level (e.g., AccessLevel.READ)
        
    Usage:
        @app.route("/accounts/<account_id>")
        @require_object_permission(ResourceType.ACCOUNT, lambda: request.view_args['account_id'], AccessLevel.READ)
        def get_account(account_id):
            return {"account_id": account_id}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check authentication first
            if not hasattr(g, 'current_user'):
                return jsonify({
                    "code": "401",
                    "status": "auth_error",
                    "error_message": "Authentication required"
                }), 401
            
            # Extract resource ID
            if callable(resource_id):
                try:
                    actual_resource_id = resource_id()
                except Exception as e:
                    logger.error(f"Error extracting resource ID: {e}")
                    return jsonify({
                        "code": "400",
                        "status": "error",
                        "error_message": "Invalid resource ID"
                    }), 400
            else:
                actual_resource_id = resource_id
            
            # Create permission object
            permission = Permission(resource_type, actual_resource_id, access_level)
            
            # Check permission
            if not access_control_policy.check_permission(g.current_user, permission):
                logger.warning(
                    "Object-level access denied",
                    extra={
                        "user_sub": g.current_user.get('sub'),
                        "resource_type": resource_type.value,
                        "resource_id": actual_resource_id,
                        "access_level": access_level.value,
                        "permission": str(permission)
                    }
                )
                return jsonify({
                    "code": "403",
                    "status": "access_denied",
                    "error_message": f"Access denied to {resource_type.value}:{actual_resource_id} with {access_level.value} permission"
                }), 403
            
            # Store permission info in g for use in route handler
            g.current_permission = permission
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_functional_access(function_name: str, required_roles: Optional[List[str]] = None):
    """
    Decorator for functional access control.
    
    Args:
        function_name: Name of the function/feature being accessed
        required_roles: List of roles that can access this function (optional)
        
    Usage:
        @app.route("/admin/users")
        @require_functional_access("user_management", ["admin", "manager"])
        def manage_users():
            return {"message": "User management access granted"}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check authentication first
            if not hasattr(g, 'current_user'):
                return jsonify({
                    "code": "401",
                    "status": "auth_error",
                    "error_message": "Authentication required"
                }), 401
            
            user_claims = g.current_user
            user_roles = user_claims.get('roles', [])
            
            # Check if user has required roles
            if required_roles:
                if not any(role in user_roles for role in required_roles):
                    logger.warning(
                        "Functional access denied - insufficient roles",
                        extra={
                            "user_sub": user_claims.get('sub'),
                            "function_name": function_name,
                            "user_roles": user_roles,
                            "required_roles": required_roles
                        }
                    )
                    return jsonify({
                        "code": "403",
                        "status": "access_denied",
                        "error_message": f"Access denied to function '{function_name}'. Required roles: {required_roles}"
                    }), 403
            
            # Check functional permissions in claims
            functional_permissions = user_claims.get('functional_permissions', [])
            if function_name not in functional_permissions:
                logger.warning(
                    "Functional access denied - no permission",
                    extra={
                        "user_sub": user_claims.get('sub'),
                        "function_name": function_name,
                        "user_functional_permissions": functional_permissions
                    }
                )
                return jsonify({
                    "code": "403",
                    "status": "access_denied",
                    "error_message": f"Access denied to function '{function_name}'"
                }), 403
            
            # Store function info in g for use in route handler
            g.current_function = function_name
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_user_owns_resource(user_claims: Dict[str, Any], resource_type: ResourceType, resource_id: str) -> bool:
    """
    Check if user owns a specific resource.
    
    Args:
        user_claims: JWT claims from authenticated user
        resource_type: Type of resource
        resource_id: Resource ID to check ownership
        
    Returns:
        True if user owns the resource, False otherwise
    """
    user_id = user_claims.get('sub')
    
    # Check if user owns the resource directly
    if resource_type == ResourceType.ACCOUNT:
        user_accounts = user_claims.get('accounts', [])
        return resource_id in user_accounts
    
    elif resource_type == ResourceType.CARD:
        user_cards = user_claims.get('cards', [])
        return resource_id in user_cards
    
    elif resource_type == ResourceType.LOAN:
        user_loans = user_claims.get('loans', [])
        return resource_id in user_loans
    
    # For other resource types, check if resource_id matches user_id
    elif resource_type == ResourceType.USER:
        return resource_id == user_id
    
    return False


def add_ownership_policy():
    """Add ownership-based policy to access control."""
    def ownership_policy(user_claims: Dict[str, Any], permission: Permission) -> bool:
        """Policy that grants access if user owns the resource."""
        return check_user_owns_resource(user_claims, permission.resource_type, permission.resource_id)
    
    access_control_policy.add_policy("ownership", ownership_policy)


def add_department_policy():
    """Add department-based policy to access control."""
    def department_policy(user_claims: Dict[str, Any], permission: Permission) -> bool:
        """Policy that grants access based on department."""
        user_department = user_claims.get('department')
        resource_department = permission.resource_id.split(':')[0] if ':' in permission.resource_id else None
        
        # If resource has department info and user is in same department
        if resource_department and user_department == resource_department:
            return True
        
        return False
    
    access_control_policy.add_policy("department", department_policy)


# Initialize default policies
add_ownership_policy()
add_department_policy()


# Helper functions for common access patterns
def require_account_access(access_level: AccessLevel = AccessLevel.READ):
    """Helper decorator for account access."""
    return require_object_permission(
        ResourceType.ACCOUNT,
        lambda: request.view_args.get('account_id') or request.args.get('account_id'),
        access_level
    )


def require_transaction_access(access_level: AccessLevel = AccessLevel.READ):
    """Helper decorator for transaction access."""
    return require_object_permission(
        ResourceType.TRANSACTION,
        lambda: request.view_args.get('transaction_id') or request.args.get('transaction_id'),
        access_level
    )


def require_customer_access(access_level: AccessLevel = AccessLevel.READ):
    """Helper decorator for customer access."""
    return require_object_permission(
        ResourceType.CUSTOMER,
        lambda: request.view_args.get('customer_id') or request.args.get('customer_id'),
        access_level
    )


def require_loan_access(access_level: AccessLevel = AccessLevel.READ):
    """Helper decorator for loan access."""
    return require_object_permission(
        ResourceType.LOAN,
        lambda: request.view_args.get('loan_id') or request.args.get('loan_id'),
        access_level
    )


def require_card_access(access_level: AccessLevel = AccessLevel.READ):
    """Helper decorator for card access."""
    return require_object_permission(
        ResourceType.CARD,
        lambda: request.view_args.get('card_id') or request.args.get('card_id'),
        access_level
    )
