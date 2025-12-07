"""
Unit tests for rule_generator_service.py - Phase 2
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import uuid
from decimal import Decimal

from app.services.rule_generator_service import RuleGeneratorService
from app.models.rule import Rule
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.flush = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def super_admin_user():
    """Mock super admin user."""
    user = Mock(spec=User)
    user.id = uuid.uuid4()
    user.role = "super_admin"
    user.email = "admin@example.com"
    return user


@pytest.fixture
def regular_user():
    """Mock regular user."""
    user = Mock(spec=User)
    user.id = uuid.uuid4()
    user.role = "agent"
    user.email = "user@example.com"
    return user


@pytest.mark.asyncio
class TestRuleGeneratorService:
    """Test cases for RuleGeneratorService."""

    async def test_generate_rules_requires_super_admin(self, mock_db, regular_user):
        """Test that only super_admin can generate rules."""
        service = RuleGeneratorService()

        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user

        result = await service.generate_rules_from_document(
            file_path="/tmp/test.pdf",
            content_type="pdf",
            document_title="Test Document",
            created_by_user_id=regular_user.id,
            db=mock_db
        )

        assert result["success"] is False
        assert "super_admin" in result["errors"][0].lower()

    async def test_generate_rules_parses_document(self, mock_db, super_admin_user):
        """Test that document is parsed correctly."""
        service = RuleGeneratorService()

        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = super_admin_user

        # Mock content parser
        with patch.object(service.parser, 'parse_content', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = "Sample document content for compliance rules"

            # Mock Ollama service
            with patch.object(service.ollama, 'generate_response', new_callable=AsyncMock) as mock_ollama:
                mock_ollama.return_value = '[]'  # Empty rules list

                result = await service.generate_rules_from_document(
                    file_path="/tmp/test.pdf",
                    content_type="pdf",
                    document_title="Test Document",
                    created_by_user_id=super_admin_user.id,
                    db=mock_db
                )

                # Verify parser was called
                mock_parse.assert_called_once_with("/tmp/test.pdf", "pdf")

    async def test_generate_rules_creates_rules_in_db(self, mock_db, super_admin_user):
        """Test that extracted rules are inserted into database."""
        service = RuleGeneratorService()

        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = super_admin_user

        # Mock content parser
        with patch.object(service.parser, 'parse_content', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = "Sample document content"

            # Mock Ollama service with valid rule extraction
            ollama_response = '''
            [
                {
                    "category": "irdai",
                    "rule_text": "No misleading claims about returns",
                    "severity": "critical",
                    "keywords": ["misleading", "returns", "guarantee"],
                    "pattern": null,
                    "points_deduction": -20.00
                },
                {
                    "category": "brand",
                    "rule_text": "Use full company name",
                    "severity": "high",
                    "keywords": ["company", "name", "brand"],
                    "pattern": null,
                    "points_deduction": -10.00
                }
            ]
            '''

            with patch.object(service.ollama, 'generate_response', new_callable=AsyncMock) as mock_ollama:
                mock_ollama.return_value = ollama_response

                result = await service.generate_rules_from_document(
                    file_path="/tmp/test.pdf",
                    content_type="pdf",
                    document_title="Test Document",
                    created_by_user_id=super_admin_user.id,
                    db=mock_db
                )

                # Verify success
                assert result["success"] is True
                assert result["rules_created"] == 2
                assert result["rules_failed"] == 0

                # Verify DB operations
                assert mock_db.add.call_count == 2
                assert mock_db.commit.call_count == 1

    async def test_generate_rules_validates_extracted_rules(self, mock_db, super_admin_user):
        """Test that invalid rules are rejected."""
        service = RuleGeneratorService()

        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = super_admin_user

        # Mock content parser
        with patch.object(service.parser, 'parse_content', new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = "Sample document content"

            # Mock Ollama with invalid rule (positive points_deduction)
            ollama_response = '''
            [
                {
                    "category": "irdai",
                    "rule_text": "Test rule",
                    "severity": "critical",
                    "keywords": ["test"],
                    "pattern": null,
                    "points_deduction": 10.00
                }
            ]
            '''

            with patch.object(service.ollama, 'generate_response', new_callable=AsyncMock) as mock_ollama:
                mock_ollama.return_value = ollama_response

                result = await service.generate_rules_from_document(
                    file_path="/tmp/test.pdf",
                    content_type="pdf",
                    document_title="Test Document",
                    created_by_user_id=super_admin_user.id,
                    db=mock_db
                )

                # Should fail validation
                assert result["rules_created"] == 0
                assert result["rules_failed"] == 1
                assert len(result["errors"]) > 0

    async def test_update_rule_requires_super_admin(self, mock_db, regular_user):
        """Test that only super_admin can update rules."""
        service = RuleGeneratorService()

        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user

        result = await service.regenerate_rule(
            rule_id=uuid.uuid4(),
            new_rule_data={"rule_text": "Updated rule"},
            updated_by_user_id=regular_user.id,
            db=mock_db
        )

        assert result["success"] is False
        assert "super_admin" in result["error"].lower()

    async def test_update_rule_succeeds(self, mock_db, super_admin_user):
        """Test successful rule update."""
        service = RuleGeneratorService()
        rule_id = uuid.uuid4()

        # Mock user and rule query
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            super_admin_user,  # First call for user
            Mock(id=rule_id, rule_text="Old rule", severity="medium")  # Second call for rule
        ]

        result = await service.regenerate_rule(
            rule_id=rule_id,
            new_rule_data={"rule_text": "Updated rule", "severity": "high"},
            updated_by_user_id=super_admin_user.id,
            db=mock_db
        )

        assert result["success"] is True
        assert mock_db.commit.called

    async def test_delete_rule_soft_deletes(self, mock_db, super_admin_user):
        """Test that delete sets is_active to False."""
        service = RuleGeneratorService()
        rule_id = uuid.uuid4()

        # Mock rule
        mock_rule = Mock(id=rule_id, is_active=True)

        # Mock user and rule query
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            super_admin_user,  # First call for user
            mock_rule  # Second call for rule
        ]

        result = await service.delete_rule(
            rule_id=rule_id,
            deleted_by_user_id=super_admin_user.id,
            db=mock_db
        )

        assert result["success"] is True
        assert mock_rule.is_active is False
        assert mock_db.commit.called


# Integration test
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rule_generation_end_to_end():
    """
    Integration test for complete rule generation flow.
    Requires: Running database, Ollama service
    """
    # This would be implemented with actual DB and Ollama service
    # For now, it's a placeholder for future E2E testing
    pass
