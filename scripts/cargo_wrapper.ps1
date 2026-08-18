param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CargoArgs = @("check")
)

$ErrorActionPreference = "Stop"
$llvmMinGwBin = "C:\Users\Swastik Pandey\AppData\Local\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\llvm-mingw-20260616-ucrt-x86_64\bin"
$pathParts = $env:PATH -split ";" | Where-Object { $_ -and ($_ -notmatch "MinGW") }
$env:PATH = ($llvmMinGwBin, ($pathParts -join ";")) -join ";"

Set-Location "src-tauri"
rustup default stable-x86_64-pc-windows-gnullvm
cargo @CargoArgs

# Synchronize runtime DLLs into target release and debug folders
$targetBase = "C:\Users\Public\meli_target"
$runtimeDlls = @("libunwind.dll", "libc++.dll")
foreach ($folder in @("release", "debug")) {
    $dir = Join-Path $targetBase $folder
    if (Test-Path $dir) {
        foreach ($dll in $runtimeDlls) {
            $src = Join-Path $llvmMinGwBin $dll
            $dst = Join-Path $dir $dll
            if (Test-Path $src) {
                Copy-Item -Path $src -Destination $dst -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

