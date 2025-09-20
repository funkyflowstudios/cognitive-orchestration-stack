# Contributing Guidelines

Thank you for considering a contribution! Fork the repo, create a topic branch, and open a PR.

## Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd agent_stack
   poetry install
   ```

2. **Configure environment**:
   ```bash
   cp config/dev.env.template config/dev.env
   # Edit config/dev.env with your credentials
   ```

## Code Standards

1. **Follow PEP 8** & project coding standards (88 character line length)
2. **Include type hints** and comprehensive docstrings
3. **Run quality checks** locally—PRs must be clean:
   ```bash
   poetry run black src tests
   poetry run isort src tests
   poetry run ruff check src tests
   poetry run mypy src
   poetry run pytest -v
   ```
4. **Update documentation** for new features (README, TUI docs, test docs)
5. **One feature or fix** per pull request

## Testing

- All new code must include tests
- Run the full test suite before submitting
- Ensure 100% test coverage for new features

## Security

- Never commit API keys or passwords
- Use environment variables for sensitive data
- Follow the security guidelines in `SECURITY.md`
