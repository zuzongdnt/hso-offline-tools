param([Parameter(Mandatory=$true)][string]$GameRoot)
$ErrorActionPreference='Stop'
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$package=Join-Path $PSScriptRoot 'payload'
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'files.json') -Raw | ConvertFrom-Json
if(-not (Test-Path -LiteralPath (Join-Path $GameRoot 'BAT_DAU.ps1'))){throw 'Hãy chọn thư mục HSO Offline PC.'}
foreach($file in $manifest.files){
    $relative=[string]$file.path
    $target=[IO.Path]::GetFullPath((Join-Path $GameRoot $relative))
    if(-not $target.StartsWith($GameRoot.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Đường dẫn cập nhật không hợp lệ.'}
    $allowed=$relative -match '^server/data/' -or $relative -in @('server/target/HSO_Re_2-1.0-jar-with-dependencies.jar','client/hso_v403_Data/Managed/Assembly-CSharp.dll','CAP_NHAT_TU_DONG.ps1','DU_LIEU.ps1','offline-version.txt')
    if(-not $allowed){throw 'Gói cập nhật có file ngoài phạm vi game.'}
    $source=Join-Path $package $relative
    if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ine [string]$file.sha256){throw ('File cập nhật bị hỏng: '+$relative)}
}
$client=Join-Path $GameRoot 'client/hso_v403.exe'
$running=Get-Process hso_v403 -ErrorAction SilentlyContinue | Where-Object Path -eq $client
foreach($game in $running){[void]$game.CloseMainWindow();if(-not $game.WaitForExit(15000)){throw 'Hãy thoát game rồi chạy cập nhật lại.'}}
& (Join-Path $GameRoot 'TAT_SERVER.ps1')
$runtime=(Resolve-Path -LiteralPath (Join-Path $GameRoot 'runtime')).Path
$deadline=(Get-Date).AddSeconds(15)
do{
    $remaining=Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -and $_.ExecutablePath.StartsWith($runtime+'\',[StringComparison]::OrdinalIgnoreCase)}
    if($remaining){Start-Sleep -Milliseconds 300}
}while($remaining -and (Get-Date) -lt $deadline)
if($remaining){throw 'Game đang lưu dữ liệu. Hãy thử cập nhật lại sau.'}
$backup=Join-Path $GameRoot ('backups/offline'+$manifest.version+'-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $GameRoot 'database') -Destination $backup -Recurse
$changed=[Collections.Generic.List[string]]::new()
try{
    foreach($file in $manifest.files){
        $relative=[string]$file.path
        $target=Join-Path $GameRoot $relative
        if(Test-Path -LiteralPath $target){
            $saved=Join-Path $backup $relative
            New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
            Copy-Item -LiteralPath $target -Destination $saved
        }
        $changed.Add($relative)
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $package $relative) -Destination $target
    }
}catch{
    foreach($relative in $changed){
        $saved=Join-Path $backup $relative
        if(Test-Path -LiteralPath $saved){Copy-Item -LiteralPath $saved -Destination (Join-Path $GameRoot $relative)}
    }
    throw
}
Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+(Join-Path $GameRoot 'CHOI_OFFLINE.ps1')+'"') -WindowStyle Hidden
Write-Output ('Đã cập nhật. Sao lưu tại '+$backup)
