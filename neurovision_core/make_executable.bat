@echo off
echo Running one-click build...
call build.bat
echo Creating shortcut on Desktop...
set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\NeuroVisionCore.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0dist\NeuroVisionCore\NeuroVisionCore.exe" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0dist\NeuroVisionCore" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo Done.
pause
