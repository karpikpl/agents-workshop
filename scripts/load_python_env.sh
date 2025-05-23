 #!/bin/sh

echo 'Creating Python virtual environment "demo_app/.setup_venv"...'
python3 -m venv .setup_venv

echo 'Installing dependencies from "setup_requirements.txt" into virtual environment (in quiet mode)...'
.setup_venv/bin/python -m pip --quiet --disable-pip-version-check install -r demo_app/setup_requirements.txt
