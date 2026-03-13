# =============================================================================
# build_and_generate_dxil.ps1
# Full Windows pipeline: build rage_fxc_extractor + XenosRecomp, extract
# Xbox 360 shaders from fxl_final, then generate shader_cache.cpp with DXIL.
#
# Run from repo root (no VS Developer Prompt required):
#   powershell -ExecutionPolicy Bypass -File .\tools\build_and_generate_dxil.ps1
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

# --- Locate cmake -----------------------------------------------------------
$CMake = $null
$CMakeCandidates = @(
    "C:\tools\cmake\bin\cmake.exe",
    "C:\Program Files\CMake\bin\cmake.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
    "C:\Program Files\Microsoft Visual Studio\2019\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
    "C:\ProgramData\chocolatey\bin\cmake.exe"
)
foreach ($candidate in $CMakeCandidates) {
    if (Test-Path $candidate) { $CMake = $candidate; break }
}
if (-not $CMake) {
    $cmakeCmd = Get-Command cmake -ErrorAction SilentlyContinue
    if ($cmakeCmd) { $CMake = $cmakeCmd.Source }
}
if (-not $CMake) {
    Write-Error "cmake not found. Install from https://cmake.org/download/ and tick 'Add to PATH'."
}
Write-Host "  Using cmake: $CMake"

# --- Detect VS generator ----------------------------------------------------
# Pick the highest VS version available so MSBuild is used (no nmake needed).
$VSGenerator = $null
$VSGeneratorCandidates = @(
    @{ Gen = "Visual Studio 17 2022"; Path = "C:\Program Files\Microsoft Visual Studio\2022" },
    @{ Gen = "Visual Studio 16 2019"; Path = "C:\Program Files\Microsoft Visual Studio\2019" },
    @{ Gen = "Visual Studio 15 2017"; Path = "C:\Program Files (x86)\Microsoft Visual Studio\2017" }
)
foreach ($entry in $VSGeneratorCandidates) {
    if (Test-Path $entry.Path) { $VSGenerator = $entry.Gen; break }
}
if (-not $VSGenerator) {
    # Fallback: try Ninja if it's on PATH
    $ninjaCmd = Get-Command ninja -ErrorAction SilentlyContinue
    if ($ninjaCmd) {
        $VSGenerator = "Ninja"
        Write-Host "  No VS install detected, falling back to Ninja generator."
    } else {
        Write-Error @"
No Visual Studio install found and 'ninja' is not on PATH.
Fix options:
  1. Install VS 2022 from https://visualstudio.microsoft.com/  (Desktop dev with C++ workload)
  2. Or run this from a VS 2022 Developer Command Prompt (Start menu -> 'Developer PowerShell for VS 2022')
"@
    }
}
Write-Host "  Using generator: $VSGenerator"

# --- Paths ------------------------------------------------------------------
$FxcExtractorSrc   = Join-Path $RepoRoot "tools\rage_fxc_extractor"
$FxcExtractorBuild = Join-Path $RepoRoot "tools\rage_fxc_extractor\build"
$FxcExtractorExe   = Join-Path $FxcExtractorBuild "Release\rage_fxc_extractor.exe"

$XenosRecompSrc    = Join-Path $RepoRoot "tools\XenosRecomp"
$XenosRecompBuild  = Join-Path $RepoRoot "tools\XenosRecomp\build_win"
$XenosRecompExe    = Join-Path $XenosRecompBuild "XenosRecomp\Release\XenosRecomp.exe"

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
    Write-Host "  > $exe $($arguments -join ' ')"
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $exe"
    }
}

# Build cmake args for configure - VS generators need -A x64; Ninja does not
function CMakeConfigureArgs {
    param([string]$srcDir, [string[]]$extra)
    $args = @($srcDir, "-G", $VSGenerator)
    if ($VSGenerator -like "Visual Studio*") {
        $args += @("-A", "x64")
    }
    $args += $extra
    return $args
}

# --- 0. Validate fxl_final --------------------------------------------------
Step "Checking shader source directory"
if (-not (Test-Path $FxlFinalDir)) {
    Write-Error "fxl_final not found at: $FxlFinalDir"
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
        Run $CMake (CMakeConfigureArgs ".." @("-DCMAKE_BUILD_TYPE=Release"))
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
        Run $CMake (CMakeConfigureArgs ".." @("-DXENOS_RECOMP_DXIL=ON", "-DCMAKE_BUILD_TYPE=Release"))
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
