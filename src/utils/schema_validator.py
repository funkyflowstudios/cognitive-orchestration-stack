"""JSON schema validation utilities for safe parsing of LLM responses."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import jsonschema
from jsonschema import ValidationError

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaValidationError(Exception):
    """Raised when JSON schema validation fails."""

    pass


class SafeJSONParser:
    """Safe JSON parser with schema validation."""

    # Schema for planner node response
    PLANNER_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "plan": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "vector_search",
                        "graph_search",
                        "vector_search_async",
                        "graph_search_async",
                    ],
                },
                "minItems": 1,
                "maxItems": 10,
            }
        },
        "required": ["plan"],
        "additionalProperties": False,
    }

    @classmethod
    def validate_planner_response(
        cls, data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Validate and parse planner response with schema validation.

        Args:
            data: The parsed JSON data to validate

        Returns:
            Validated planner response with plan list

        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            # Validate against schema
            jsonschema.validate(data, cls.PLANNER_RESPONSE_SCHEMA)

            # Additional business logic validation
            plan = data.get("plan", [])
            if not plan:
                raise SchemaValidationError("Plan cannot be empty")

            # Validate that all tools in plan are valid
            valid_tools = {
                "vector_search",
                "graph_search",
                "vector_search_async",
                "graph_search_async",
            }
            invalid_tools = set(plan) - valid_tools
            if invalid_tools:
                raise SchemaValidationError(
                    f"Invalid tools in plan: {invalid_tools}"
                )

            return {"plan": plan}

        except ValidationError as e:
            logger.error("Schema validation failed: %s", e.message)
            raise SchemaValidationError(
                f"Schema validation failed: {e.message}"
            )
        except Exception as e:
            logger.error("Unexpected error during validation: %s", str(e))
            raise SchemaValidationError(f"Validation error: {str(e)}")

    @classmethod
    def safe_parse_json(
        cls, json_string: str, schema_type: str = "planner"
    ) -> Dict[str, Any]:
        """
        Safely parse JSON string with schema validation.

        Args:
            json_string: The JSON string to parse
            schema_type: Type of schema to validate against

        Returns:
            Parsed and validated JSON data

        Raises:
            SchemaValidationError: If parsing or validation fails
        """
        try:
            # Parse JSON
            data = json.loads(json_string)

            # Validate based on schema type
            if schema_type == "planner":
                return cls.validate_planner_response(data)
            else:
                # For other schema types, add validation here
                return data

        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            raise SchemaValidationError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error during JSON parsing: %s", str(e))
            raise SchemaValidationError(f"JSON parsing error: {str(e)}")


def sanitize_user_input(user_input: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.

    Args:
        user_input: Raw user input

    Returns:
        Sanitized user input
    """
    if not user_input:
        return ""

    # Remove or escape potentially dangerous characters
    # This is a basic implementation - in production, you might want more
    # sophisticated sanitization
    sanitized = user_input.strip()

    # Remove common prompt injection patterns
    injection_patterns = [
        "ignore previous instructions",
        "forget everything",
        "you are now",
        "pretend to be",
        "act as if",
        "system:",
        "assistant:",
        "user:",
        "human:",
        "ai:",
    ]

    for pattern in injection_patterns:
        if pattern.lower() in sanitized.lower():
            logger.warning("Potential prompt injection detected: %s", pattern)
            # Remove the pattern and everything after it
            sanitized = sanitized[
                : sanitized.lower().find(pattern.lower())
            ].strip()

    # Limit length to prevent extremely long inputs
    max_length = 10000
    if len(sanitized) > max_length:
        logger.warning(
            "User input truncated due to length: %d characters", len(sanitized)
        )
        sanitized = sanitized[:max_length]

    return sanitized
