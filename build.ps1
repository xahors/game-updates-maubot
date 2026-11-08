$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$metaPath = Join-Path $PSScriptRoot "maubot.yaml"
if (-not (Test-Path -LiteralPath $metaPath)) {
    Write-Error "Missing maubot.yaml"
}

$id = $null
$version = $null
foreach ($line in Get-Content -LiteralPath $metaPath) {
    if ($line -match '^\s*id:\s*(.+)\s*$') {
        $id = $Matches[1].Trim()
    } elseif ($line -match '^\s*version:\s*(.+)\s*$') {
        $version = $Matches[1].Trim()
    }
}
if (-not $id -or -not $version) {
    Write-Error "Could not read id and version from maubot.yaml"
}

$buildDir = Join-Path $PSScriptRoot "build"
if (-not (Test-Path -LiteralPath $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

$outName = "${id}-v${version}.mbp"
$outFile = Join-Path $buildDir $outName

if (Get-Command mbc -ErrorAction SilentlyContinue) {
    Write-Host "Using mbc build -> $outName"
    & mbc build -o $outFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Built: $outFile"
        exit 0
    }
    Write-Warning "mbc build failed (exit $LASTEXITCODE); building $outName manually."
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

$zipTemp = Join-Path $buildDir "$outName.zip"
foreach ($p in @($outFile, $zipTemp)) {
    if (Test-Path -LiteralPath $p) {
        Remove-Item -LiteralPath $p -Force
    }
}

Compress-Archive -Path $files -DestinationPath $zipTemp -CompressionLevel Optimal
Rename-Item -LiteralPath $zipTemp -NewName $outName
Write-Host "Built: $outFile"
