# =============================================================================
# build_and_generate_dxil.ps1
# Full Windows pipeline: build rage_fxc_extractor + XenosRecomp, extract
# Xbox 360 shaders from fxl_final, then generate shader_cache.cpp with DXIL.
#
# Run from repo root in a VS 2022 x64 Developer PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\tools\build_and_generate_dxil.ps1
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

# --- Locate cmake (prefer VS-bundled, fall back to PATH) --------------------
$CMake = "cmake"
$VSCMake = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
if (Test-Path $VSCMake) { $CMake = $VSCMake }

# --- Paths ------------------------------------------------------------------
$FxcExtractorSrc   = Join-Path $RepoRoot "tools\rage_fxc_extractor"
$FxcExtractorBuild = Join-Path $RepoRoot "tools\rage_fxc_extractor\build"
$FxcExtractorExe   = Join-Path $FxcExtractorBuild "Release\rage_fxc_extractor.exe"

$XenosRecompSrc    = Join-Path $RepoRoot "tools\XenosRecomp"
$XenosRecompBuild  = Join-Path $RepoRoot "tools\XenosRecomp\build_win"
$XenosRecompExe    = Join-Path $XenosRecompBuild "XenosRecomp\Release\XenosRecomp.exe"

# fxl_final is already extracted on the Mac by the macOS installer
# fxl_final is inside the repo private dir - visible to Windows over the Mac share
$FxlFinalDir         = Join-Path $RepoRoot "LibertyRecompLib\private\fxl_final"
$ExtractedShadersDir = Join-Path $RepoRoot "extracted_shaders"
$ShaderCacheCpp      = Join-Path $RepoRoot "LibertyRecompLib\shader\shader_cache.cpp"
$ShaderCommonH       = Join-Path $RepoRoot "tools\XenosRecomp\XenosRecomp\shader_common.h"
$DxilDll             = Join-Path $RepoRoot "tools\XenosRecomp\thirdparty\dxc-bin\bin\x64\dxil.dll"

# --- Helpers ----------------------------------------------------------------
function Step([string]$msg) {
    Write-Host ""
    Write-Host "--- $msg ---" -ForegroundColor Cyan
}

function Run {
    param([string]$exe, [string[]]$arguments)
    Write-Host "  > $exe $arguments"
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $exe"
    }
}

# --- 0. Validate fxl_final --------------------------------------------------
Step "Checking shader source directory"
if (-not (Test-Path $FxlFinalDir)) {
    Write-Error "fxl_final not found at: $FxlFinalDir`nMake sure the Mac home share is accessible and the game is installed on macOS."
}
$FxcCount = (Get-ChildItem -LiteralPath $FxlFinalDir -Filter "*.fxc").Count
Write-Host "  Found $FxcCount .fxc files" -ForegroundColor Green

# --- 1. Build rage_fxc_extractor --------------------------------------------
Step "Building rage_fxc_extractor"
if (Test-Path $FxcExtractorExe) {
    Write-Host "  Already built, skipping." -ForegroundColor DarkGray
} else {
    New-Item -ItemType Directory -Force -Path $FxcExtractorBuild | Out-Null
    Push-Location $FxcExtractorBuild
    try {
        Run $CMake @("..", "-DCMAKE_BUILD_TYPE=Release")
        Run $CMake @("--build", ".", "--config", "Release")
    } finally {
        Pop-Location
    }
}
Write-Host "  $FxcExtractorExe" -ForegroundColor Green

# --- 2. Build XenosRecomp ---------------------------------------------------
Step "Building XenosRecomp (DXIL enabled)"
if (Test-Path $XenosRecompExe) {
    Write-Host "  Already built, skipping." -ForegroundColor DarkGray
} else {
    New-Item -ItemType Directory -Force -Path $XenosRecompBuild | Out-Null
    Push-Location $XenosRecompBuild
    try {
        Run $CMake @("..", "-DXENOS_RECOMP_DXIL=ON", "-DCMAKE_BUILD_TYPE=Release")
        Run $CMake @("--build", ".", "--config", "Release", "--target", "XenosRecomp")
    } finally {
        Pop-Location
    }
}
Write-Host "  $XenosRecompExe" -ForegroundColor Green

# --- 3. dxil.dll beside the process for DXIL signing -----------------------
Step "Setting up dxil.dll"
$dxilDest = Join-Path (Get-Location) "dxil.dll"
if (-not (Test-Path $dxilDest)) {
    Copy-Item $DxilDll $dxilDest
    Write-Host "  Copied dxil.dll to working directory" -ForegroundColor Green
} else {
    Write-Host "  dxil.dll already present" -ForegroundColor DarkGray
}

# --- 4. Extract Xbox 360 shaders --------------------------------------------
Step "Extracting Xbox 360 shaders from fxl_final"
$existingFiles = 0
if (Test-Path $ExtractedShadersDir) {
    $existingFiles = (Get-ChildItem -LiteralPath $ExtractedShadersDir -Recurse -File).Count
}

if ($existingFiles -gt 0) {
    Write-Host "  extracted_shaders\ already has $existingFiles files, skipping." -ForegroundColor DarkGray
    Write-Host "  (Delete extracted_shaders\ to force re-extraction)" -ForegroundColor DarkGray
} else {
    New-Item -ItemType Directory -Force -Path $ExtractedShadersDir | Out-Null
    Run $FxcExtractorExe @("--batch", $FxlFinalDir, $ExtractedShadersDir)
    $extracted = (Get-ChildItem -LiteralPath $ExtractedShadersDir -Recurse -File).Count
    Write-Host "  Extracted $extracted shader files" -ForegroundColor Green
}

# --- 5. Generate shader_cache.cpp with DXIL ---------------------------------
Step "Generating shader_cache.cpp"
if (Test-Path $ShaderCacheCpp) {
    Copy-Item $ShaderCacheCpp "$ShaderCacheCpp.bak" -Force
    Write-Host "  Backed up existing shader_cache.cpp"
}
Run $XenosRecompExe @($ExtractedShadersDir, $ShaderCacheCpp, $ShaderCommonH)
$sizeMB = [math]::Round((Get-Item $ShaderCacheCpp).Length / 1MB, 1)
Write-Host "  Generated shader_cache.cpp ($sizeMB MB)" -ForegroundColor Green

# --- 6. Compile post-process HLSL -> .dxil.h --------------------------------
Step "Compiling post-process HLSL shaders"
$ps1 = Join-Path $RepoRoot "tools\compile_dxil_shaders.ps1"
powershell -ExecutionPolicy Bypass -File $ps1
if ($LASTEXITCODE -ne 0) {
    throw "compile_dxil_shaders.ps1 failed"
}

# --- Done -------------------------------------------------------------------
Write-Host ""
Write-Host "All done! Run the build:" -ForegroundColor Green
Write-Host "  cmake . --preset x64-Clang-Release"
Write-Host "  cmake --build .\out\build\x64-Clang-Release --target LibertyRecomp"
Write-Host ""
