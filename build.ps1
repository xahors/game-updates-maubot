$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$outFile = Join-Path $PSScriptRoot "game-updates.mbp"

if (Get-Command mbc -ErrorAction SilentlyContinue) {
    Write-Host "Using mbc build..."
    & mbc build
    if ($LASTEXITCODE -eq 0) {
        exit 0
    }
    Write-Warning "mbc build failed (exit $LASTEXITCODE); building game-updates.mbp manually."
}

$files = @(
    (Join-Path $PSScriptRoot "maubot.yaml"),
    (Join-Path $PSScriptRoot "bot.py")
)
foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath $f)) {
        Write-Error "Missing required file: $f"
    }
}

$zipTemp = Join-Path $PSScriptRoot "game-updates.mbp.zip"
foreach ($p in @($outFile, $zipTemp)) {
    if (Test-Path -LiteralPath $p) {
        Remove-Item -LiteralPath $p -Force
    }
}

Compress-Archive -Path $files -DestinationPath $zipTemp -CompressionLevel Optimal
Rename-Item -LiteralPath $zipTemp -NewName "game-updates.mbp"
Write-Host "Built: $outFile"
