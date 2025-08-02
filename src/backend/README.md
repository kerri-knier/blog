# Backend

This is an aws lambda function behind an API Gateway instance.

# Managing packages

Install `uv` to manage packages

Create a virtual environment for the packages `uv venv`

Install the required packages `uv pip install --requirements requirements.txt`

If the linter is showing unresolved imports, then choose the python interpreter from `src/backend/.venv/bin/python`