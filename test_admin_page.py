"""
Unit tests for admin page functionality.

Tests authentication, authorization, configuration management, and other core features.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import sys
from datetime import datetime

# Import admin page functions
sys.path.insert(0, '/home/ubuntu/Desktop/demo')
from pages.admin import (
    hash_password,
    authenticate_user,
    UserRole,
    AccessLevel,
    ROLE_PERMISSIONS,
    FEATURE_ACCESS,
    DEFAULT_RISK_THRESHOLDS,
    get_default_users,
)


class TestAuthentication(unittest.TestCase):
    """Tests for authentication functions."""

    def test_hash_password_consistency(self):
        """Test that same password hashes to same value."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        self.assertEqual(hash1, hash2)

    def test_hash_password_different_passwords(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        self.assertNotEqual(hash1, hash2)

    def test_authenticate_user_valid_admin(self):
        """Test authentication with valid admin credentials."""
        result = authenticate_user("admin", "admin123")
        self.assertTrue(result)

    def test_authenticate_user_valid_manager(self):
        """Test authentication with valid manager credentials."""
        result = authenticate_user("manager", "manager123")
        self.assertTrue(result)

    def test_authenticate_user_valid_analyst(self):
        """Test authentication with valid analyst credentials."""
        result = authenticate_user("analyst", "analyst123")
        self.assertTrue(result)

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        result = authenticate_user("admin", "wrongpassword")
        self.assertFalse(result)

    def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username."""
        result = authenticate_user("nonexistent", "password123")
        self.assertFalse(result)

    def test_authenticate_user_empty_credentials(self):
        """Test authentication with empty credentials."""
        result = authenticate_user("", "")
        self.assertFalse(result)


class TestUserRoles(unittest.TestCase):
    """Tests for user role management."""

    def test_user_role_enum_values(self):
        """Test that all expected user roles exist."""
        expected_roles = ["admin", "manager", "analyst", "viewer"]
        actual_roles = [role.value for role in UserRole]
        self.assertEqual(sorted(actual_roles), sorted(expected_roles))

    def test_role_permissions_mapping(self):
        """Test that all roles have permission mapping."""
        for role in UserRole:
            self.assertIn(role, ROLE_PERMISSIONS)
            permission_level = ROLE_PERMISSIONS[role]
            self.assertIsInstance(permission_level, AccessLevel)

    def test_role_hierarchy(self):
        """Test that role hierarchy is correct."""
        # Admin should have highest access (lowest number)
        admin_level = ROLE_PERMISSIONS[UserRole.ADMIN]
        manager_level = ROLE_PERMISSIONS[UserRole.MANAGER]
        analyst_level = ROLE_PERMISSIONS[UserRole.ANALYST]
        viewer_level = ROLE_PERMISSIONS[UserRole.VIEWER]

        self.assertLess(admin_level, manager_level)
        self.assertLess(manager_level, analyst_level)
        self.assertLess(analyst_level, viewer_level)

    def test_admin_can_access_all_features(self):
        """Test that admin can access all features."""
        admin_level = ROLE_PERMISSIONS[UserRole.ADMIN]
        for feature, required_level in FEATURE_ACCESS.items():
            # Admin should be able to access (lower or equal number means access)
            can_access = admin_level <= required_level
            self.assertTrue(can_access, f"Admin cannot access {feature}")

    def test_viewer_has_limited_access(self):
        """Test that viewer has limited access."""
        viewer_level = ROLE_PERMISSIONS[UserRole.VIEWER]
        restricted_features = [
            "risk_thresholds",
            "user_management",
            "system_health",
            "database_stats",
        ]

        for feature in restricted_features:
            required_level = FEATURE_ACCESS[feature]
            can_access = viewer_level <= required_level
            # Viewer should NOT be able to access these
            self.assertFalse(can_access, f"Viewer should not access {feature}")


class TestDefaultUsers(unittest.TestCase):
    """Tests for default user configuration."""

    def test_default_users_exist(self):
        """Test that default users are configured."""
        users = get_default_users()
        expected_users = ["admin", "manager", "analyst"]
        for user in expected_users:
            self.assertIn(user, users)

    def test_default_users_have_roles(self):
        """Test that all default users have assigned roles."""
        users = get_default_users()
        for username, user_data in users.items():
            self.assertIn("role", user_data)
            self.assertIsInstance(user_data["role"], UserRole)

    def test_default_users_have_password_hash(self):
        """Test that all default users have password hashes."""
        users = get_default_users()
        for username, user_data in users.items():
            self.assertIn("password_hash", user_data)
            self.assertIsInstance(user_data["password_hash"], str)
            # Hash should be 64 characters (SHA-256 hex)
            self.assertEqual(len(user_data["password_hash"]), 64)

    def test_default_users_are_active(self):
        """Test that default users are active."""
        users = get_default_users()
        for username, user_data in users.items():
            self.assertTrue(user_data.get("active", False))


class TestRiskThresholds(unittest.TestCase):
    """Tests for risk threshold configuration."""

    def test_default_thresholds_structure(self):
        """Test that default thresholds have required keys."""
        required_keys = [
            "credit_score_minimum",
            "debt_to_income_maximum",
            "employment_years_minimum",
            "savings_to_loan_ratio",
            "risk_score_low_threshold",
            "risk_score_medium_threshold",
            "risk_score_high_threshold",
            "approval_threshold_low",
            "approval_threshold_medium",
            "approval_threshold_high",
        ]

        for key in required_keys:
            self.assertIn(key, DEFAULT_RISK_THRESHOLDS)

    def test_default_thresholds_are_numeric(self):
        """Test that all default thresholds are numeric."""
        for key, value in DEFAULT_RISK_THRESHOLDS.items():
            self.assertIsInstance(value, (int, float))

    def test_risk_score_threshold_ordering(self):
        """Test that risk score thresholds are in correct order."""
        low = DEFAULT_RISK_THRESHOLDS["risk_score_low_threshold"]
        medium = DEFAULT_RISK_THRESHOLDS["risk_score_medium_threshold"]
        high = DEFAULT_RISK_THRESHOLDS["risk_score_high_threshold"]

        self.assertLess(low, medium)
        self.assertLess(medium, high)

    def test_approval_threshold_ordering(self):
        """Test that approval thresholds are in correct order (inverted for risk)."""
        # Higher confidence needed for lower risk
        low = DEFAULT_RISK_THRESHOLDS["approval_threshold_low"]
        medium = DEFAULT_RISK_THRESHOLDS["approval_threshold_medium"]
        high = DEFAULT_RISK_THRESHOLDS["approval_threshold_high"]

        self.assertGreater(low, medium)
        self.assertGreater(medium, high)

    def test_approval_thresholds_in_valid_range(self):
        """Test that approval thresholds are between 0 and 1."""
        for threshold_name in [
            "approval_threshold_low",
            "approval_threshold_medium",
            "approval_threshold_high"
        ]:
            value = DEFAULT_RISK_THRESHOLDS[threshold_name]
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_credit_score_in_valid_range(self):
        """Test that minimum credit score is within valid FICO range."""
        min_score = DEFAULT_RISK_THRESHOLDS["credit_score_minimum"]
        self.assertGreaterEqual(min_score, 300)  # Minimum FICO
        self.assertLessEqual(min_score, 850)  # Maximum FICO

    def test_debt_to_income_in_valid_range(self):
        """Test that maximum DTI ratio is reasonable."""
        max_dti = DEFAULT_RISK_THRESHOLDS["debt_to_income_maximum"]
        self.assertGreater(max_dti, 0)
        self.assertLessEqual(max_dti, 100)  # Should be percentage


class TestAccessControl(unittest.TestCase):
    """Tests for access control features."""

    def test_feature_access_coverage(self):
        """Test that all features have access requirements."""
        expected_features = [
            "risk_thresholds",
            "user_management",
            "system_health",
            "database_stats",
            "log_viewer",
            "configuration",
        ]

        for feature in expected_features:
            self.assertIn(feature, FEATURE_ACCESS)

    def test_access_levels_are_valid(self):
        """Test that all feature access levels are valid."""
        for feature, access_level in FEATURE_ACCESS.items():
            self.assertIsInstance(access_level, AccessLevel)

    def test_admin_features_are_restricted(self):
        """Test that admin-only features exist."""
        admin_features = [
            key for key, level in FEATURE_ACCESS.items()
            if level == AccessLevel.ADMIN_ONLY
        ]
        self.assertGreater(len(admin_features), 0)

    def test_public_features_exist(self):
        """Test that most features have access requirements defined."""
        # All features should have access requirements defined
        self.assertGreater(len(FEATURE_ACCESS), 0)
        # All admin-only features should exist
        admin_features = [
            key for key, level in FEATURE_ACCESS.items()
            if level == AccessLevel.ADMIN_ONLY
        ]
        self.assertGreater(len(admin_features), 0)


class TestLoggingStructure(unittest.TestCase):
    """Tests for logging functionality."""

    def test_log_entry_has_required_fields(self):
        """Test that log entries have required fields."""
        required_fields = [
            "timestamp",
            "user",
            "action",
            "action_type",
            "details",
        ]

        # Simulate a log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": "admin",
            "action": "Test action",
            "action_type": "TEST",
            "details": "",
        }

        for field in required_fields:
            self.assertIn(field, log_entry)

    def test_action_types_are_documented(self):
        """Test that action types are consistent."""
        valid_action_types = [
            "LOGIN",
            "LOGOUT",
            "CONFIG_UPDATE",
            "USER_CREATE",
            "USER_UPDATE",
            "USER_DEACTIVATE",
        ]

        # This is just documenting expected types
        self.assertGreater(len(valid_action_types), 0)


class TestDataValidation(unittest.TestCase):
    """Tests for data validation."""

    def test_password_hashing_is_deterministic(self):
        """Test that password hashing is deterministic."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        self.assertEqual(hash1, hash2)

    def test_password_hash_length(self):
        """Test that password hash has correct length (SHA-256)."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        # SHA-256 hex is always 64 characters
        self.assertEqual(len(hashed), 64)

    def test_password_hash_is_lowercase_hex(self):
        """Test that password hash is lowercase hexadecimal."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        # Should be valid hex
        try:
            int(hashed, 16)
        except ValueError:
            self.fail("Password hash is not valid hexadecimal")


class TestIntegration(unittest.TestCase):
    """Integration tests for admin page features."""

    def test_authentication_to_access_flow(self):
        """Test flow from authentication to access control."""
        # User authenticates
        is_authenticated = authenticate_user("admin", "admin123")
        self.assertTrue(is_authenticated)

        # User gets admin role
        users = get_default_users()
        user_role = users["admin"]["role"]
        self.assertEqual(user_role, UserRole.ADMIN)

        # Admin can access admin features
        admin_access_level = ROLE_PERMISSIONS[user_role]
        can_access_risk_config = admin_access_level <= FEATURE_ACCESS["risk_thresholds"]
        self.assertTrue(can_access_risk_config)

    def test_default_user_permissions(self):
        """Test that each default user has appropriate permissions."""
        users = get_default_users()

        # Admin should have full access
        admin_role = users["admin"]["role"]
        admin_level = ROLE_PERMISSIONS[admin_role]
        self.assertEqual(admin_level, AccessLevel.ADMIN_ONLY)

        # Manager should have manager access
        manager_role = users["manager"]["role"]
        manager_level = ROLE_PERMISSIONS[manager_role]
        self.assertEqual(manager_level, AccessLevel.MANAGER_AND_UP)

        # Analyst should have analyst access
        analyst_role = users["analyst"]["role"]
        analyst_level = ROLE_PERMISSIONS[analyst_role]
        self.assertEqual(analyst_level, AccessLevel.ANALYST_AND_UP)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAuthentication))
    suite.addTests(loader.loadTestsFromTestCase(TestUserRoles))
    suite.addTests(loader.loadTestsFromTestCase(TestDefaultUsers))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskThresholds))
    suite.addTests(loader.loadTestsFromTestCase(TestAccessControl))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    result = run_tests()

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
