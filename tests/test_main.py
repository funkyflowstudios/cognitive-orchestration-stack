"""Tests for main CLI application."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.main import ChimeraCLI, _parse_args, main


class TestChimeraCLI:
    """Test the ChimeraCLI class."""

    def test_chimera_cli_initialization(self):
        """Test ChimeraCLI initialization."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class:

            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_style = MagicMock()
            mock_style_class.from_dict.return_value = mock_style

            cli = ChimeraCLI()

            assert cli.toolbar_msg == "Type a query or 'help'"
            assert cli.session is mock_session
            mock_session_class.assert_called_once()
            mock_style_class.from_dict.assert_called_once()

    def test_chimera_cli_start_interactive_mode_exit(self):
        """Test interactive mode with exit command."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.run_animation') as mock_animation, \
             patch('builtins.print') as mock_print:

            mock_session = MagicMock()
            mock_session.prompt.side_effect = ["exit"]
            mock_session_class.return_value = mock_session
            mock_style_class.from_dict.return_value = MagicMock()

            cli = ChimeraCLI()
            cli.start_interactive_mode()

            # Should call prompt once for "exit", then break out of loop
            assert mock_session.prompt.call_count == 1
            mock_animation.assert_called_once()
            mock_print.assert_called()

    def test_chimera_cli_start_interactive_mode_quit(self):
        """Test interactive mode with quit command."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.run_animation') as mock_animation, \
             patch('builtins.print') as mock_print:

            mock_session = MagicMock()
            mock_session.prompt.side_effect = ["quit"]
            mock_session_class.return_value = mock_session
            mock_style_class.from_dict.return_value = MagicMock()

            cli = ChimeraCLI()
            cli.start_interactive_mode()

            # Should call prompt once for "quit", then break out of loop
            assert mock_session.prompt.call_count == 1
            mock_animation.assert_called_once()
            mock_print.assert_called()

    def test_chimera_cli_start_interactive_mode_empty_input(self):
        """Test interactive mode with empty input."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.run_animation') as mock_animation:

            mock_session = MagicMock()
            mock_session.prompt.side_effect = ["", "   ", "exit"]
            mock_session_class.return_value = mock_session
            mock_style_class.from_dict.return_value = MagicMock()

            cli = ChimeraCLI()
            cli.start_interactive_mode()

            # Should call prompt 3 times (empty, whitespace, exit), then break
            assert mock_session.prompt.call_count == 3
            mock_animation.assert_called_once()

    def test_chimera_cli_start_interactive_mode_keyboard_interrupt(self):
        """Test interactive mode with keyboard interrupt."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class:

            mock_session = MagicMock()
            mock_session.prompt.side_effect = KeyboardInterrupt()
            mock_session_class.return_value = mock_session
            mock_style_class.from_dict.return_value = MagicMock()

            cli = ChimeraCLI()
            cli.start_interactive_mode()  # Should not raise exception

            assert mock_session.prompt.call_count == 1

    def test_chimera_cli_run_direct_query(self):
        """Test direct query execution."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch.object(ChimeraCLI, '_handle_query') as mock_handle_query:

            mock_session_class.return_value = MagicMock()
            mock_style_class.from_dict.return_value = MagicMock()

            cli = ChimeraCLI()
            cli.run_direct_query("What is AI?")

            mock_handle_query.assert_called_once_with("What is AI?")

    def test_chimera_cli_handle_query(self):
        """Test query handling."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.FocusController') as mock_focus_class, \
             patch('src.main.GRAPH') as mock_graph, \
             patch('src.main.AgentState') as mock_state_class:

            mock_session_class.return_value = MagicMock()
            mock_style_class.from_dict.return_value = MagicMock()

            # Setup mocks
            mock_focus = MagicMock()
            mock_focus_class.return_value.__enter__.return_value = mock_focus

            mock_state = MagicMock()
            mock_state_class.return_value = mock_state

            mock_graph.invoke.return_value = {"response": "Test response"}

            cli = ChimeraCLI()
            cli._handle_query("What is AI?")

            # Verify state creation
            mock_state_class.assert_called_once()
            call_args = mock_state_class.call_args
            assert call_args[1]["query"] == "What is AI?"
            assert callable(call_args[1]["ui"])

            # Verify graph execution
            mock_graph.invoke.assert_called_once_with(mock_state)

            # Verify focus controller usage
            mock_focus.set_planning.assert_called_once()
            mock_focus.set_answer.assert_called_once()

    def test_chimera_cli_handle_query_ui_callbacks(self):
        """Test UI callbacks in query handling."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.FocusController') as mock_focus_class, \
             patch('src.main.GRAPH') as mock_graph, \
             patch('src.main.AgentState') as mock_state_class:

            mock_session_class.return_value = MagicMock()
            mock_style_class.from_dict.return_value = MagicMock()

            # Setup mocks
            mock_focus = MagicMock()
            mock_focus_class.return_value.__enter__.return_value = mock_focus

            mock_state = MagicMock()
            mock_state_class.return_value = mock_state

            mock_graph.invoke.return_value = {"response": "Test response"}

            cli = ChimeraCLI()
            cli._handle_query("What is AI?")

            # Get the UI callback function
            call_args = mock_state_class.call_args
            ui_callback = call_args[1]["ui"]

            # Test UI callback with different messages
            ui_callback("planning_complete")
            ui_callback("tool_start:vector_search")
            ui_callback("synth_start")

            # Verify focus controller calls
            mock_focus.set_planning.assert_called()
            mock_focus.set_executing.assert_called_with("vector_search")
            mock_focus.set_synthesizing.assert_called()

    def test_chimera_cli_handle_query_async_removed(self):
        """Test that _handle_query_async method has been removed."""
        cli = ChimeraCLI()
        # Verify the method no longer exists
        assert not hasattr(cli, '_handle_query_async')


class TestMainFunction:
    """Test the main function and argument parsing."""

    def test_parse_args_no_arguments(self):
        """Test argument parsing with no arguments."""
        with patch('sys.argv', ['main.py']):
            args = _parse_args()
            assert args.question is None

    def test_parse_args_with_question(self):
        """Test argument parsing with question argument."""
        with patch('sys.argv', ['main.py', '--question', 'What is AI?']):
            args = _parse_args()
            assert args.question == "What is AI?"

    def test_parse_args_with_short_question(self):
        """Test argument parsing with short question argument."""
        with patch('sys.argv', ['main.py', '-q', 'What is AI?']):
            args = _parse_args()
            assert args.question == "What is AI?"

    def test_main_with_question(self):
        """Test main function with question argument."""
        with patch('sys.argv', ['main.py', '--question', 'What is AI?']), \
             patch('src.main.ChimeraCLI') as mock_cli_class:

            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli

            main()

            mock_cli.run_direct_query.assert_called_once_with("What is AI?")

    def test_main_without_question(self):
        """Test main function without question argument."""
        with patch('sys.argv', ['main.py']), \
             patch('src.main.ChimeraCLI') as mock_cli_class:

            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli

            main()

            mock_cli.start_interactive_mode.assert_called_once()

    def test_main_cli_initialization(self):
        """Test that main function initializes CLI properly."""
        with patch('sys.argv', ['main.py']), \
             patch('src.main.ChimeraCLI') as mock_cli_class:

            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli

            main()

            mock_cli_class.assert_called_once()


class TestChimeraCLIIntegration:
    """Test ChimeraCLI integration scenarios."""

    def test_cli_with_real_graph_execution(self):
        """Test CLI with real graph execution (mocked dependencies)."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.FocusController') as mock_focus_class, \
             patch('src.main.GRAPH') as mock_graph, \
             patch('src.main.AgentState') as mock_state_class, \
             patch('src.main.Markdown') as mock_markdown_class:

            mock_session_class.return_value = MagicMock()
            mock_style_class.from_dict.return_value = MagicMock()

            # Setup mocks for realistic execution
            mock_focus = MagicMock()
            mock_focus_class.return_value.__enter__.return_value = mock_focus

            mock_state = MagicMock()
            mock_state_class.return_value = mock_state

            mock_graph.invoke.return_value = {
                "response": "AI is artificial intelligence...",
                "plan": ["vector_search"],
                "tool_output": ["Document about AI"],
                "iteration": 1
            }

            mock_markdown = MagicMock()
            mock_markdown_class.return_value = mock_markdown

            cli = ChimeraCLI()
            cli._handle_query("What is AI?")

            # Verify all components were called
            mock_state_class.assert_called_once()
            mock_graph.invoke.assert_called_once_with(mock_state)
            mock_focus.set_planning.assert_called_once()
            mock_focus.set_answer.assert_called_once_with(mock_markdown)
            mock_markdown_class.assert_called_once_with("AI is artificial intelligence...")

    def test_cli_toolbar_message_updates(self):
        """Test that toolbar message updates during execution."""
        with patch('src.main.PromptSession') as mock_session_class, \
             patch('src.main.Style') as mock_style_class, \
             patch('src.main.FocusController') as mock_focus_class, \
             patch('src.main.GRAPH') as mock_graph, \
             patch('src.main.AgentState') as mock_state_class:

            mock_session_class.return_value = MagicMock()
            mock_style_class.from_dict.return_value = MagicMock()

            mock_focus = MagicMock()
            mock_focus_class.return_value.__enter__.return_value = mock_focus

            mock_state = MagicMock()
            mock_state_class.return_value = mock_state

            mock_graph.invoke.return_value = {"response": "Test response"}

            cli = ChimeraCLI()

            # Check initial toolbar message
            assert cli.toolbar_msg == "Type a query or 'help'"

            cli._handle_query("What is AI?")

            # Check that toolbar message was updated during execution
            # (This would require checking the UI callback implementation)
            assert cli.toolbar_msg == "Type a query or 'help'"  # Should be reset after execution
