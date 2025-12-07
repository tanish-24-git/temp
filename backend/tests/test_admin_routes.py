"""
Integration tests for admin API routes - Phase 2
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import uuid

from app.main import app

# Test client
client = TestClient(app)

# Mock user IDs
SUPER_ADMIN_ID = str(uuid.uuid4())
REGULAR_USER_ID = str(uuid.uuid4())


class TestAdminRoutesAuth:
    """Test authentication and authorization for admin routes."""

    def test_list_rules_requires_auth(self):
        """Test that listing rules requires authentication."""
        response = client.get("/api/admin/rules")
        assert response.status_code == 401
        assert "User ID header" in response.json()["detail"]

    def test_list_rules_requires_super_admin(self):
        """Test that listing rules requires super_admin role."""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = uuid.UUID(REGULAR_USER_ID)
            mock_user.role = "agent"
            mock_get_user.return_value = mock_user

            response = client.get(
                "/api/admin/rules",
                headers={"X-User-Id": REGULAR_USER_ID}
            )
            # Should get 403 Forbidden since user is not super_admin
            assert response.status_code == 403
            assert "super admin" in response.json()["detail"].lower()

    def test_generate_rules_requires_super_admin(self):
        """Test that rule generation requires super_admin role."""
        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = uuid.UUID(REGULAR_USER_ID)
            mock_user.role = "reviewer"
            mock_get_user.return_value = mock_user

            response = client.post(
                "/api/admin/rules/generate",
                headers={"X-User-Id": REGULAR_USER_ID},
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
                data={"document_title": "Test Document"}
            )
            assert response.status_code == 403


class TestAdminRulesEndpoints:
    """Test admin rules CRUD endpoints."""

    @patch("app.api.deps.require_super_admin")
    @patch("app.api.deps.get_db_session")
    def test_list_rules_pagination(self, mock_db, mock_auth):
        """Test rules list with pagination."""
        # Mock super admin
        mock_user = Mock()
        mock_user.id = uuid.UUID(SUPER_ADMIN_ID)
        mock_user.role = "super_admin"
        mock_auth.return_value = mock_user

        # Mock database
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.count.return_value = 50
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        mock_db.return_value.__enter__ = Mock(return_value=mock_db_session)
        mock_db.return_value.__exit__ = Mock(return_value=False)

        response = client.get(
            "/api/admin/rules?page=1&page_size=20",
            headers={"X-User-Id": SUPER_ADMIN_ID}
        )

        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "total" in data
        assert "page" in data

    @patch("app.api.deps.require_super_admin")
    def test_generate_rules_validates_file_type(self, mock_auth):
        """Test that only allowed file types can be uploaded."""
        mock_user = Mock()
        mock_user.id = uuid.UUID(SUPER_ADMIN_ID)
        mock_user.role = "super_admin"
        mock_auth.return_value = mock_user

        # Try to upload invalid file type
        response = client.post(
            "/api/admin/rules/generate",
            headers={"X-User-Id": SUPER_ADMIN_ID},
            files={"file": ("test.exe", b"fake exe", "application/exe")},
            data={"document_title": "Test Document"}
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    @patch("app.api.deps.require_super_admin")
    @patch("app.api.routes.admin.rule_generator_service")
    def test_generate_rules_success(self, mock_service, mock_auth):
        """Test successful rule generation."""
        mock_user = Mock()
        mock_user.id = uuid.UUID(SUPER_ADMIN_ID)
        mock_user.role = "super_admin"
        mock_auth.return_value = mock_user

        # Mock service response
        mock_service.generate_rules_from_document = AsyncMock(return_value={
            "success": True,
            "rules_created": 5,
            "rules_failed": 0,
            "rules": [
                {
                    "id": str(uuid.uuid4()),
                    "category": "irdai",
                    "rule_text": "Test rule",
                    "severity": "high",
                    "points_deduction": -10.00
                }
            ],
            "errors": []
        })

        response = client.post(
            "/api/admin/rules/generate",
            headers={"X-User-Id": SUPER_ADMIN_ID},
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            data={"document_title": "IRDAI Guidelines 2024"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["rules_created"] == 5


class TestRuleFiltering:
    """Test rule filtering and search."""

    @patch("app.api.deps.require_super_admin")
    @patch("app.api.deps.get_db_session")
    def test_filter_by_category(self, mock_db, mock_auth):
        """Test filtering rules by category."""
        mock_user = Mock()
        mock_user.id = uuid.UUID(SUPER_ADMIN_ID)
        mock_user.role = "super_admin"
        mock_auth.return_value = mock_user

        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        mock_db.return_value.__enter__ = Mock(return_value=mock_db_session)
        mock_db.return_value.__exit__ = Mock(return_value=False)

        response = client.get(
            "/api/admin/rules?category=irdai",
            headers={"X-User-Id": SUPER_ADMIN_ID}
        )

        assert response.status_code == 200

    @patch("app.api.deps.require_super_admin")
    @patch("app.api.deps.get_db_session")
    def test_search_rule_text(self, mock_db, mock_auth):
        """Test searching in rule text."""
        mock_user = Mock()
        mock_user.id = uuid.UUID(SUPER_ADMIN_ID)
        mock_user.role = "super_admin"
        mock_auth.return_value = mock_user

        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        mock_db.return_value.__enter__ = Mock(return_value=mock_db_session)
        mock_db.return_value.__exit__ = Mock(return_value=False)

        response = client.get(
            "/api/admin/rules?search=misleading",
            headers={"X-User-Id": SUPER_ADMIN_ID}
        )

        assert response.status_code == 200


class TestRuleStats:
    """Test rule statistics endpoint."""

    @patch("app.api.deps.require_super_admin")
    @patch("app.api.deps.get_db_session")
    def test_get_rule_stats(self, mock_db, mock_auth):
        """Test fetching rule statistics."""
        mock_user = Mock()
        mock_user.id = uuid.UUID(SUPER_ADMIN_ID)
        mock_user.role = "super_admin"
        mock_auth.return_value = mock_user

        mock_db_session = Mock()
        # Mock scalar() for count queries
        mock_db_session.query.return_value.scalar.side_effect = [
            50,  # total
            45,  # active
            15,  # irdai
            20,  # brand
            15,  # seo
            10,  # critical
            15,  # high
            20,  # medium
            5,   # low
        ]
        mock_db.return_value.__enter__ = Mock(return_value=mock_db_session)
        mock_db.return_value.__exit__ = Mock(return_value=False)

        response = client.get(
            "/api/admin/rules/stats/summary",
            headers={"X-User-Id": SUPER_ADMIN_ID}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_rules" in data
        assert "active_rules" in data
        assert "by_category" in data
        assert "by_severity" in data
