@echo off
echo [%date% %time%] START >> "%USERPROFILE%\Desktop\patent_verify_run.log"
echo CPU: %PROCESSOR_IDENTIFIER% >> "%USERPROFILE%\Desktop\patent_verify_run.log"
"%~dp0专利证书核验系统_core.exe" >> "%USERPROFILE%\Desktop\patent_verify_run.log" 2>&1
echo [%date% %time%] EXIT: %ERRORLEVEL% >> "%USERPROFILE%\Desktop\patent_verify_run.log"
if %ERRORLEVEL% NEQ 0 echo CRASH - Exit code: %ERRORLEVEL% >> "%USERPROFILE%\Desktop\patent_verify_run.log"
