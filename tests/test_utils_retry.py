"""Tests for the retry utility module."""

import time

import pytest

from src.utils.retry import retry


class TestRetryDecorator:
    """Test the retry decorator."""

    def test_retry_success_on_first_attempt(self):
        """Test that function succeeds on first attempt without retry."""
        call_count = 0

        @retry
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """Test that function succeeds after some failures."""
        call_count = 0

        @retry
        def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = eventually_successful_function()

        assert result == "success"
        assert call_count == 3

    def test_retry_max_retries_exceeded(self):
        """Test that function raises exception after max retries exceeded."""
        call_count = 0

        @retry
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError) as exc_info:
            always_failing_function()

        assert "Always fails" in str(exc_info.value)
        assert call_count == 3  # Initial attempt + 2 retries

    def test_retry_preserves_function_metadata(self):
        """Test that retry decorator preserves function metadata."""

        @retry
        def test_function():
            """Test function docstring."""
            return "success"

        # Check that function metadata is preserved
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."

    def test_retry_with_args_and_kwargs(self):
        """Test retry with function arguments and keyword arguments."""
        call_count = 0

        @retry
        def function_with_args(arg1, arg2, kwarg1=None, kwarg2=None):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return f"{arg1}-{arg2}-{kwarg1}-{kwarg2}"

        result = function_with_args("a", "b", kwarg1="c", kwarg2="d")

        assert result == "a-b-c-d"
        assert call_count == 3

    def test_retry_with_return_value_preservation(self):
        """Test that retry preserves return value type and content."""

        @retry
        def function_returning_dict():
            return {"key": "value", "number": 42}

        @retry
        def function_returning_list():
            return [1, 2, 3, "test"]

        @retry
        def function_returning_none():
            return None

        dict_result = function_returning_dict()
        list_result = function_returning_list()
        none_result = function_returning_none()

        assert dict_result == {"key": "value", "number": 42}
        assert list_result == [1, 2, 3, "test"]
        assert none_result is None

    def test_retry_multiple_functions_independently(self):
        """Test that multiple retry functions work independently."""
        call_count_1 = 0
        call_count_2 = 0

        @retry
        def function_1():
            nonlocal call_count_1
            call_count_1 += 1
            if call_count_1 < 2:
                raise ValueError("Function 1 failure")
            return "function_1_success"

        @retry
        def function_2():
            nonlocal call_count_2
            call_count_2 += 1
            if call_count_2 < 3:
                raise ValueError("Function 2 failure")
            return "function_2_success"

        result_1 = function_1()
        result_2 = function_2()

        assert result_1 == "function_1_success"
        assert result_2 == "function_2_success"
        assert call_count_1 == 2
        assert call_count_2 == 3

    def test_retry_with_different_exception_types(self):
        """Test retry with different exception types."""
        call_count = 0

        @retry
        def function_with_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Value error")
            elif call_count == 2:
                raise RuntimeError("Runtime error")
            return "success"

        result = function_with_different_exceptions()

        assert result == "success"
        assert call_count == 3

    def test_retry_with_nested_functions(self):
        """Test retry with nested function calls."""
        call_count = 0

        @retry
        def outer_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Outer failure")
            return inner_function()

        @retry
        def inner_function():
            return "inner_success"

        result = outer_function()

        assert result == "inner_success"
        assert call_count == 2

    def test_retry_with_class_methods(self):
        """Test retry with class methods."""
        call_count = 0

        class TestClass:
            @retry
            def test_method(self):
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("Method failure")
                return "method_success"

        obj = TestClass()
        result = obj.test_method()

        assert result == "method_success"
        assert call_count == 2

    def test_retry_with_static_methods(self):
        """Test retry with static methods."""
        call_count = 0

        class TestClass:
            @staticmethod
            @retry
            def static_method():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("Static method failure")
                return "static_success"

        result = TestClass.static_method()

        assert result == "static_success"
        assert call_count == 2

    def test_retry_timing_behavior(self):
        """Test that retry has appropriate timing behavior."""
        call_count = 0
        call_times = []

        @retry
        def function_with_timing():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        start_time = time.time()
        result = function_with_timing()
        total_time = time.time() - start_time

        assert result == "success"
        assert call_count == 3

        # Should take some time due to exponential backoff
        assert total_time > 0.5  # At least 0.5 seconds due to retry delays
        assert total_time < 10.0  # But not too long

    def test_retry_with_lambda_functions(self):
        """Test retry with lambda functions."""
        call_count = 0

        def create_retry_function():
            @retry
            def lambda_function():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("Lambda failure")
                return "lambda_success"

            return lambda_function

        retry_func = create_retry_function()
        result = retry_func()

        assert result == "lambda_success"
        assert call_count == 2
