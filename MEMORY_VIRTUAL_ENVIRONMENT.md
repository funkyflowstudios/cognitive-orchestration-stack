# Memory: Always Work Within Virtual Environment

## Critical Practice

When working on Python projects, I must ALWAYS ensure I'm working within the project's virtual environment before installing any dependencies or running Python commands.

## Required Steps

1. Check if a venv exists in the project
2. Activate the virtual environment before running any pip install, python commands, or other Python-related operations
3. Verify I'm in the venv by checking sys.prefix or looking for (venv) in the prompt

## Why This Matters

- Prevents installing packages globally
- Ensures reproducible builds
- Maintains project isolation
- Prevents dependency conflicts

## Commands

- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`
- Verify: `python -c "import sys; print(sys.prefix)"`

## Never Do

- Install dependencies outside of the project's virtual environment
- Run pip install without first activating the venv
- Assume the environment is already activated

This memory was created after making the mistake of installing dependencies globally instead of within the project's virtual environment.
