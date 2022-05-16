@echo off

:: BatchGotAdmin
:-------------------------------------
    REM  --> Check for permissions
        IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
    >nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
    ) ELSE (
    >nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
    )

    REM --> If error flag set, we do not have admin.
    if '%errorlevel%' NEQ '0' (
        echo Requesting administrative privileges...
        goto UACPrompt
    ) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params= %*
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

:--------------------------------------
    REM Install pigar if it's not installed already
    python -m pip install --upgrade pip | findstr /V /C:"Requirement already satisfied" | findstr /C:"Successfully installed"
    pip install pigar | findstr /V /C:"Requirement already satisfied"

    REM Generate requirements.txt
	echo N | pigar --without-referenced-comments >NUL
    echo Generated requirements.txt. && echo.

    REM Install dependencies
    python -m pip install -r requirements.txt | findstr /V /C:"Requirement already satisfied"

    REM upgrade installed dependencies
    python -m pip install -r requirements.txt --upgrade | findstr /V /C:"Requirement already satisfied"

    REM Generate version.py
    python generate_version_file.py 2>&1

    REM Generate final EXE
    python -m PyInstaller main.py --name "VALORANT-ystr" --icon favicon.ico --hidden-import "pystray._win32" --onefile --version-file "version.py" --log-level WARN

    echo. && echo Build complete.
    timeout /t 5 /nobreak