$projectRoot = Split-Path -Parent $PSScriptRoot
$zipName = "AI_Powered_Flight_Delay_Prediction_System.zip"
$zipPath = Join-Path $projectRoot $zipName

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path (Join-Path $projectRoot "*") -DestinationPath $zipPath
Write-Host "ZIP created at: $zipPath"
