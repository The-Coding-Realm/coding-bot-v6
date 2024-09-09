@ECHO OFF

:: Check for Python Installation
py -3.10 > NUL 
if errorlevel 1 (goto errorNoPylauncher) else (goto pyLauncherScript)

:pyLauncherScript
    :: Reaching here means Python is installed.
    echo "Upgrading pip..."
    py -3.10 -m pip install --upgrade pip > NUL
    if errorlevel 1 goto errorPipUpgrade

    py -3.10 -m pip install --upgrade setuptools > NUL
    if errorlevel 1 goto errorSetuptoolsUpgrade 

    echo "Creating virtual environment..."
    py -3.10 -m pip install virtualenv 
    py -3.10 -m venv venv 
    .\venv\Scripts\activate.bat

    echo "Installing requirements..."

    pip install -r requirements.txt > NUL
    if errorlevel 1 goto errorRequirements

    python main.py

:pythonScript
    echo "Upgrading pip..."
    python -m pip install --upgrade pip > NUL
    if errorlevel 1 goto errorPipUpgrade

    python -m pip install --upgrade setuptools > NUL
    if errorlevel 1 goto errorSetuptoolsUpgrade 

    echo "Creating virtual environment..."
    python -m pip install virtualenv 
    python -m venv venv 
    .\venv\Scripts\activate.bat

    echo "Installing requirements..."

    pip install -r requirements.txt > NUL
    if errorlevel 1 goto errorRequirements

    python main.py

:: Execute stuff...

:: Once done, exit the batch file -- skips executing the errorNoPython section
goto:eof

:errorNoPylauncher
    python --version | findstr 3.10 > NUL
    if errorlevel 1 (goto errorNoPython) else (goto pythonScript)

:errorNoPython
    echo "Python 3.10 is not installed."
    echo "Please install Python 3.10 and try again."
    echo "Exiting..."
    exit 1

:errorPipUpgrade
echo.
echo Error^: pip upgrade failed

:errorSetuptoolsUpgrade
echo.
echo Error^: setuptools upgrade failed

:errorRequirements
echo.
echo Error^: requirements installation failed

