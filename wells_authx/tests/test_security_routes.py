"""Test file for security implementation in routes."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g

# Mock the service imports to avoid import errors
import sys
from unittest.mock import MagicMock

# Create mock modules
mock_file_service = MagicMock()
mock_jira_service = MagicMock()

# Add to sys.modules
sys.modules['src.services.file_service'] = mock_file_service
sys.modules['src.services.jira_service'] = mock_jira_service

# Mock the service functions
mock_file_service.apigee_proxy_update = Mock(return_value=({"status": "success"}, 200))
mock_jira_service.check_jira = Mock(return_value=({"status": "success"}, 200))
mock_jira_service.handle_ticket = Mock(return_value=({"status": "success"}, 200))
mock_jira_service.get_tickets_by_label_and_component = Mock(return_value=({"status": "success"}, 200))
mock_jira_service.process_ticket_labels = Mock(return_value=({"status": "success"}, 200))

from routes import register_routes


class TestSecurityRoutes:
    """Test security implementation in routes."""
    
    def setup_method(self):
        """Set up test Flask app."""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Register routes
        register_routes(self.app)
    
    def test_health_check_no_auth_required(self):
        """Test that health check endpoint doesn't require authentication."""
        response = self.client.get('/adcs-health/')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['code'] == '200'
        assert data['status'] == 'success'
        assert 'transaction_id' in data
    
    @patch('routes.get_wells_authenticated_user')
    def test_apigee_proxy_update_requires_auth(self, mock_auth):
        """Test that apigee proxy update requires authentication."""
        # Mock authentication failure
        mock_auth.side_effect = Exception("Authentication required")
        
        response = self.client.get('/apigee_proxy_update/TEST-123')
        # Should fail due to authentication
        assert response.status_code != 200
    
    @patch('routes.get_wells_authenticated_user')
    @patch('routes.require_functional_access')
    def test_apigee_proxy_update_with_auth(self, mock_func_auth, mock_auth):
        """Test apigee proxy update with authentication."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        mock_func_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['admin'],
                'functional_permissions': ['apigee_management']
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.get('/apigee_proxy_update/TEST-123')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'transaction_id' in data
            assert 'correlation_id' in data
    
    @patch('routes.get_wells_authenticated_user')
    @patch('routes.require_functional_access')
    def test_jira_ticket_check_with_auth(self, mock_func_auth, mock_auth):
        """Test JIRA ticket check with authentication."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        mock_func_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['developer'],
                'functional_permissions': ['jira_access']
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.get('/check_ticket/TICKET-123')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'transaction_id' in data
            assert 'correlation_id' in data
    
    @patch('routes.get_wells_authenticated_user')
    @patch('routes.require_functional_access')
    @patch('routes.require_wells_scope')
    def test_jira_ticket_handle_with_auth(self, mock_scope_auth, mock_func_auth, mock_auth):
        """Test JIRA ticket handling with authentication and scope."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        mock_func_auth.return_value = lambda f: f
        mock_scope_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['manager'],
                'scope': ['write'],
                'functional_permissions': ['jira_management']
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.post('/jira_ticket', data={'summary': 'Test ticket'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'transaction_id' in data
            assert 'correlation_id' in data
    
    @patch('routes.get_wells_authenticated_user')
    @patch('routes.require_functional_access')
    def test_get_tickets_by_label_with_auth(self, mock_func_auth, mock_auth):
        """Test get tickets by label with authentication."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        mock_func_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['tester'],
                'functional_permissions': ['jira_query']
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.get('/get_tickets_by_label/bug')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'transaction_id' in data
            assert 'correlation_id' in data
    
    @patch('routes.get_wells_authenticated_user')
    @patch('routes.require_functional_access')
    def test_ticket_status_with_auth(self, mock_func_auth, mock_auth):
        """Test ticket status processing with authentication."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        mock_func_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['developer'],
                'functional_permissions': ['jira_status']
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.get('/ticket_current_status/TICKET-123')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'transaction_id' in data
            assert 'correlation_id' in data
    
    @patch('routes.get_wells_authenticated_user')
    def test_user_permissions_endpoint(self, mock_auth):
        """Test user permissions endpoint."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['admin'],
                'scope': ['read', 'write'],
                'functional_permissions': ['jira_management'],
                'department': 'IT'
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.get('/user/permissions')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['code'] == '200'
            assert data['status'] == 'success'
            assert 'permissions' in data
            assert data['permissions']['user_id'] == 'test@wellsfargo.com'
            assert 'admin' in data['permissions']['roles']
    
    @patch('routes.get_wells_authenticated_user')
    def test_permission_test_endpoint(self, mock_auth):
        """Test permission testing endpoint."""
        # Mock successful authentication
        mock_auth.return_value = lambda f: f
        
        # Mock g.current_user
        with self.app.test_request_context():
            g.current_user = {
                'sub': 'test@wellsfargo.com',
                'roles': ['admin'],
                'permissions': ['account:ACC123:read']
            }
            g.correlation_id = 'test-correlation-id'
            
            response = self.client.post('/security/test-permission', 
                                      json={
                                          'resource_type': 'account',
                                          'resource_id': 'ACC123',
                                          'access_level': 'read'
                                      })
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['code'] == '200'
            assert data['status'] == 'success'
            assert 'has_permission' in data


def main():
    """Run basic security route tests."""
    print("Running security route tests...")
    
    # Test basic functionality
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Mock the service modules
    with patch.dict('sys.modules', {
        'src.services.file_service': mock_file_service,
        'src.services.jira_service': mock_jira_service
    }):
        register_routes(app)
        print("✓ Routes registered successfully")
    
    # Test health check
    with app.test_client() as client:
        response = client.get('/adcs-health/')
        if response.status_code == 200:
            print("✓ Health check endpoint works")
        else:
            print(f"✗ Health check failed: {response.status_code}")
    
    print("\nSecurity route tests completed! 🎉")
    print("\nTo run full test suite:")
    print("pip install pytest")
    print("pytest tests/test_security_routes.py -v")


if __name__ == "__main__":
    main()
