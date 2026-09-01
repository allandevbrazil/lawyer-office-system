# keepalive.ps1 — Keep Alive local (Render + Neon)

# Uso manual (ou via Agendador de Tarefas do Windows, ex.: 1x por semana):
#   powershell -ExecutionPolicy Bypass -File .\scripts\keepalive.ps1
# Faz o mesmo que o workflow .github/workflows/keepalive.yml:
# acorda a API do Render e valida login + banco (Neon) com credenciais demo.

$ErrorActionPreference = "Stop"
$BASE = "https://lawyer-office-system.onrender.com"
$EMAIL = "master@example.com"
$PASS  = "DemoMaster@2026!"

Write-Host "== Keep Alive: $BASE =="

# 1) Acordar a API (Render free dorme após ~15 min)
$ready = Invoke-WebRequest -Uri "$BASE/ready" -UseBasicParsing -TimeoutSec 120
Write-Host "GET /ready -> $($ready.StatusCode)"
if ($ready.StatusCode -ne 200) { throw "API nao respondeu 200 em /ready" }

# 2) Login (OAuth2 form) -> access_token
$body = @{ username = $EMAIL; password = $PASS }
$login = Invoke-RestMethod -Uri "$BASE/api/v1/auth/login" -Method Post `
  -Body $body -TimeoutSec 60
$token = $login.access_token
if (-not $token) { throw "Login falhou (token vazio)" }
Write-Host "Login OK"

# 3) Endpoint protegido -> comprova que o banco (Neon) responde
$headers = @{ Authorization = "Bearer $token" }
$summary = Invoke-RestMethod -Uri "$BASE/api/v1/dashboard/summary" -Headers $headers -TimeoutSec 60
Write-Host "GET /api/v1/dashboard/summary -> 200 OK (banco respondendo)"

Write-Host "== Keep Alive concluido com sucesso: $(Get-Date) =="
