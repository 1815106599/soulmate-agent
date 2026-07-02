# 社交匹配系统一键启动脚本
# 自动启动后端 (uvicorn) + 前端 (streamlit)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  社交匹配系统 — 一键启动" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\18151\AppData\Local\Programs\Python\Python311\python.exe"
$BackendPort = 8001
$StreamlitPort = 8501

# 检查 Python
if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ 找不到 Python: $PythonExe" -ForegroundColor Red
    exit 1
}

# 杀死旧进程
Write-Host "🔄 清理旧进程..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
    $cmdLine = (Get-CimObject Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
    if ($cmdLine -match "uvicorn.*backend\.app" -or $cmdLine -match "streamlit.*app\.py") {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  已停止 PID $($_.Id)" -ForegroundColor Gray
    }
}
Start-Sleep -Seconds 1

# 启动后端
Write-Host ""
Write-Host "🚀 启动后端 (port $BackendPort)..." -ForegroundColor Green
$backendJob = Start-Job -Name "SocialMatch-Backend" -ScriptBlock {
    param($root, $python, $port)
    Set-Location $root
    & $python -m uvicorn backend.app:app --host 0.0.0.0 --port $port
} -ArgumentList $ProjectRoot, $PythonExe, $BackendPort

Start-Sleep -Seconds 3

# 检查后端是否启动成功
$backendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$BackendPort/docs" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $backendOk = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($backendOk) {
    Write-Host "✅ 后端启动成功: http://localhost:$BackendPort" -ForegroundColor Green
} else {
    Write-Host "⚠️ 后端启动中，请稍后... http://localhost:$BackendPort" -ForegroundColor Yellow
}

# 启动前端
Write-Host ""
Write-Host "🚀 启动前端 (port $StreamlitPort)..." -ForegroundColor Green
$frontendJob = Start-Job -Name "SocialMatch-Frontend" -ScriptBlock {
    param($root, $python, $port)
    Set-Location $root
    $env:STREAMLIT_SERVER_HEADLESS = "true"
    & $python -m streamlit run frontend/app.py --server.headless=true --server.port $port
} -ArgumentList $ProjectRoot, $PythonExe, $StreamlitPort

Start-Sleep -Seconds 3

# 检查前端
$frontendOk = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$StreamlitPort" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $frontendOk = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($frontendOk) {
    Write-Host "✅ 前端启动成功: http://localhost:$StreamlitPort" -ForegroundColor Green
} else {
    Write-Host "⚠️ 前端启动中，请稍后... http://localhost:$StreamlitPort" -ForegroundColor Yellow
}

# 完成
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  启动完成！" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  前端页面: http://localhost:$StreamlitPort" -ForegroundColor White
Write-Host "  后端API:  http://localhost:$BackendPort" -ForegroundColor White
Write-Host "  API文档:   http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host ""
Write-Host "  停止服务: Stop-Job -Name SocialMatch-Backend, SocialMatch-Frontend" -ForegroundColor Gray
Write-Host ""

# 保持窗口打开
Read-Host "按 Enter 键退出..."
