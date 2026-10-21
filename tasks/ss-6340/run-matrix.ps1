$ErrorActionPreference = 'Stop'
$ticketDir = $PSScriptRoot
$runDir = Join-Path $ticketDir ('runs/' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-matrix')
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$runDir | Set-Content (Join-Path $ticketDir 'latest-matrix.txt')
$base = 'https://api.search.dev.travel-dev.com'
$mixes = @(
    @{name='1adt';adt=1;chd=0;inf=0},
    @{name='2adt';adt=2;chd=0;inf=0},
    @{name='adt-chd';adt=1;chd=1;inf=0},
    @{name='adt-inf';adt=1;chd=0;inf=1},
    @{name='adt-chd-inf';adt=1;chd=1;inf=1}
)
$matrix = @()
foreach ($type in @('OW','RT','MC')) {
    foreach ($mix in $mixes) {
        $id = $type.ToLower() + '-' + $mix.name
        $origin = if ($type -eq 'MC') {'LAX'} else {'AMS'}
        $destination = if ($type -eq 'MC') {'FRA'} else {'LHR'}
        $url = $base + '/brightsun/v1/search?tripType=' + $type + '&fl[0][o]=' + $origin + '&fl[0][d]=' + $destination + '&fl[0][dt]=2026-11-11&cabin=Y&adt=' + $mix.adt + '&chd=' + $mix.chd + '&inf=' + $mix.inf
        if ($type -eq 'RT') {$url += '&fl[1][o]=LHR&fl[1][d]=AMS&fl[1][dt]=2026-11-18'}
        if ($type -eq 'MC') {$url += '&fl[1][o]=MUC&fl[1][d]=LAX&fl[1][dt]=2026-11-18'}
        $url += '&limit=100'
        $existing = $null
        if ($id -eq 'rt-1adt') { $existing = (Get-Content (Join-Path $ticketDir 'latest-run.txt') -Raw).Trim() }
        if ($id -eq 'rt-2adt') { $existing = (Get-ChildItem (Join-Path $ticketDir 'runs') -Directory -Filter '*-rt-2adt' | Sort-Object Name -Descending | Select-Object -First 1).FullName }
        $caseDir = if ($existing) {$existing} else {Join-Path $runDir $id}
        $entry = [pscustomobject]@{scenario_id=$id;tripType=$type;adt=$mix.adt;chd=$mix.chd;inf=$mix.inf;search_url=$url;evidence=$caseDir;reused=[bool]$existing}
        $matrix += $entry
        $matrix | ConvertTo-Json -Depth 20 | Set-Content (Join-Path $runDir 'matrix.json') -Encoding utf8
        if ($existing) {Write-Output ($id + ': existing live evidence retained');continue}
        New-Item -ItemType Directory -Path $caseDir -Force | Out-Null
        [pscustomobject]@{method='GET';url=$url} | ConvertTo-Json | Set-Content (Join-Path $caseDir 'search-request.json') -Encoding utf8
        try {
            $search = Invoke-WebRequest -Uri $url -Method Get -NoProxy -SkipHttpErrorCheck -TimeoutSec 40
            $search.Content | Set-Content (Join-Path $caseDir 'search-response.json') -Encoding utf8
            [pscustomobject]@{status=[int]$search.StatusCode;receivedAt=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $caseDir 'search-meta.json')
            $data = $search.Content | ConvertFrom-Json -Depth 100
            if (-not $data.results.Count) {Write-Output ($id + ': Search HTTP ' + [int]$search.StatusCode + ', no selectable solution');continue}
            $selected = $data.results[0]
            $body = $selected | ConvertTo-Json -Depth 100
            $body | Set-Content (Join-Path $caseDir 'selected-solution.json') -Encoding utf8
            [pscustomobject]@{method='POST';url=($base+'/brightsun/v1/result');headers=@{'Content-Type'='application/json'};body=$selected} | ConvertTo-Json -Depth 100 | Set-Content (Join-Path $caseDir 'result-request.json') -Encoding utf8
            $result = Invoke-WebRequest -Uri ($base+'/brightsun/v1/result') -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -NoProxy -SkipHttpErrorCheck -TimeoutSec 40
            $result.Content | Set-Content (Join-Path $caseDir 'result-response.json') -Encoding utf8
            [pscustomobject]@{status=[int]$result.StatusCode;receivedAt=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $caseDir 'result-meta.json')
            $response = $result.Content | ConvertFrom-Json -Depth 100
            Write-Output ($id + ': Search ' + [int]$search.StatusCode + '/' + $data.results.Count + ' solutions; Result ' + [int]$result.StatusCode + '; pax=' + ($response.passengers.PSObject.Properties.Name -join ',') + '; total=' + $response.prices.totalPrice + ' ' + $response.currency)
        } catch {
            [pscustomobject]@{error=$_.Exception.Message;receivedAt=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $caseDir 'transport-error.json')
            Write-Output ($id + ': request/response unavailable: ' + $_.Exception.Message)
        }
    }
}
Write-Output ('Matrix evidence: ' + $runDir)
