@echo off
REM HanLang launcher for Windows CMD
if exist "%~dp0dist\han.exe" (
    "%~dp0dist\han.exe" %*
) else (
    python "%~dp0han.py" %*
)
