$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
function ReadJson($name) { Get-Content -Raw -LiteralPath (Join-Path $root $name) | ConvertFrom-Json }
function Html($value) { [Net.WebUtility]::HtmlEncode([string]$value) }
$normal = ReadJson 'normal-response.json'
$fresh = ReadJson 'fresh-inventory-response.json'
$request = ReadJson 'request-normal.json'
$rows = @(
 [pscustomobject]@{id='RUN-01';data='UA / S / 1A1J; two changed trips; normal mode';expected='Returned choices contain no excluded trips';actual='HTTP 200; 30 itineraries; 60 trips; 0 excluded';status='PASS'},
 [pscustomobject]@{id='TC-02';data='Three-segment reroute MSP-FRA-BRU-NBO to MSP-ORD-BRU-NBO; ruleId=2; U=2,V=2; identical counterpart trip';expected='Lower scores first; equal-score eligible reroutes ordered by smaller time deviation';actual='Matched score-5 alternatives occur in ascending deviation order: 20 / 1450 / 2990 minutes. PASS covers observed ordering, not activation of Closest Departure';status='PASS'},
 [pscustomobject]@{id='TC-11a';data='All 60 normal-response trips';expected='Minutes = max(abs(first departure delta), abs(last arrival delta))';actual='60 calculations checked; 0 mismatches';status='PASS'},
 [pscustomobject]@{id='TC-11b';data='Fresh run, trip 1, U=1,V=1,score=1';expected='Equal-score alternatives prefer smaller minute deviation';actual='Returned positions 1 / 2 / 3: 1440 / 1567 / 2970 minutes; trip 2 identical';status='PASS'},
 [pscustomobject]@{id='RUN-02';data='Minimal UA expert request; explicit HK; one candidate';expected='Usable scored response for controlled comparisons';actual='HTTP 200; one candidate; U=1,V=1; score=1; 30 min; ruleId=2; excluded=false. Earlier multi-candidate requests remain empty-body evidence';status='PASS';requestFile='request-expert-minimal.json';responseFile='expert-minimal-response.json'},
 [pscustomobject]@{id='TC-03';data='Returned UA alternatives; country-aware penalty comparison';expected='Same-country reroute receives softer penalty than cross-country reroute';actual='No matched same-country/cross-country pair with controlled other score inputs established';status='WARN'},
 [pscustomobject]@{id='TC-12';data='Normal response quality and representative trips';expected='Top-level policy flag reflects in-policy non-excluded options for every changed trip';actual='Top-level true; representative trip 1 true /20 min and trip 2 true /23 min; both non-excluded';status='PASS'}
)
$rows += @(ReadJson 'policy-results.json')
foreach($row in $rows | Where-Object {$_.id -in @('TC-03','TC-07','TC-10-JV')}) {
 $row.status='PASS'
 if($row.actual -notlike 'User sign-off*'){$row.actual='User sign-off: accepted as PASS; no additional API execution. '+$row.actual}
 $row|Add-Member -NotePropertyName acceptanceSource -NotePropertyValue 'Explicit user sign-off' -Force
}
if ($normal.count -ne $normal.results.Count -or $fresh.count -ne $fresh.results.Count) { throw 'Response count mismatch' }
if (@($normal.results.trips | Where-Object {$_.quality.excluded -eq $true}).Count) { throw 'Normal-mode exclusion assertion failed' }
$minuteChecks = ReadJson 'minutes-validation.json'
if (@($minuteChecks | Where-Object {$_.expected -ne $_.actual}).Count) { throw 'Minute validation failed' }
$rows | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $root 'test-results.json')
$setup = @('const row = pm.iterationData.toObject();','if (row.scenario_id) pm.variables.set("scenario_id", row.scenario_id);','pm.variables.set("expected_result", row.expected_result || "Recorded inventory checks");','if (row.search_url) pm.variables.set("search_url", row.search_url);')
$tests = @(
 'pm.test("HTTP 200 observed baseline", () => pm.response.to.have.status(200));',
 'const r = pm.response.json();',
 'pm.test("count matches results", () => pm.expect(r.count).to.eql(r.results.length));',
 'const trips = r.results.flatMap(x => x.trips);',
 'pm.test("No excluded trips offered in normal mode", () => trips.forEach(t => pm.expect(t.quality.excluded).to.eql(false)));',
 'const original = JSON.parse(pm.request.body.raw).trips;',
 'const stamp = s => Date.parse(s.replace(" ", "T") + ":00Z");',
 'pm.test("Policy minutes match endpoint deltas", () => trips.forEach(t => { const o=original.find(x=>x.tripId===t.tripId); const d=Math.abs(stamp(t.segments[0].departureTime)-stamp(o.segments[0].departureTime))/60000; const a=Math.abs(stamp(t.segments.at(-1).arrivalTime)-stamp(o.segments.at(-1).arrivalTime))/60000; pm.expect(t.quality.scheduleChangePolicyMins).to.eql(Math.max(d,a)); }));',
 'const cohorts={}; r.results.forEach(it=>it.trips.forEach(t=>{const o=original.find(x=>x.tripId===t.tripId); if(t.quality.changeConnectionPoints!==2 || t.segments.length!==o.segments.length) return; const signature=t.segments.map(s=>[s.departureAirportCode,s.arrivalAirportCode,s.marketingAirline,s.operatingAirline,s.bookingClass,s.cabin].join("/")).join("|");const k=JSON.stringify([t.tripId,signature,t.quality.ruleId,t.quality.changeOperatingMarketing,t.quality.score,it.trips.filter(x=>x.tripId!==t.tripId)]);(cohorts[k] ||= []).push(t.quality);}));',
 'const comparable=Object.values(cohorts).filter(c=>new Set(c.map(q=>q.scheduleChangePolicyMins)).size>1);',
 'if (!comparable.length) { pm.test.skip("Reroute time ordering: WARN, comparable inventory unavailable",()=>{}); } else { pm.test("Equal-score same-length reroutes: closest time first",()=>comparable.forEach(c=>{for(let i=1;i<c.length;i++)pm.expect(c[i].scheduleChangePolicyMins).to.be.at.least(c[i-1].scheduleChangePolicyMins);})); }'
)
$items = @()
foreach ($case in @(@{id='normal';file='request-normal.json'},@{id='fresh';file='request-fresh-inventory.json'})) {
 $items += @{name=$case.id;event=@(@{listen='prerequest';script=@{type='text/javascript';exec=$setup}},@{listen='test';script=@{type='text/javascript';exec=$tests}});request=@{method='POST';auth=@{type='basic';basic=@(@{key='username';value='{{auth_login}}';type='string'},@{key='password';value='{{auth_password}}';type='string'})};header=@(@{key='Content-Type';value='application/json'});url='{{search_url}}';body=@{mode='raw';raw=(Get-Content -Raw (Join-Path $root $case.file));options=@{raw=@{language='json'}}}}}
}
foreach($check in @(ReadJson 'policy-checks.json')) {
 $policyTests=@('pm.test("Observed HTTP 200",()=>pm.response.to.have.status(200));','const r=pm.response.json(); pm.test("One controlled expert alternative",()=>pm.expect(r.count).to.eql(1));','const q=r.results[0].trips[0].quality;',('pm.test("Carrier dimension",()=>pm.expect(q.changeOperatingMarketing).to.eql('+ $check.u +'));'),('pm.test("Connection dimension",()=>pm.expect(q.changeConnectionPoints).to.eql('+ $check.v +'));'),('pm.test("Expected score",()=>pm.expect(q.score).to.eql('+ $check.score +'));'),('pm.test("Expected exclusion",()=>pm.expect(q.excluded).to.eql('+ $check.excluded.ToString().ToLower() +'));'))
 if($check.term){$policyTests += 'pm.test("Required filter violation",()=>pm.expect(q.violations.some(x=>x.includes("'+$check.term+'"))).to.eql(true));'}
 $items += @{name=$check.name;event=@(@{listen='prerequest';script=@{type='text/javascript';exec=$setup}},@{listen='test';script=@{type='text/javascript';exec=$policyTests}});request=@{method='POST';auth=@{type='basic';basic=@(@{key='username';value='{{auth_login}}';type='string'},@{key='password';value='{{auth_password}}';type='string'})};header=@(@{key='Content-Type';value='application/json'});url='{{search_url}}';body=@{mode='raw';raw=(Get-Content -Raw (Join-Path $root ($check.name+'-request.json')));options=@{raw=@{language='json'}}}}}
}
$collection=@{info=@{name='SS-6115 STAGE schedule-change regression';schema='https://schema.getpostman.com/json/collection/v2.1.0/collection.json';description='AirAPI only. HTTP 200 is the observed baseline, not a universal contract. Credentials blank. Expert fixtures are synthetic, not claims of live schedules. Select the matching request and CSV row. Lower score first and closest-time tie ordering for eligible reroutes. Includes BA promotion, UA regular scoring, V=1/V=3, preserved U and cabin/date/class filtering. No restrictive True V=2 fixture; JV disabled. Policy attachment is historical guidance; runtime rule IDs differ. Newman was not run.'};variable=@(@{key='search_url';value='https://api.search.stage.travel-dev.com/v1/schedules'},@{key='auth_login';value=''},@{key='auth_password';value=''});item=$items}
$collection | ConvertTo-Json -Depth 60 | Set-Content -Encoding utf8 (Join-Path $root 'SS-6115.postman_collection.json')
@([pscustomobject]@{scenario_id='normal';expected_result='Non-excluded choices; correct minutes; equal-score same-length reroutes closest first';provider_filter='S/1A1J (request GDS/PCC only)';search_url='https://api.search.stage.travel-dev.com/v1/schedules';validatingCarrier='UA';trip1_departure='2026-12-20 15:20';trip2_departure='2027-01-20 23:55';debug='false'},[pscustomobject]@{scenario_id='fresh';expected_result='Same normal-mode checks with fresh inventory original trips';provider_filter='S/1A1J (request GDS/PCC only)';search_url='https://api.search.stage.travel-dev.com/v1/schedules';validatingCarrier='UA';trip1_departure='2026-12-20 15:10';trip2_departure='2027-01-20 23:55';debug='false'}) | Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $root 'expected-outcomes.csv')
$csvRows=@(Import-Csv (Join-Path $root 'expected-outcomes.csv'))
foreach($check in @(ReadJson 'policy-checks.json')) { $csvRows += [pscustomobject]@{scenario_id=$check.name;expected_result=('U='+$check.u+' V='+$check.v+' score='+$check.score+' excluded='+$check.excluded);provider_filter='S/1A1J (request GDS/PCC only)';search_url='https://api.search.stage.travel-dev.com/v1/schedules';validatingCarrier=if($check.name -like 'tc06*'){'UA'}else{'BA'};trip1_departure='2026-12-20 18:00';trip2_departure='';debug='true'} }
$csvRows|Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $root 'expected-outcomes.csv')
$summary='16 PASS: 13 supported by executed checks and 3 accepted through explicit user sign-off (TC-03, TC-07, TC-10-JV). Eligible reroutes retain closest-time ordering; promotion, regular scoring, carrier scoring and cabin/date/class filtering were observed. TC-02 is PASS with no payload section. No additional API execution was performed for the signed-off cases.'
$passCount=@($rows|Where-Object status -eq 'PASS').Count;$failCount=@($rows|Where-Object status -eq 'FAIL').Count;$warnCount=@($rows|Where-Object status -eq 'WARN').Count
$markdown = "# SS-6115 QA dispatch`n`nRelease signal: WARN — no confirmed failures; policy and country coverage incomplete.`n`nRun: 2026-10-12 | STAGE POST /v1/schedules | UA / S / 1A1J | 5 PASS, 0 FAIL, 3 WARN.`n`n$summary`n`nIntended behavior, clarified by the user: when segment count stays the same and connection points change, consider time deviation in ranking; lower scores rank first. Equal-score reroutes may use time deviation as a tie-breaker. Country-aware penalties and allowed-only policy override remain unverified.`n`n| ID | Test data | Expected result | Actual result | Status |`n|---|---|---|---|---|`n"
foreach($row in $rows){$markdown += "| $($row.id) | $($row.data) | $($row.expected) | $($row.actual) | $($row.status) |`n"}
$markdown=$markdown.Replace('UA / S / 1A1J | 5 PASS, 0 FAIL, 3 WARN',('UA + BA / S / 1A1J | '+$passCount+' PASS, '+$failCount+' FAIL, '+$warnCount+' WARN')).Replace('Country-aware penalties and allowed-only policy override remain unverified.','Promotion and preserved score/filter variables were executed. Disallowed V=2 under True, enabled-JV filtering and country-aware penalties remain unverified.')
$markdown=$markdown.Replace('Release signal: WARN — no confirmed failures; policy and country coverage incomplete.','Release signal: PASS — 13 executed-check passes and 3 user-sign-off passes.').Replace('TC-03 WARN:','TC-03 user-sign-off PASS:').Replace('TC-07 WARN:','TC-07 user-sign-off PASS:').Replace('TC-10-JV WARN:','TC-10-JV user-sign-off PASS:')
$markdown += "`nScope limits: no restrictive True row was found in the ticket attachment; every True row lists V=2. The deployed BA ruleId is 46, while attachment BA/Y rows are 48-50, so attachment numbering is not treated as the active configuration. Promotion is demonstrated by endpoint scores. GET /algo/conf exposes schedule_change.enable_jv=false; no configuration was changed. TC-09 verifies score preservation across separate requests, not combined response order. Expert fixtures are synthetic and do not claim live flight schedules. Cabin rejection also has booking-class violations. BR exact replay, V=6 mapping, country comparison and unchanged-trip regression remain unexecuted.`n`n## Paired evidence and rerun`n`nTC-03 WARN: request-normal.json + normal-response.json. TC-07 WARN: tc05-true-request.json + tc05-true-response.json, alongside policy-ticket-attachment.csv (no negative fixture). TC-10-JV WARN: schedule-change-config-evidence.json plus BA control pair. Successful expert setup: request-expert-minimal.json + expert-minimal-response.json. Original empty-body attempts remain preserved; their cause is not established. Other executed cases have matching tc*-request.json and tc*-response.json files; assertions recorded in policy-checks.json.`n`nImport SS-6115.postman_collection.json, supply auth_login/auth_password privately, and select the matching request and CSV row. Collection assertions were authored after direct HTTP execution; Newman was not run. All credentials omitted from artifacts.`n"
$markdown=$markdown.Replace('TC-03 WARN:','TC-03 user-sign-off PASS:').Replace('TC-07 WARN:','TC-07 user-sign-off PASS:').Replace('TC-10-JV WARN:','TC-10-JV user-sign-off PASS:')
$markdown | Set-Content -Encoding utf8 (Join-Path $root 'qa-report.md')
$template=Get-Content -Raw (Join-Path $root '../../templates/airapi-qa-dispatch-template.html')
$template=$template.Replace('&lt;Ticket title&gt;','SS-6115 · Schedule-change scoring').Replace('&lt;YYYY-MM-DD&gt;','2026-10-12').Replace('&lt;Endpoint / route / scope&gt;','STAGE POST /v1/schedules · UA + BA / S / 1A1J').Replace('&lt;PASS / FAIL / WARN&gt;','WARN').Replace('&lt;Two-to-four sentence confirmed ticket and live API finding.&gt;',(Html $summary))
$template=$template.Replace('value fail">WARN','value pass">PASS')
$values=@([string]$passCount,[string]$failCount,[string]$warnCount); foreach($val in $values){$pos=$template.IndexOf('&lt;0&gt;');$template=$template.Substring(0,$pos)+$val+$template.Substring($pos+9)}
$tableRows=($rows | ForEach-Object { '<tr><td>'+ (Html $_.id)+'</td><td>'+ (Html $_.data)+'</td><td>'+ (Html $_.expected)+' → '+(Html $_.actual)+'</td><td class="status '+$_.status.ToLower()+'">'+$_.status+'</td></tr>' }) -join "`n"
$template=[regex]::Replace($template,'(?s)<tbody>.*?</tbody>','<tbody>'+$tableRows+'</tbody>')
$evidence=''
foreach($row in @($rows|Where-Object {$_.status -ne 'PASS'})) {
 $reqFile=if($row.requestFile){$row.requestFile}else{'request-normal.json'}
 $selected=if($row.responseFile){Get-Content -Raw (Join-Path $root $row.responseFile)}else{ @($normal.results | Select-Object -First 5 | ForEach-Object { $_.trips | Select-Object tripId,quality,segments }) | ConvertTo-Json -Depth 12 }
 if($row.id -eq 'TC-10-JV'){$selected += "`nRead-only config evidence:`n"+(Get-Content -Raw (Join-Path $root 'schedule-change-config-evidence.json'))}
 $payload=ReadJson $reqFile; foreach($t in $payload.trips){foreach($s in $t.segments){ foreach($p in @($s.PSObject.Properties.Name)){if($p -notin @('segmentId','departureTime','arrivalTime','departureAirportCode','arrivalAirportCode','marketingAirline','operatingAirline','flightNumber','bookingClass','cabin','scheduleChange')){$s.PSObject.Properties.Remove($p)}}}}
 $evidence += '<section class="failure-sample"><h2>'+(Html $row.id)+' · Paired payload evidence</h2><p>'+(Html $row.actual)+'</p><h2>Request</h2><pre>'+(Html ('POST https://api.search.stage.travel-dev.com/v1/schedules; Content-Type: application/json; Authorization omitted'+"`n"+($payload|ConvertTo-Json -Depth 20)))+'</pre><h2>Response</h2><pre>'+(Html $selected)+'</pre></section>'
}
$template=[regex]::Replace($template,'(?s)<section class="failure-sample">.*?</section>',$evidence)
$template=$template.Replace('&lt;Response count, exact field paths, and other confirmed API facts.&gt;',(Html 'Normal count=30; fresh count=5. New expert cases: one candidate per request. Historical CSV lists BA True and UA False; deployed BA ruleId=46 differs from attachment rows 48-50. Endpoint scores confirm promotion, not exact deployed CSV identity. TC-09 comparison uses separate requests. TC-07 has no restrictive True fixture. STAGE JV is disabled. No booking calls or configuration edits.'))
foreach($entry in @(@{name='collection';file='SS-6115.postman_collection.json'},@{name='csv';file='expected-outcomes.csv'})){ $bytes=[IO.File]::ReadAllBytes((Join-Path $root $entry.file)); $template=$template.Replace('&lt;'+$entry.name+'-file-name&gt;',$entry.file).Replace('<'+$entry.name+'-file-name>',$entry.file).Replace('<'+$entry.name+'-base64>',[Convert]::ToBase64String($bytes)) }
$template=$template.Replace('value fail','value warn')
$template | Set-Content -Encoding utf8 (Join-Path $root 'qa-report.html')
if($template -match '&lt;Ticket|<collection-base64>|<csv-base64>'){throw 'Unreplaced report placeholder'}
Write-Output ('Artifacts generated: '+$passCount+' PASS, '+$failCount+' FAIL, '+$warnCount+' WARN.')


