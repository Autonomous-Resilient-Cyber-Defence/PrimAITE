@ECHO OFF

setlocal EnableDelayedExpansion

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
if "%JUPYTER%" == "" (
	set JUPYTER=jupyter
)
set SOURCEDIR=.
set BUILDDIR=_build

set AUTOSUMMARYDIR="%cd%\source\_autosummary\"
set JUPYTEROUTPUTPATH="%cd%\_static\notebooks\html"

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://www.sphinx-doc.org/
	exit /b 1
)

%JUPYTER% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.'jupyter' command was not found. Make sure you have Jupyter
	echo.installed, then set the JUPYTER environment variable to point
	echo.to the full path of the 'jupyter' executable.
	exit /b 1
)

if "%1" == "" goto help

REM delete autosummary if it exists

IF EXIST %AUTOSUMMARYDIR% (
    echo deleting %AUTOSUMMARYDIR%
    RMDIR %AUTOSUMMARYDIR% /s /q
)

REM delete notebook if it exists
IF EXIST %JUPYTEROUTPUTPATH% (
    echo deleting %JUPYTEROUTPUTPATH%
    RMDIR %JUPYTEROUTPUTPATH% /s /q
)

REM run and print html of notebooks
JUPYTER nbconvert --execute --to html --output-dir %JUPYTEROUTPUTPATH% "%cd%\..\src\primaite\**\*.ipynb"

REM copy notebook image dependencies
robocopy ..\src\primaite\notebooks\_package_data _static\notebooks\html\_package_data

REM print the YT licenses
set LICENSEBUILD=pip-licenses --format=rst --with-urls
set DEPS="%cd%\source\primaite-dependencies.rst"

%LICENSEBUILD% --output-file=%DEPS%

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:clean
IF EXIST %AUTOSUMMARYDIR% (
    echo deleting %AUTOSUMMARYDIR%
    RMDIR %AUTOSUMMARYDIR% /s /q
)

IF EXIST %JUPYTEROUTPUTPATH% (
    echo deleting %JUPYTEROUTPUTPATH%
    RMDIR %JUPYTEROUTPUTPATH% /s /q
)

:end
popd
