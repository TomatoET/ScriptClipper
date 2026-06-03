$ErrorActionPreference = "Stop"

$AppName = "ScriptClipper"
$Version = "0.1.0"
$PackageName = "$AppName-v$Version-windows-x64"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$BuildDir = Join-Path $Root "build"
$DistDir = Join-Path $Root "dist"
$ReleaseDir = Join-Path $Root "release"
$ReleaseAppDir = Join-Path $ReleaseDir $PackageName
$ZipPath = Join-Path $ReleaseDir "$PackageName.zip"
$SpecPath = Join-Path $Root "ScriptClipper.spec"
$ExePath = Join-Path $ReleaseAppDir "$AppName.exe"

Write-Host "Building $PackageName"
Set-Location $Root

foreach ($Path in @($BuildDir, $DistDir, $ReleaseDir)) {
    if (Test-Path $Path) {
        Write-Host "Removing $Path"
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

Write-Host "Checking PyInstaller..."
python -m PyInstaller --version | Out-Host

Write-Host "Running PyInstaller..."
python -m PyInstaller --noconfirm $SpecPath

$BuiltAppDir = Join-Path $DistDir $AppName
if (-not (Test-Path $BuiltAppDir)) {
    throw "PyInstaller output not found: $BuiltAppDir"
}

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
Copy-Item -LiteralPath $BuiltAppDir -Destination $ReleaseAppDir -Recurse

foreach ($FileName in @("README.md", "LICENSE")) {
    $Source = Join-Path $Root $FileName
    if (Test-Path $Source) {
        Copy-Item -LiteralPath $Source -Destination (Join-Path $ReleaseAppDir $FileName) -Force
    }
}

$AssetsSource = Join-Path $Root "assets"
$AssetsTarget = Join-Path $ReleaseAppDir "assets"
if ((Test-Path $AssetsSource) -and (-not (Test-Path $AssetsTarget))) {
    Copy-Item -LiteralPath $AssetsSource -Destination $AssetsTarget -Recurse
}

if (-not (Test-Path $ExePath)) {
    throw "Final executable not found: $ExePath"
}

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

Write-Host "Creating zip package..."
Compress-Archive -Path $ReleaseAppDir -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "Build completed."
Write-Host "EXE: $ExePath"
Write-Host "ZIP: $ZipPath"
