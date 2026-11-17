$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'BAT_DAU.ps1') -ServerOnly
$config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'server/hso.conf')
$portLine=$config | Where-Object {$_ -match '^port\s*:'} | Select-Object -First 1
$gamePort=[int]($portLine -split ':',2)[1]
$toolsPort=if($gamePort -eq 19140){19141}else{19140}
Start-Process ('http://127.0.0.1:'+$toolsPort+'/')
