./scripts/load_python_env.ps1

$venvPythonPath = "./.setup_venv/scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = "./.setup_venv/bin/python"
}

# Define the path to the Python script
$pythonScriptPath = "demo_app/setup_intvect.py"

Start-Process -FilePath $venvPythonPath -ArgumentList $pythonScriptPath -Wait -NoNewWindow