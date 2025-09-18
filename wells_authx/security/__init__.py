"""Security module for Wells Fargo AuthX Flask application."""

from .container import DependencyContainer, container
from .deps import (
    get_wells_authenticated_user,
    get_wells_apigee_user,
    require_wells_scope,
    get_wells_client_id,
    get_wells_user_id,
    get_wells_user_scopes
)
from .wells_authenticator import WellsAuthenticator
from .access_control import (
    AccessLevel,
    ResourceType,
    Permission,
    AccessControlPolicy,
    access_control_policy,
    require_object_permission,
    require_functional_access,
    check_user_owns_resource,
    require_account_access,
    require_transaction_access,
    require_customer_access,
    require_loan_access,
    require_card_access
)

__all__ = [
    "DependencyContainer",
    "container",
    "get_wells_authenticated_user",
    "get_wells_apigee_user", 
    "require_wells_scope",
    "get_wells_client_id",
    "get_wells_user_id",
    "get_wells_user_scopes",
    "WellsAuthenticator",
    # Access Control
    "AccessLevel",
    "ResourceType", 
    "Permission",
    "AccessControlPolicy",
    "access_control_policy",
    "require_object_permission",
    "require_functional_access",
    "check_user_owns_resource",
    "require_account_access",
    "require_transaction_access",
    "require_customer_access",
    "require_loan_access",
    "require_card_access"
]
