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

# --- Detect VS generator via vswhere ----------------------------------------
$VSGenerator = $null
$VSArch = "x64"

$vswhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    $vsVersionRaw = & $vswhere -latest -property installationVersion 2>$null
    if ($vsVersionRaw) {
        $vsMajor = [int]($vsVersionRaw.Split(".")[0])
        switch ($vsMajor) {
            17 { $VSGenerator = "Visual Studio 17 2022" }
            16 { $VSGenerator = "Visual Studio 16 2019" }
            15 { $VSGenerator = "Visual Studio 15 2017" }
            default { $VSGenerator = "Visual Studio 17 2022" }
        }
        Write-Host "  Detected VS $vsVersionRaw -> generator: $VSGenerator"
    }
}

if (-not $VSGenerator) {
    Write-Host "  vswhere not available, scanning cmake generators..."
    $cmakeHelp = & $CMake --help 2>&1 | Out-String
    $generatorOrder = @("Visual Studio 17 2022", "Visual Studio 16 2019", "Visual Studio 15 2017", "Visual Studio 14 2015")
    foreach ($gen in $generatorOrder) {
        if ($cmakeHelp -match [regex]::Escape($gen)) {
            $VSGenerator = $gen
            Write-Host "  Found generator: $VSGenerator"
            break
        }
    }
}

if (-not $VSGenerator) {
    $ninjaCmd = Get-Command ninja -ErrorAction SilentlyContinue
    if ($ninjaCmd) {
        $VSGenerator = "Ninja"
        $VSArch = ""
        Write-Host "  Falling back to Ninja generator."
    }
}

if (-not $VSGenerator) {
    Write-Error @"
Could not detect a usable CMake generator.
Fix: Install VS 2022 with 'Desktop development with C++' workload from:
  https://visualstudio.microsoft.com/
"@
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

# Wipe a build dir if it contains a CMakeCache with a different generator.
# This prevents the "generator does not match" error after a failed first run.
function Reset-BuildDirIfStale {
    param([string]$buildDir)
    $cacheFile = Join-Path $buildDir "CMakeCache.txt"
    if (-not (Test-Path $cacheFile)) { return }
    $cacheContent = Get-Content $cacheFile -Raw
    # Check if the cached generator matches what we want to use
    if ($cacheContent -notmatch [regex]::Escape($VSGenerator)) {
        Write-Host "  Stale CMakeCache detected (wrong generator). Wiping $buildDir ..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $buildDir
    }
}

function CMakeConfigureArgs {
    param([string]$srcDir, [string[]]$extra)
    $a = @($srcDir, "-G", $VSGenerator)
    if ($VSArch -ne "") { $a += @("-A", $VSArch) }
    $a += $extra
    return $a
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
    Reset-BuildDirIfStale $FxcExtractorBuild
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
    Reset-BuildDirIfStale $XenosRecompBuild
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
