@echo off
REM Update these with your Anaplan credentials
set ANAPLAN_USER=your.email@example.com
set ANAPLAN_PASS=yourPassword
set FLOW_ID=your_cloudworks_integration_flow_id

REM Encode username:password in base64 using PowerShell
for /f "delims=" %%i in ('powershell "[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('%ANAPLAN_USER%:%ANAPLAN_PASS%'))"') do set BASIC_AUTH=%%i

REM Get token from Anaplan Authentication Service API
for /f "delims=" %%j in ('curl -s -X POST "https://auth.anaplan.com/token/authenticate" ^
    -H "Authorization: Basic %BASIC_AUTH%" ^
    -H "Content-Type: application/json" ^
    -d "{}" ^ | powershell -Command "($input | ConvertFrom-Json).tokenInfo.tokenValue"') do set BEARER_TOKEN=%%j

REM Execute the CloudWorks integration flow
curl -X POST "https://api.anaplan.com/cloudworks/v2/integrationFlows/%FLOW_ID%/executions" ^
  -H "Authorization: Bearer %BEARER_TOKEN%" ^
  -H "Content-Type: application/json"

pause
