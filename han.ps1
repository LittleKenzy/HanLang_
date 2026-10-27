# HanLang PowerShell launcher
# Usage: .\han.ps1 run program.han
# To create an alias: Set-Alias han "$PWD\han.ps1"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$scriptDir\dist\han.exe") {
    & "$scriptDir\dist\han.exe" @args
} else {
    python "$scriptDir\han.py" @args
}

