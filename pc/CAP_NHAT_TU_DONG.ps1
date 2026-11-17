param([string]$GameRoot=$PSScriptRoot)
$ErrorActionPreference='Stop'
$env:PSModulePath=(Join-Path $PSHOME 'Modules')+';'+$env:PSModulePath
$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName PresentationFramework
function Show-UpdateMessage([string]$Text, [switch]$Confirm, [switch]$Status) {
    $window = [System.Windows.Window]::new()
    $window.Title = 'HSO Offline'
    $window.Topmost = $true
    $window.Width = 390
    $window.SizeToContent = 'Height'
    $window.WindowStartupLocation = 'CenterScreen'
    $window.ResizeMode = 'NoResize'
    $content = [System.Windows.Controls.StackPanel]::new()
    $content.Margin = [System.Windows.Thickness]::new(20)
    $message = [System.Windows.Controls.TextBlock]::new()
    $message.Text = $Text
    $message.TextWrapping = 'Wrap'
    [void]$content.Children.Add($message)
    if ($Status) {
        $window.Content = $content
        $window.Show()
        [void]$window.Dispatcher.Invoke([Action]{}, [System.Windows.Threading.DispatcherPriority]::Render)
        return $window
    }
    $buttons = [System.Windows.Controls.StackPanel]::new()
    $buttons.Orientation = 'Horizontal'
    $buttons.HorizontalAlignment = 'Right'
    $buttons.Margin = [System.Windows.Thickness]::new(0,16,0,0)
    if ($Confirm) {
        $accept = [System.Windows.Controls.Button]::new()
        $accept.Content = 'Cập nhật'
        $accept.Padding = [System.Windows.Thickness]::new(12,4,12,4)
        $accept.Margin = [System.Windows.Thickness]::new(0,0,8,0)
        $accept.Add_Click({ param($button) [System.Windows.Window]::GetWindow($button).DialogResult = $true })
        [void]$buttons.Children.Add($accept)
    }
    $close = [System.Windows.Controls.Button]::new()
    $close.Content = if ($Confirm) { 'Để sau' } else { 'Đóng' }
    $close.IsCancel = $true
    $close.IsDefault = $true
    $close.Padding = [System.Windows.Thickness]::new(12,4,12,4)
    [void]$buttons.Children.Add($close)
    [void]$content.Children.Add($buttons)
    $window.Content = $content
    $window.ShowDialog()
}
$updateLock = [System.Threading.Mutex]::new($false, 'Local\HSOOfflinePCUpdate')
$ownsLock = $false
$statusWindow = $null
$log = Join-Path $GameRoot 'logs/update.log'
function Set-UpdateStatus([string]$Text) {
    Add-Content -LiteralPath $log -Encoding UTF8 -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' '+$Text)
    if ($statusWindow -and $statusWindow.IsVisible) {
        $statusWindow.Content.Children[0].Text = $Text
        [void]$statusWindow.Dispatcher.Invoke([Action]{}, [System.Windows.Threading.DispatcherPriority]::Render)
    }
}
try {
    try { $ownsLock = $updateLock.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $ownsLock = $true }
    if (-not $ownsLock) { return }
    New-Item -ItemType Directory -Path (Join-Path $GameRoot 'logs') -Force | Out-Null
    $manifest=Invoke-RestMethod -Uri 'https://github.com/zuzongdnt/hso-offline-tools/releases/latest/download/update.json' -TimeoutSec 20
    $versionFile=Join-Path $GameRoot 'offline-version.txt'
    $current=if(Test-Path -LiteralPath $versionFile){[int](Get-Content -LiteralPath $versionFile -Raw)}else{22}
    if([int]$manifest.version -le $current){Show-UpdateMessage 'Bạn đang dùng bản mới nhất.' | Out-Null;return}
    $url=[string]$manifest.pc.url
    if(-not $url.StartsWith('https://github.com/zuzongdnt/hso-offline-tools/releases/download/')){throw 'Link cập nhật không hợp lệ.'}
    $answer=Show-UpdateMessage ('Tải và cài bản '+$manifest.version+'? Game sẽ lưu dữ liệu và đóng để cập nhật.') -Confirm
    if(!$answer){return}
    $staging=Join-Path $GameRoot ('updates/'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $staging -Force | Out-Null
    $zip=Join-Path $staging 'update.zip'
    $statusWindow=Show-UpdateMessage 'Đang tải bản cập nhật. Vui lòng chờ…' -Status
    Set-UpdateStatus 'Đang tải bản cập nhật. Vui lòng chờ…'
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing -TimeoutSec 300
    Set-UpdateStatus 'Đang kiểm tra và giải nén bản cập nhật…'
    if((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ine [string]$manifest.pc.sha256){throw 'File tải về chưa toàn vẹn. Hãy thử lại.'}
    Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $staging 'package')
    Set-UpdateStatus 'Đang lưu nhân vật, sao lưu và cài bản cập nhật…'
    & (Join-Path $staging 'package/CAP_NHAT.ps1') -GameRoot $GameRoot
    $statusWindow.Close()
    Set-UpdateStatus ('Đã cập nhật thành công bản '+$manifest.version+'.')
    Show-UpdateMessage ('Đã cập nhật thành công bản '+$manifest.version+'. Game đang mở lại.') | Out-Null
} catch {
    if ($statusWindow) { $statusWindow.Close() }
    if ($ownsLock) {
        $failure = $_
        $failure | Out-String | Add-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue
        Show-UpdateMessage ($failure.Exception.Message+"`nChi tiết: "+$log) | Out-Null
    }
    else { throw }
} finally {
    if ($ownsLock) { $updateLock.ReleaseMutex() }
    $updateLock.Dispose()
}
