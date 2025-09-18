"""Wells Fargo AuthX routes with comprehensive security features."""

import uuid
import logging
from flask import request, jsonify, g
from typing import Dict, Any

from security import (
    get_wells_authenticated_user,
    require_wells_scope,
    require_object_permission,
    require_functional_access,
    AccessLevel,
    ResourceType
)

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all routes with the Flask application."""
    
    # ============================================================================
    # HEALTH CHECK ENDPOINT (No authentication required)
    # ============================================================================
    
    @app.route("/adcs-health/", methods=["GET"])
    def health_check():
        """Health check endpoint - no authentication required."""
        transaction_id = str(uuid.uuid4())
        correlation_id = getattr(g, 'correlation_id', transaction_id)
        
        app.logger.info(f"Transaction ID: {transaction_id} - Health check endpoint called")
        logger.info(
            "Health check endpoint accessed",
            extra={
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "endpoint": "/adcs-health/"
            }
        )
        
        return jsonify({
            "code": "200",
            "status": "success",
            "message": "This Server Is Healthy",
            "transaction_id": transaction_id,
            "correlation_id": correlation_id
        }), 200

    # ============================================================================
    # APIGEE PROXY UPDATE ENDPOINT
    # ============================================================================
    
    @app.route("/apigee_proxy_update/<issue_key>", methods=["GET"])
    @get_wells_authenticated_user
    @require_functional_access("apigee_management", ["admin", "manager", "developer"])
    def apigee_proxy_update_route(issue_key: str):
        """
        Apigee proxy update endpoint.
        Requires authentication and functional access to 'apigee_management'.
        """
        transaction_id = str(uuid.uuid4())
        correlation_id = getattr(g, 'correlation_id', transaction_id)
        current_user = g.current_user
        
        app.logger.info(
            f"Transaction ID: {transaction_id} - apigee_proxy_update called with issue_key: {issue_key}"
        )
        
        logger.info(
            "Apigee proxy update requested",
            extra={
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "issue_key": issue_key,
                "user_sub": current_user.get('sub'),
                "user_roles": current_user.get('roles', []),
                "endpoint": "/apigee_proxy_update"
            }
        )
        
        try:
            # Import the service function
            from src.services.file_service import apigee_proxy_update
            
            response, status_code = apigee_proxy_update(transaction_id, issue_key)
            
            # Add security context to response
            if isinstance(response, dict):
                response.update({
                    "transaction_id": transaction_id,
                    "correlation_id": correlation_id,
                    "user_id": current_user.get('sub'),
                    "access_granted": True
                })
            
            return jsonify(response), status_code
            
        except ImportError as e:
            logger.error(f"Failed to import apigee_proxy_update service: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Service unavailable",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500
        except Exception as e:
            logger.error(f"Error in apigee_proxy_update: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Internal server error",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500

    # ============================================================================
    # JIRA TICKET CHECK ENDPOINT
    # ============================================================================
    
    @app.route("/check_ticket/<issue_key>", methods=["GET"])
    @get_wells_authenticated_user
    @require_functional_access("jira_access", ["admin", "manager", "developer", "tester"])
    def check_jira_route(issue_key: str):
        """
        Check JIRA ticket endpoint.
        Requires authentication and functional access to 'jira_access'.
        """
        transaction_id = str(uuid.uuid4())
        correlation_id = getattr(g, 'correlation_id', transaction_id)
        current_user = g.current_user
        
        app.logger.info(
            f"Transaction ID: {transaction_id} - check_jira called with issue_key: {issue_key}"
        )
        
        logger.info(
            "JIRA ticket check requested",
            extra={
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "issue_key": issue_key,
                "user_sub": current_user.get('sub'),
                "user_roles": current_user.get('roles', []),
                "endpoint": "/check_ticket"
            }
        )
        
        try:
            # Import the service function
            from src.services.jira_service import check_jira
            
            response, status_code = check_jira(transaction_id, issue_key)
            
            # Add security context to response
            if isinstance(response, dict):
                response.update({
                    "transaction_id": transaction_id,
                    "correlation_id": correlation_id,
                    "user_id": current_user.get('sub'),
                    "access_granted": True
                })
            
            return jsonify(response), status_code
            
        except ImportError as e:
            logger.error(f"Failed to import check_jira service: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Service unavailable",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500
        except Exception as e:
            logger.error(f"Error in check_jira: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Internal server error",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500

    # ============================================================================
    # JIRA TICKET HANDLING ENDPOINT
    # ============================================================================
    
    @app.route("/jira_ticket", methods=["POST"])
    @get_wells_authenticated_user
    @require_functional_access("jira_management", ["admin", "manager", "developer"])
    @require_wells_scope("write")
    def handle_ticket_route():
        """
        Handle JIRA ticket endpoint.
        Requires authentication, functional access to 'jira_management', and 'write' scope.
        """
        transaction_id = str(uuid.uuid4())
        correlation_id = getattr(g, 'correlation_id', transaction_id)
        current_user = g.current_user
        
        app.logger.info(f"Transaction ID: {transaction_id} - handle_ticket called")
        
        logger.info(
            "JIRA ticket handling requested",
            extra={
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "user_sub": current_user.get('sub'),
                "user_roles": current_user.get('roles', []),
                "user_scopes": current_user.get('scope', []),
                "endpoint": "/jira_ticket"
            }
        )
        
        try:
            # Import the service function
            from src.services.jira_service import handle_ticket
            
            form_data = request.form
            files = request.files
            
            # Log file upload details (without sensitive content)
            file_info = []
            for filename, file in files.items():
                file_info.append({
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(file.read()) if hasattr(file, 'read') else 0
                })
                file.seek(0)  # Reset file pointer
            
            logger.info(
                "JIRA ticket processing started",
                extra={
                    "correlation_id": correlation_id,
                    "transaction_id": transaction_id,
                    "form_fields": list(form_data.keys()),
                    "files": file_info,
                    "user_sub": current_user.get('sub')
                }
            )
            
            response, status_code = handle_ticket(transaction_id, form_data, files)
            
            # Add security context to response
            if isinstance(response, dict):
                response.update({
                    "transaction_id": transaction_id,
                    "correlation_id": correlation_id,
                    "user_id": current_user.get('sub'),
                    "access_granted": True
                })
            
            return jsonify(response), status_code
            
        except ImportError as e:
            logger.error(f"Failed to import handle_ticket service: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Service unavailable",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500
        except Exception as e:
            logger.error(f"Error in handle_ticket: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Internal server error",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500

    # ============================================================================
    # GET TICKETS BY LABEL ENDPOINT
    # ============================================================================
    
    @app.route("/get_tickets_by_label/<label>", methods=["GET"])
    @get_wells_authenticated_user
    @require_functional_access("jira_query", ["admin", "manager", "developer", "tester", "customer_service"])
    def get_tickets_by_label_route(label: str):
        """
        Get tickets by label endpoint.
        Requires authentication and functional access to 'jira_query'.
        """
        transaction_id = str(uuid.uuid4())
        correlation_id = getattr(g, 'correlation_id', transaction_id)
        current_user = g.current_user
        
        app.logger.info(
            f"Transaction ID: {transaction_id} - get_tickets_by_label called with label: {label}"
        )
        
        logger.info(
            "JIRA tickets query requested",
            extra={
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "label": label,
                "user_sub": current_user.get('sub'),
                "user_roles": current_user.get('roles', []),
                "endpoint": "/get_tickets_by_label"
            }
        )
        
        try:
            # Import the service function
            from src.services.jira_service import get_tickets_by_label_and_component
            
            query_params = request.args.to_dict()
            
            logger.info(
                "JIRA tickets query processing",
                extra={
                    "correlation_id": correlation_id,
                    "transaction_id": transaction_id,
                    "label": label,
                    "query_params": query_params,
                    "user_sub": current_user.get('sub')
                }
            )
            
            response, status_code = get_tickets_by_label_and_component(transaction_id, label, query_params)
            
            # Add security context to response
            if isinstance(response, dict):
                response.update({
                    "transaction_id": transaction_id,
                    "correlation_id": correlation_id,
                    "user_id": current_user.get('sub'),
                    "access_granted": True
                })
            
            return jsonify(response), status_code
            
        except ImportError as e:
            logger.error(f"Failed to import get_tickets_by_label_and_component service: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Service unavailable",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500
        except Exception as e:
            logger.error(f"Error in get_tickets_by_label_and_component: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Internal server error",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500

    # ============================================================================
    # TICKET STATUS PROCESSING ENDPOINT
    # ============================================================================
    
    @app.route("/ticket_current_status/<ticket_id>", methods=["GET"])
    @get_wells_authenticated_user
    @require_functional_access("jira_status", ["admin", "manager", "developer", "tester"])
    def process_ticket_labels_route(ticket_id: str):
        """
        Process ticket labels/status endpoint.
        Requires authentication and functional access to 'jira_status'.
        """
        transaction_id = str(uuid.uuid4())
        correlation_id = getattr(g, 'correlation_id', transaction_id)
        current_user = g.current_user
        
        app.logger.info(
            f"Transaction ID: {transaction_id} - process_ticket_labels called with ticket_id: {ticket_id}"
        )
        
        logger.info(
            "JIRA ticket status processing requested",
            extra={
                "correlation_id": correlation_id,
                "transaction_id": transaction_id,
                "ticket_id": ticket_id,
                "user_sub": current_user.get('sub'),
                "user_roles": current_user.get('roles', []),
                "endpoint": "/ticket_current_status"
            }
        )
        
        try:
            # Import the service function
            from src.services.jira_service import process_ticket_labels
            
            response, status_code = process_ticket_labels(transaction_id, ticket_id)
            
            # Add security context to response
            if isinstance(response, dict):
                response.update({
                    "transaction_id": transaction_id,
                    "correlation_id": correlation_id,
                    "user_id": current_user.get('sub'),
                    "access_granted": True
                })
            
            return jsonify(response), status_code
            
        except ImportError as e:
            logger.error(f"Failed to import process_ticket_labels service: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Service unavailable",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500
        except Exception as e:
            logger.error(f"Error in process_ticket_labels: {e}")
            return jsonify({
                "code": "500",
                "status": "error",
                "error_message": "Internal server error",
                "transaction_id": transaction_id,
                "correlation_id": correlation_id
            }), 500

    # ============================================================================
    # ADDITIONAL SECURITY ENDPOINTS
    # ============================================================================
    
    @app.route("/user/permissions", methods=["GET"])
    @get_wells_authenticated_user
    def get_user_permissions():
        """Get current user's permissions and access information."""
        current_user = g.current_user
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        
        # Extract permission information
        permissions_info = {
            "user_id": current_user.get('sub'),
            "client_id": current_user.get('client_id'),
            "roles": current_user.get('roles', []),
            "scopes": current_user.get('scope', []),
            "permissions": current_user.get('permissions', []),
            "resource_permissions": current_user.get('resource_permissions', []),
            "functional_permissions": current_user.get('functional_permissions', []),
            "department": current_user.get('department'),
            "correlation_id": correlation_id
        }
        
        logger.info(
            "User permissions requested",
            extra={
                "correlation_id": correlation_id,
                "user_sub": current_user.get('sub'),
                "user_roles": current_user.get('roles', [])
            }
        )
        
        return jsonify({
            "code": "200",
            "status": "success",
            "message": "User permissions retrieved",
            "permissions": permissions_info
        })

    @app.route("/security/test-permission", methods=["POST"])
    @get_wells_authenticated_user
    def test_permission():
        """Test a specific permission for the current user."""
        current_user = g.current_user
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        test_data = request.get_json() or {}
        
        resource_type = test_data.get('resource_type')
        resource_id = test_data.get('resource_id')
        access_level = test_data.get('access_level')
        
        if not all([resource_type, resource_id, access_level]):
            return jsonify({
                "code": "400",
                "status": "error",
                "error_message": "Missing required fields: resource_type, resource_id, access_level",
                "correlation_id": correlation_id
            }), 400
        
        try:
            from security import Permission, access_control_policy
            
            # Create permission object
            permission = Permission(
                ResourceType(resource_type),
                resource_id,
                AccessLevel(access_level)
            )
            
            # Test permission
            has_permission = access_control_policy.check_permission(current_user, permission)
            
            logger.info(
                "Permission test completed",
                extra={
                    "correlation_id": correlation_id,
                    "user_sub": current_user.get('sub'),
                    "permission": str(permission),
                    "has_permission": has_permission
                }
            )
            
            return jsonify({
                "code": "200",
                "status": "success",
                "message": "Permission test completed",
                "permission": str(permission),
                "has_permission": has_permission,
                "user_id": current_user.get('sub'),
                "correlation_id": correlation_id
            })
            
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid permission parameters: {e}")
            return jsonify({
                "code": "400",
                "status": "error",
                "error_message": f"Invalid permission parameters: {str(e)}",
                "correlation_id": correlation_id
            }), 400