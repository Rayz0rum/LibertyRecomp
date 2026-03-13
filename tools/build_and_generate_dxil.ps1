# =============================================================================
# build_and_generate_dxil.ps1
# Full Windows pipeline: build rage_fxc_extractor + XenosRecomp, extract
# Xbox 360 shaders from the RPF, then generate shader_cache.cpp with DXIL.
#
# Run from repo root in a VS 2022 x64 Developer PowerShell:
#   cd \\Mac\Home\Downloads\LibertyRecomp
#   .\tools\build_and_generate_dxil.ps1
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot | Split-Path -Parent

# ── Locate cmake (prefer VS-bundled, fall back to PATH) ──────────────────────
$CMake = "cmake"
$VSCMake = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
if (Test-Path $VSCMake) { $CMake = $VSCMake }

# ── Paths ────────────────────────────────────────────────────────────────────
$FxcExtractorSrc  = Join-Path $RepoRoot "tools\rage_fxc_extractor"
$FxcExtractorBuild= Join-Path $RepoRoot "tools\rage_fxc_extractor\build"
$FxcExtractorExe  = Join-Path $FxcExtractorBuild "Release\rage_fxc_extractor.exe"

$XenosRecompSrc   = Join-Path $RepoRoot "tools\XenosRecomp"
$XenosRecompBuild = Join-Path $RepoRoot "tools\XenosRecomp\build_win"
$XenosRecompExe   = Join-Path $XenosRecompBuild "XenosRecomp\Release\XenosRecomp.exe"

# Shader source: use the already-extracted fxl_final directory on the Mac share
# (common.rpf has already been extracted by the macOS installer)
$FxlFinalDir = "\\Mac\Home\Library\Application Support\LibertyRecomp\game\common\shaders\fxl_final"

$ExtractedShadersDir = Join-Path $RepoRoot "extracted_shaders"
$ShaderCacheCpp      = Join-Path $RepoRoot "LibertyRecompLib\shader\shader_cache.cpp"
$ShaderCommonH       = Join-Path $RepoRoot "tools\XenosRecomp\XenosRecomp\shader_common.h"
$DxilDll             = Join-Path $RepoRoot "tools\XenosRecomp\thirdparty\dxc-bin\bin\x64\dxil.dll"

# ── Helper ───────────────────────────────────────────────────────────────────
function Step([string]$msg) {
    Write-Host ""
    Write-Host "━━━ $msg" -ForegroundColor Cyan
}

function Run([string]$exe, [string[]]$args) {
    Write-Host "  > $exe $args"
    & $exe @args
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE): $exe" }
}

# ── 0. Validate fxl_final exists and is non-empty ───────────────────────────
Step "Checking shader source directory"
if (-not (Test-Path $FxlFinalDir)) {
    Write-Error @"
fxl_final directory not found at:
  $FxlFinalDir

Make sure the Mac is sharing its home folder and the game has been installed
at least once on macOS (~/Library/Application Support/LibertyRecomp/game/).
"@
}
$FxcCount = (Get-ChildItem $FxlFinalDir -Filter "*.fxc").Count
Write-Host "  Found $FxcCount .fxc files in fxl_final" -ForegroundColor Green

# ── 1. Build rage_fxc_extractor ──────────────────────────────────────────────
Step "Building rage_fxc_extractor"
if (Test-Path $FxcExtractorExe) {
    Write-Host "  Already built, skipping." -ForegroundColor DarkGray
} else {
    New-Item -ItemType Directory -Force $FxcExtractorBuild | Out-Null
    Push-Location $FxcExtractorBuild
    try {
        Run $CMake @("..", "-DCMAKE_BUILD_TYPE=Release")
        Run $CMake @("--build", ".", "--config", "Release")
    } finally { Pop-Location }
}
Write-Host "  rage_fxc_extractor.exe: $FxcExtractorExe" -ForegroundColor Green

# ── 2. Build XenosRecomp ─────────────────────────────────────────────────────
Step "Building XenosRecomp (with DXIL)"
if (Test-Path $XenosRecompExe) {
    Write-Host "  Already built, skipping." -ForegroundColor DarkGray
} else {
    New-Item -ItemType Directory -Force $XenosRecompBuild | Out-Null
    Push-Location $XenosRecompBuild
    try {
        Run $CMake @("..", "-DXENOS_RECOMP_DXIL=ON", "-DCMAKE_BUILD_TYPE=Release")
        Run $CMake @("--build", ".", "--config", "Release", "--target", "XenosRecomp")
    } finally { Pop-Location }
}
Write-Host "  XenosRecomp.exe: $XenosRecompExe" -ForegroundColor Green

# ── 3. dxil.dll must be beside the current process for DXIL signing ─────────
Step "Setting up dxil.dll"
$dxilDest = Join-Path (Get-Location) "dxil.dll"
if (-not (Test-Path $dxilDest)) {
    Copy-Item $DxilDll $dxilDest
    Write-Host "  Copied dxil.dll to working directory" -ForegroundColor Green
} else {
    Write-Host "  dxil.dll already present" -ForegroundColor DarkGray
}

# ── 4. Extract Xbox 360 shaders from .fxc files ──────────────────────────────
Step "Extracting Xbox 360 shaders from fxl_final"
if ((Test-Path $ExtractedShadersDir) -and (Get-ChildItem $ExtractedShadersDir -Recurse -File).Count -gt 0) {
    $existing = (Get-ChildItem $ExtractedShadersDir -Recurse -File).Count
    Write-Host "  extracted_shaders/ already has $existing files, skipping extraction." -ForegroundColor DarkGray
    Write-Host "  (Delete extracted_shaders\ to force re-extraction)" -ForegroundColor DarkGray
} else {
    New-Item -ItemType Directory -Force $ExtractedShadersDir | Out-Null
    Run $FxcExtractorExe @("--batch", $FxlFinalDir, $ExtractedShadersDir)
    $extracted = (Get-ChildItem $ExtractedShadersDir -Recurse -File).Count
    Write-Host "  Extracted $extracted shader files" -ForegroundColor Green
}

# ── 5. Generate shader_cache.cpp with DXIL ───────────────────────────────────
Step "Generating shader_cache.cpp (DXIL)"

# Back up existing shader_cache.cpp
if (Test-Path $ShaderCacheCpp) {
    $backup = "$ShaderCacheCpp.bak"
    Copy-Item $ShaderCacheCpp $backup -Force
    Write-Host "  Backed up existing shader_cache.cpp → shader_cache.cpp.bak"
}

Run $XenosRecompExe @($ExtractedShadersDir, $ShaderCacheCpp, $ShaderCommonH)

$size = (Get-Item $ShaderCacheCpp).Length / 1MB
Write-Host ("  Generated shader_cache.cpp ({0:F1} MB)" -f $size) -ForegroundColor Green

# ── 6. Compile post-process .dxil.h shaders ──────────────────────────────────
Step "Compiling post-process HLSL shaders to DXIL"
$ps1 = Join-Path $RepoRoot "tools\compile_dxil_shaders.ps1"
& $ps1
if ($LASTEXITCODE -ne 0) { throw "compile_dxil_shaders.ps1 failed" }

# ── 7. Summary ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host " All done! Next steps:" -ForegroundColor Green
Write-Host "   cmake . --preset x64-Clang-Release" -ForegroundColor White
Write-Host "   cmake --build .\out\build\x64-Clang-Release --target LibertyRecomp" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
