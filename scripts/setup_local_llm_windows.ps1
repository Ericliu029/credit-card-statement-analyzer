$ErrorActionPreference = "Stop"

$model = "llama3.2:3b"
$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaPath = if ($ollamaCommand) { $ollamaCommand.Source } else { $null }

if (-not $ollamaPath) {
    $localOllama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $localOllama) {
        $ollamaPath = $localOllama
    } elseif (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements
        $ollamaPath = $localOllama
    } else {
        throw "Install Ollama from https://ollama.com/download/windows and run this script again."
    }
}

try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 3 | Out-Null
} catch {
    Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

& $ollamaPath pull $model
Write-Output "Local AI is ready: $model"
