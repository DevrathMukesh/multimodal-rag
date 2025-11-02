# PowerShell script to initialize Ollama with the embedding model
# For Windows users

$ollamaUrl = "http://localhost:11434"
$maxRetries = 30
$retryCount = 0

Write-Host "Waiting for Ollama to be ready..." -ForegroundColor Yellow

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "$ollamaUrl/api/tags" -UseBasicParsing -ErrorAction Stop
        Write-Host "Ollama is ready!" -ForegroundColor Green
        break
    } catch {
        $retryCount++
        Write-Host "Waiting for Ollama... ($retryCount/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if ($retryCount -eq $maxRetries) {
    Write-Host "Failed to connect to Ollama after $maxRetries attempts" -ForegroundColor Red
    exit 1
}

Write-Host "Pulling embedding model: embeddinggemma:latest" -ForegroundColor Cyan
$body = @{
    name = "embeddinggemma:latest"
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "$ollamaUrl/api/pull" -Method Post -Body $body -ContentType "application/json"
    Write-Host "Model pull initiated..." -ForegroundColor Green
} catch {
    Write-Host "Error pulling model: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nOllama initialization complete!" -ForegroundColor Green
Write-Host "Available models:" -ForegroundColor Cyan
try {
    $models = Invoke-RestMethod -Uri "$ollamaUrl/api/tags" -UseBasicParsing
    $models.models | ForEach-Object { Write-Host "  - $($_.name)" -ForegroundColor White }
} catch {
    Write-Host "Could not retrieve model list" -ForegroundColor Yellow
}

