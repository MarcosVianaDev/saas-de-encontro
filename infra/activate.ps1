# Execute com dot-sourcing: . .\infra\activate.ps1
$projectRoot = Split-Path $PSScriptRoot -Parent
$env:PATH = (Join-Path $projectRoot '.tools\node-v26.10.0-win-x64') + ';' + $env:PATH
. (Join-Path $projectRoot '.venv\Scripts\Activate.ps1')
