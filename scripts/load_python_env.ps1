$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  # fallback to python3 if python not found
  $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

Write-Host 'Creating python virtual environment ".setup_venv"'
Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m venv ./.setup_venv" -Wait -NoNewWindow

$venvPythonPath = "./.setup_venv/scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = "./.setup_venv/bin/python"
}

Write-Host 'Installing dependencies from "setup_requirements.txt" into virtual environment'
Start-Process -FilePath $venvPythonPath -ArgumentList "-m pip install -r setup/setup_requirements.txt" -Wait -NoNewWindow