 #!/bin/sh


if command -v uv >/dev/null 2>&1; then
    echo 'Using UV for Python environment management...'
    cd setup
    uv sync
    echo 'Running setup_intvect.py with UV...'
    uv run setup_intvect.py
    cd ..
else
    echo 'UV not found. Using standard Python venv...'
    . ./scripts/load_python_env.sh
    ./.setup_venv/bin/python ./setup/setup_intvect.py
fi

