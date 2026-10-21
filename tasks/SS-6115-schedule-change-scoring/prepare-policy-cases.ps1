$ErrorActionPreference='Stop'
$root=$PSScriptRoot
function CopyObject($value){ $value|ConvertTo-Json -Depth 30|ConvertFrom-Json }
function ShiftTrip($trip,$minutes){$copy=CopyObject $trip;foreach($s in $copy.segments){foreach($field in @('departureTime','arrivalTime')){$s.$field=[datetime]::ParseExact($s.$field,'yyyy-MM-dd HH:mm',$null).AddMinutes($minutes).ToString('yyyy-MM-dd HH:mm')}};return $copy}
function Segment($id,$from,$to,$dep,$arr,$duration){[pscustomobject]@{segmentId=$id;departureAirportCode=$from;arrivalAirportCode=$to;departureTime=$dep;arrivalTime=$arr;duration=$duration;marketingAirline='BA';operatingAirline='BA';flightNumber=([string](100+$id));bookingClass='Y';cabin='Y';status='HK';scheduleChange=$true}}
$original=[pscustomobject]@{tripId=1;duration=900;segments=@((Segment 1 'JFK' 'LHR' '2026-12-20 18:00' '2026-12-21 06:00' 420),(Segment 2 'LHR' 'CDG' '2026-12-21 08:00' '2026-12-21 10:00' 60))}
$reroute=ShiftTrip $original 30
$reroute.segments[0].arrivalAirportCode='LGW';$reroute.segments[1].departureAirportCode='LGW'
$ba=[pscustomobject]@{gds='S';pcc='1A1J';issueDate='2024-10-13';paxCnt=1;debug=$true;validatingCarrier='BA';cabin='Y';trips=@($original);expertTrips=@($reroute)}
$ba|ConvertTo-Json -Depth 30|Set-Content -Encoding utf8 (Join-Path $root 'tc05-true-request.json')
$ua=CopyObject $ba;$ua.validatingCarrier='UA';foreach($t in @($ua.trips)+@($ua.expertTrips)){foreach($s in $t.segments){$s.marketingAirline='UA';$s.operatingAirline='UA'}}
$ua|ConvertTo-Json -Depth 30|Set-Content -Encoding utf8 (Join-Path $root 'tc06-false-request.json')
$same=ShiftTrip $original 1440
$extra=[pscustomobject]@{tripId=1;duration=900;segments=@((Segment 1 'JFK' 'LHR' '2026-12-20 18:00' '2026-12-21 06:00' 420),(Segment 2 'LHR' 'AMS' '2026-12-21 07:00' '2026-12-21 09:00' 60),(Segment 3 'AMS' 'CDG' '2026-12-21 10:00' '2026-12-21 11:30' 90))}
$tc08=CopyObject $ba;$tc08.expertTrips=@($reroute,$same,$extra);$tc08|ConvertTo-Json -Depth 30|Set-Content -Encoding utf8 (Join-Path $root 'tc08-shapes-request.json')
$tc09=CopyObject $ba;foreach($s in $tc09.trips[0].segments){$s.marketingAirline='AA';$s.operatingAirline='AA'}
$u1=ShiftTrip $reroute 90;foreach($s in $u1.segments){$s.marketingAirline='AA';$s.operatingAirline='AA'}
$u5=CopyObject $reroute;foreach($s in $u5.segments){$s.marketingAirline='BA';$s.operatingAirline='AA'}
$tc09.expertTrips=@($u1,$u5);$tc09|ConvertTo-Json -Depth 30|Set-Content -Encoding utf8 (Join-Path $root 'tc09-carriers-request.json')
foreach($branch in @('cabin','flex','booking')){$candidate=CopyObject $ba;if($branch -eq 'cabin'){$candidate.expertTrips[0].segments[1].cabin='C'}elseif($branch -eq 'flex'){$candidate.expertTrips=@((ShiftTrip $reroute 4320))}else{foreach($s in $candidate.expertTrips[0].segments){$s.bookingClass='J'}};$candidate|ConvertTo-Json -Depth 30|Set-Content -Encoding utf8 (Join-Path $root ('tc10-'+$branch+'-request.json'))}
Write-Output 'Prepared synthetic expert fixtures, not asserted live flight schedules. Every segment scheduleChange=true.'
