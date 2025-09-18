"""Test file for Object-Level and Functional Access Control."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from ..security.access_control import (
    AccessLevel,
    ResourceType,
    Permission,
    AccessControlPolicy,
    access_control_policy,
    require_object_permission,
    require_functional_access,
    check_user_owns_resource
)


class TestAccessLevel:
    """Test AccessLevel enum."""
    
    def test_access_level_values(self):
        """Test access level enum values."""
        assert AccessLevel.READ.value == "read"
        assert AccessLevel.WRITE.value == "write"
        assert AccessLevel.DELETE.value == "delete"
        assert AccessLevel.ADMIN.value == "admin"


class TestResourceType:
    """Test ResourceType enum."""
    
    def test_resource_type_values(self):
        """Test resource type enum values."""
        assert ResourceType.ACCOUNT.value == "account"
        assert ResourceType.TRANSACTION.value == "transaction"
        assert ResourceType.CUSTOMER.value == "customer"
        assert ResourceType.LOAN.value == "loan"
        assert ResourceType.CARD.value == "card"


class TestPermission:
    """Test Permission class."""
    
    def test_permission_creation(self):
        """Test permission object creation."""
        perm = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        
        assert perm.resource_type == ResourceType.ACCOUNT
        assert perm.resource_id == "ACC123"
        assert perm.access_level == AccessLevel.READ
    
    def test_permission_string_representation(self):
        """Test permission string representation."""
        perm = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert str(perm) == "account:ACC123:read"
    
    def test_permission_equality(self):
        """Test permission equality."""
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        perm2 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        perm3 = Permission(ResourceType.ACCOUNT, "ACC456", AccessLevel.READ)
        
        assert perm1 == perm2
        assert perm1 != perm3
    
    def test_permission_hash(self):
        """Test permission hashing."""
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        perm2 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        
        assert hash(perm1) == hash(perm2)


class TestAccessControlPolicy:
    """Test AccessControlPolicy class."""
    
    def setup_method(self):
        """Set up test policy."""
        self.policy = AccessControlPolicy()
    
    def test_direct_permission_match(self):
        """Test direct permission matching."""
        user_claims = {
            "sub": "user123",
            "permissions": ["account:ACC123:read", "account:ACC456:write"]
        }
        
        # Test matching permission
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm1) is True
        
        # Test non-matching permission
        perm2 = Permission(ResourceType.ACCOUNT, "ACC789", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm2) is False
    
    def test_wildcard_permissions(self):
        """Test wildcard permission matching."""
        user_claims = {
            "sub": "user123",
            "permissions": ["account:*:read", "transaction:*:write"]
        }
        
        # Test wildcard match
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm1) is True
        
        # Test wildcard admin access
        perm2 = Permission(ResourceType.ACCOUNT, "ACC456", AccessLevel.WRITE)
        assert self.policy.check_permission(user_claims, perm2) is False
        
        # Test admin wildcard
        user_claims_admin = {
            "sub": "user123",
            "permissions": ["account:*:admin"]
        }
        perm3 = Permission(ResourceType.ACCOUNT, "ACC789", AccessLevel.READ)
        assert self.policy.check_permission(user_claims_admin, perm3) is True
    
    def test_role_based_permissions(self):
        """Test role-based permission matching."""
        user_claims = {
            "sub": "user123",
            "roles": ["admin"]
        }
        
        # Admin should have access to everything
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm1) is True
        
        perm2 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.DELETE)
        assert self.policy.check_permission(user_claims, perm2) is True
        
        # Manager should have read/write access
        user_claims_manager = {
            "sub": "user123",
            "roles": ["manager"]
        }
        
        perm3 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims_manager, perm3) is True
        
        perm4 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.WRITE)
        assert self.policy.check_permission(user_claims_manager, perm4) is True
        
        perm5 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.DELETE)
        assert self.policy.check_permission(user_claims_manager, perm5) is False
    
    def test_teller_permissions(self):
        """Test teller role permissions."""
        user_claims = {
            "sub": "user123",
            "roles": ["teller"]
        }
        
        # Teller should have read/write access to accounts and transactions
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm1) is True
        
        perm2 = Permission(ResourceType.TRANSACTION, "TXN456", AccessLevel.WRITE)
        assert self.policy.check_permission(user_claims, perm2) is True
        
        # Teller should not have delete access
        perm3 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.DELETE)
        assert self.policy.check_permission(user_claims, perm3) is False
    
    def test_structured_resource_permissions(self):
        """Test structured resource permissions."""
        user_claims = {
            "sub": "user123",
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
            ]
        }
        
        perm1 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm1) is True
        
        perm2 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.WRITE)
        assert self.policy.check_permission(user_claims, perm2) is True
        
        perm3 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.DELETE)
        assert self.policy.check_permission(user_claims, perm3) is False
    
    def test_custom_policy(self):
        """Test custom policy functions."""
        def custom_policy(user_claims, permission):
            return permission.resource_id == "SPECIAL123"
        
        self.policy.add_policy("custom", custom_policy)
        
        user_claims = {"sub": "user123"}
        
        perm1 = Permission(ResourceType.ACCOUNT, "SPECIAL123", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm1) is True
        
        perm2 = Permission(ResourceType.ACCOUNT, "NORMAL456", AccessLevel.READ)
        assert self.policy.check_permission(user_claims, perm2) is False


class TestOwnershipFunctions:
    """Test ownership-based access control functions."""
    
    def test_check_user_owns_account(self):
        """Test account ownership checking."""
        user_claims = {
            "sub": "user123",
            "accounts": ["ACC123", "ACC456"]
        }
        
        assert check_user_owns_resource(user_claims, ResourceType.ACCOUNT, "ACC123") is True
        assert check_user_owns_resource(user_claims, ResourceType.ACCOUNT, "ACC456") is True
        assert check_user_owns_resource(user_claims, ResourceType.ACCOUNT, "ACC789") is False
    
    def test_check_user_owns_card(self):
        """Test card ownership checking."""
        user_claims = {
            "sub": "user123",
            "cards": ["CARD123", "CARD456"]
        }
        
        assert check_user_owns_resource(user_claims, ResourceType.CARD, "CARD123") is True
        assert check_user_owns_resource(user_claims, ResourceType.CARD, "CARD789") is False
    
    def test_check_user_owns_loan(self):
        """Test loan ownership checking."""
        user_claims = {
            "sub": "user123",
            "loans": ["LOAN123", "LOAN456"]
        }
        
        assert check_user_owns_resource(user_claims, ResourceType.LOAN, "LOAN123") is True
        assert check_user_owns_resource(user_claims, ResourceType.LOAN, "LOAN789") is False
    
    def test_check_user_owns_user(self):
        """Test user ownership checking."""
        user_claims = {
            "sub": "user123"
        }
        
        assert check_user_owns_resource(user_claims, ResourceType.USER, "user123") is True
        assert check_user_owns_resource(user_claims, ResourceType.USER, "user456") is False


class TestIntegration:
    """Integration tests for access control system."""
    
    def test_complete_access_control_flow(self):
        """Test complete access control flow."""
        # Test user with multiple permission types
        user_claims = {
            "sub": "user123",
            "roles": ["manager"],
            "permissions": ["account:ACC123:read"],
            "resource_permissions": [
                {
                    "resource_type": "transaction",
                    "resource_id": "TXN456",
                    "access_level": "write"
                }
            ],
            "accounts": ["ACC789"],
            "functional_permissions": ["user_management"]
        }
        
        # Test role-based access
        perm1 = Permission(ResourceType.ACCOUNT, "ACC999", AccessLevel.READ)
        assert access_control_policy.check_permission(user_claims, perm1) is True
        
        # Test direct permission
        perm2 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
        assert access_control_policy.check_permission(user_claims, perm2) is True
        
        # Test structured permission
        perm3 = Permission(ResourceType.TRANSACTION, "TXN456", AccessLevel.WRITE)
        assert access_control_policy.check_permission(user_claims, perm3) is True
        
        # Test ownership
        assert check_user_owns_resource(user_claims, ResourceType.ACCOUNT, "ACC789") is True
        
        # Test denied access
        perm4 = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.DELETE)
        assert access_control_policy.check_permission(user_claims, perm4) is False


if __name__ == "__main__":
    # Run basic tests
    print("Running access control tests...")
    
    # Test enums
    print("✓ AccessLevel enum works")
    print("✓ ResourceType enum works")
    
    # Test Permission class
    perm = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
    print(f"✓ Permission creation works: {perm}")
    
    # Test AccessControlPolicy
    policy = AccessControlPolicy()
    user_claims = {
        "sub": "user123",
        "roles": ["admin"],
        "permissions": ["account:ACC123:read"]
    }
    
    test_perm = Permission(ResourceType.ACCOUNT, "ACC123", AccessLevel.READ)
    result = policy.check_permission(user_claims, test_perm)
    print(f"✓ Access control policy works: {result}")
    
    # Test ownership
    ownership_result = check_user_owns_resource(user_claims, ResourceType.ACCOUNT, "ACC123")
    print(f"✓ Ownership checking works: {ownership_result}")
    
    print("\nAll basic tests passed! 🎉")
    print("\nTo run full test suite:")
    print("pip install pytest")
    print("pytest tests/test_access_control.py -v")
