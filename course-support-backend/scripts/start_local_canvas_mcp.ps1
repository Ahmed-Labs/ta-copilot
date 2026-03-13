$repoRoot = Split-Path -Parent $PSScriptRoot
$canvasRepo = Join-Path $repoRoot "..\\canvas-mcp"
$serverExe = Join-Path $canvasRepo ".venv\\Scripts\\canvas-mcp-server.exe"

if (-not (Test-Path $serverExe)) {
    Write-Error "Canvas MCP server executable not found at $serverExe"
    exit 1
}

Write-Output "Starting local Canvas MCP server on http://127.0.0.1:8819/mcp"
& $serverExe --transport streamable-http --host 127.0.0.1 --port 8819
