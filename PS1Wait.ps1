Start-Sleep -Seconds 3.0

# wait for all other sub-processes to complete
while ((Get-CimInstance -Class Win32_Process | Where-Object { $_.ParentProcessID -eq $unity.Id -and $_.Name -ne 'VBCSCompiler.exe' }).count -gt 0) {
    Start-Sleep -Seconds 1.0
}
if (!$unity.HasExited) {
    Wait-Process -Id $unity.Id
}

exit $unity.ExitCode