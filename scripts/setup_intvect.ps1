# Check if UV is available
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host 'Using UV for Python environment management...'
    
    # Navigate to setup directory
    Set-Location -Path setup
    
    # Run UV sync to create/update environment
    uv sync
    uv run setup_intvect.py

    Set-Location -Path ..
} else {
    # Fall back to standard venv if UV is not available
    # First, load the Python environment
    ./scripts/load_python_env.ps1
    $venvPythonPath = "./.setup_venv/scripts/python.exe"
    if (Test-Path -Path "/usr") {
        # fallback to Linux venv path
        $venvPythonPath = "./.setup_venv/bin/python"
    }

    # Define the path to the Python script
    $pythonScriptPath = "setup/setup_intvect.py"

    # Run the Python script
    Start-Process -FilePath $venvPythonPath -ArgumentList $pythonScriptPath -Wait -NoNewWindow
}

