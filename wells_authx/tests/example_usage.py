#!/usr/bin/env python3
"""
Example showing optimized Wells Fargo AuthX usage patterns.
"""

from flask import Flask, jsonify, g
from ..security import get_wells_authenticated_user, require_wells_scope

app = Flask(__name__)

# Example 1: Simple authentication
@app.route("/api/user/profile")
@get_wells_authenticated_user
def get_user_profile():
    """Get user profile - requires authentication only."""
    user = g.current_user
    return jsonify({
        "user_id": user.get('sub'),
        "client_id": user.get('client_id'),
        "email": user.get('email', 'N/A')
    })

# Example 2: Authentication + Scope requirement
@app.route("/api/admin/users")
@get_wells_authenticated_user
@require_wells_scope("admin")
def get_all_users():
    """Get all users - requires authentication + admin scope."""
    return jsonify({
        "message": "Admin access granted",
        "users": ["user1", "user2", "user3"]
    })

# Example 3: Multiple scope requirements
@app.route("/api/data/read")
@get_wells_authenticated_user
@require_wells_scope("read")
def read_data():
    """Read data - requires authentication + read scope."""
    return jsonify({"data": "sensitive data here"})

@app.route("/api/data/write")
@get_wells_authenticated_user
@require_wells_scope("write")
def write_data():
    """Write data - requires authentication + write scope."""
    return jsonify({"message": "Data written successfully"})

# Example 4: Conditional logic based on user claims
@app.route("/api/user/dashboard")
@get_wells_authenticated_user
def user_dashboard():
    """User dashboard with conditional content based on scopes."""
    user = g.current_user
    user_scopes = user.get('scope', [])
    
    dashboard_data = {
        "user_id": user.get('sub'),
        "basic_info": "Welcome to your dashboard"
    }
    
    # Add features based on user's scopes
    if "admin" in user_scopes:
        dashboard_data["admin_panel"] = "Admin features available"
    
    if "read" in user_scopes:
        dashboard_data["data_access"] = "Data reading enabled"
    
    if "write" in user_scopes:
        dashboard_data["data_modification"] = "Data writing enabled"
    
    return jsonify(dashboard_data)

if __name__ == "__main__":
    print("Example Wells Fargo AuthX Flask Application")
    print("=" * 50)
    print("Available endpoints:")
    print("  GET  /api/user/profile     - User profile (auth required)")
    print("  GET  /api/admin/users      - All users (auth + admin scope)")
    print("  GET  /api/data/read        - Read data (auth + read scope)")
    print("  POST /api/data/write       - Write data (auth + write scope)")
    print("  GET  /api/user/dashboard   - Dashboard (auth + conditional features)")
    print("\nTo test with a JWT token:")
    print("  curl -H 'Authorization: Bearer YOUR_JWT_TOKEN' http://localhost:5000/api/user/profile")
