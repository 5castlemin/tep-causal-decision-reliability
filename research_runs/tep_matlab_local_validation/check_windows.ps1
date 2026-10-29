param([string]$OutputPath = '')
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$disk = Get-PSDrive C
$commands = @('matlab','mex','cl','gcc','clang') | ForEach-Object {
    $item = Get-Command $_ -ErrorAction SilentlyContinue | Select-Object -First 1
    [pscustomobject]@{name=$_; found=($null -ne $item); source=if ($item) {$item.Source} else {$null}}
}
$paths = @('C:\Program Files\MATLAB','C:\Program Files (x86)\MATLAB') | ForEach-Object { [pscustomobject]@{path=$_; exists=(Test-Path -LiteralPath $_)} }
$result = [ordered]@{os=$os.Caption; version=$os.Version; architecture=$os.OSArchitecture; memory_total_kib=$os.TotalVisibleMemorySize; memory_available_kib=$os.FreePhysicalMemory; cpu=$cpu.Name; cores=$cpu.NumberOfCores; logical_processors=$cpu.NumberOfLogicalProcessors; c_drive_free_bytes=$disk.Free; commands=$commands; common_paths=$paths; simulink='UNKNOWN until MATLAB licence test'; license='UNKNOWN until MATLAB licence test'; compiler_compatibility='UNKNOWN until mex check'}
$json=$result | ConvertTo-Json -Depth 5
if ($OutputPath) {if (Test-Path -LiteralPath $OutputPath) {throw 'Output file already exists'}; [System.IO.File]::WriteAllText($OutputPath,$json,[System.Text.UTF8Encoding]::new($false))} else { $json }
