"""Tests for the schema validator module."""

import json
import pytest
from unittest.mock import patch

from src.utils.schema_validator import (
    SafeJSONParser,
    SchemaValidationError,
    sanitize_user_input,
)


class TestSafeJSONParser:
    """Test the SafeJSONParser class."""

    def test_safe_parse_json_valid_json(self):
        """Test parsing valid JSON."""
        valid_json = '{"plan": ["vector_search", "graph_search"]}'
        result = SafeJSONParser.safe_parse_json(valid_json, "planner")

        assert result["plan"] == ["vector_search", "graph_search"]

    def test_safe_parse_json_invalid_json(self):
        """Test parsing invalid JSON raises SchemaValidationError."""
        invalid_json = '{"plan": ["vector_search", "graph_search"'  # Missing closing brace

        with pytest.raises(SchemaValidationError) as exc_info:
            SafeJSONParser.safe_parse_json(invalid_json, "planner")

        assert "Invalid JSON" in str(exc_info.value)

    def test_safe_parse_json_empty_string(self):
        """Test parsing empty string raises SchemaValidationError."""
        with pytest.raises(SchemaValidationError) as exc_info:
            SafeJSONParser.safe_parse_json("", "planner")

        assert "Invalid JSON" in str(exc_info.value)

    def test_safe_parse_json_none_input(self):
        """Test parsing None input raises SchemaValidationError."""
        with pytest.raises(SchemaValidationError) as exc_info:
            SafeJSONParser.safe_parse_json(None, "planner")

        assert "Invalid JSON" in str(exc_info.value)

    def test_safe_parse_json_non_string_input(self):
        """Test parsing non-string input raises SchemaValidationError."""
        with pytest.raises(SchemaValidationError) as exc_info:
            SafeJSONParser.safe_parse_json(123, "planner")

        assert "Invalid JSON" in str(exc_info.value)

    def test_safe_parse_json_with_planner_schema(self):
        """Test parsing with planner schema validation."""
        valid_planner_json = '{"plan": ["vector_search"]}'
        result = SafeJSONParser.safe_parse_json(valid_planner_json, "planner")

        assert "plan" in result
        assert isinstance(result["plan"], list)

    def test_safe_parse_json_planner_schema_validation_failure(self):
        """Test planner schema validation failure."""
        invalid_planner_json = '{"invalid_field": "value"}'

        with pytest.raises(SchemaValidationError) as exc_info:
            SafeJSONParser.safe_parse_json(invalid_planner_json, "planner")

        assert "Schema validation failed" in str(exc_info.value)

    def test_safe_parse_json_unknown_schema_type(self):
        """Test parsing with unknown schema type."""
        valid_json = '{"data": "value"}'
        result = SafeJSONParser.safe_parse_json(valid_json, "unknown")

        # Should return the parsed JSON without additional validation
        assert result["data"] == "value"

    def test_safe_parse_json_malformed_json_with_extra_text(self):
        """Test parsing JSON with extra text."""
        malformed_json = '{"plan": ["vector_search"]} extra text'

        with pytest.raises(SchemaValidationError) as exc_info:
            SafeJSONParser.safe_parse_json(malformed_json, "planner")

        assert "Invalid JSON" in str(exc_info.value)

    def test_safe_parse_json_unicode_characters(self):
        """Test parsing JSON with unicode characters."""
        unicode_json = '{"plan": ["vector_search"], "description": "Test with émojis 🚀"}'
        result = SafeJSONParser.safe_parse_json(unicode_json, "planner")

        assert result["plan"] == ["vector_search"]
        assert "émojis 🚀" in result["description"]


class TestSchemaValidationError:
    """Test the SchemaValidationError exception."""

    def test_schema_validation_error_creation(self):
        """Test creating SchemaValidationError."""
        error = SchemaValidationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_schema_validation_error_inheritance(self):
        """Test SchemaValidationError inheritance."""
        error = SchemaValidationError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, ValueError)


class TestSanitizeUserInput:
    """Test the sanitize_user_input function."""

    def test_sanitize_user_input_normal_text(self):
        """Test sanitizing normal text."""
        input_text = "What are the key features of Ableton Live?"
        result = sanitize_user_input(input_text)

        assert result == input_text

    def test_sanitize_user_input_with_special_characters(self):
        """Test sanitizing text with special characters."""
        input_text = "Test with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = sanitize_user_input(input_text)

        # Should return the same text (no actual sanitization implemented)
        assert result == input_text

    def test_sanitize_user_input_empty_string(self):
        """Test sanitizing empty string."""
        result = sanitize_user_input("")
        assert result == ""

    def test_sanitize_user_input_whitespace(self):
        """Test sanitizing text with whitespace."""
        input_text = "  \t\n  Test with whitespace  \t\n  "
        result = sanitize_user_input(input_text)

        # Should return the same text (no trimming implemented)
        assert result == input_text

    def test_sanitize_user_input_unicode(self):
        """Test sanitizing unicode text."""
        input_text = "Test with unicode: émojis 🚀 and ñ characters"
        result = sanitize_user_input(input_text)

        assert result == input_text

    def test_sanitize_user_input_none(self):
        """Test sanitizing None input."""
        result = sanitize_user_input(None)
        assert result is None


class TestIntegrationScenarios:
    """Test integration scenarios for schema validation."""

    def test_complete_planner_workflow(self):
        """Test complete planner workflow with schema validation."""
        # Simulate LLM response
        llm_response = '{"plan": ["vector_search", "graph_search", "neo4j_query"]}'

        # Parse and validate
        parsed_data = SafeJSONParser.safe_parse_json(llm_response, "planner")

        assert parsed_data["plan"] == ["vector_search", "graph_search", "neo4j_query"]

    def test_error_handling_chain(self):
        """Test error handling through the validation chain."""
        # Test with invalid JSON
        with pytest.raises(SchemaValidationError):
            SafeJSONParser.safe_parse_json("invalid json", "planner")

        # Test with valid JSON but invalid schema
        valid_json = '{"invalid_field": "value"}'
        parsed_data = SafeJSONParser.safe_parse_json(valid_json, "planner")

        # Should still work since we're not doing strict validation
        assert parsed_data["invalid_field"] == "value"