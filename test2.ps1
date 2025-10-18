$BASE_URL = "http://localhost:8000"

Write-Host "Commander Mission Control - Multi Mission Rotating Token Test"
Write-Host "================================================================`n"

# 1) Health check
try {
    $ping = Invoke-RestMethod -Uri "$BASE_URL/" -Method Get
    Write-Host "Commander says: $($ping.message)"
}
catch {
    Write-Host "Commander not reachable! Make sure the backend is running."
    exit
}

# 2) Data
$soldiers   = @(1, 2)
$objectives = @(
    "Secure Tiger Hill", "Inspect Outpost", "Patrol Perimeter",
    "Monitor Radio Signals", "Defend Checkpoint",
    "Survey Supply Lines", "Scout North Sector",
    "Repair Communication Tower", "Guard Ammunition Depot",
    "Assist Civilian Evacuation"
)
$priorities = @("LOW", "MEDIUM", "HIGH")

$missions   = @()
$initialTokens = @{}
$finalTokens   = @{}

# Helper - Shorten token for readability
function ShortToken {
    param($token)
    if ($token.Length -gt 20) {
        return ($token.Substring(0, 10) + "..." + $token.Substring($token.Length - 10))
    } else {
        return $token
    }
}

# 3) Assign missions alternately (1,2,1,2...)
Write-Host "`nAssigning 10 missions alternately to Soldier 1 and 2...`n"

for ($i = 0; $i -lt 10; $i++) {
    $sid       = $soldiers[$i % 2]
    $objective = $objectives[$i]
    $priority  = $priorities[$i % 3]

    $body = @{
        "soldier_id" = "$sid"
        "objective"  = "$objective"
        "priority"   = "$priority"
    } | ConvertTo-Json

    try {
        $resp = Invoke-RestMethod -Uri "$BASE_URL/missions" -Method Post -Body $body -ContentType "application/json"
        $mid  = $resp.mission_id
        $missions += [PSCustomObject]@{
            soldier_id = $sid
            mission_id = $mid
            objective  = $objective
            status     = "QUEUED"
        }
        Write-Host ("Mission assigned -> Soldier {0} | {1} | ID: {2}" -f $sid, $objective, $mid)
    }
    catch {
        Write-Host "Failed assigning mission to Soldier $sid"
    }

    Start-Sleep -Seconds 1
}

# 4️⃣ Initial Snapshot Table
Write-Host "`nInitial Mission Overview:`n"
Write-Host ("{0,-10} {1,-30} {2,-12} {3}" -f "Soldier", "Objective", "Status", "Token ID")
Write-Host ("{0,-10} {1,-30} {2,-12} {3}" -f "--------", "----------------------------", "------------", "----------------------------")

foreach ($m in $missions) {
    try {
        $tokenResp = Invoke-RestMethod -Uri "$BASE_URL/auth/token/$($m.soldier_id)" -Method Get
        $token = $tokenResp.token
        $initialTokens[$m.soldier_id] = $token
        $tokenShort = ShortToken $token
    } catch {
        $tokenShort = "<N/A>"
    }

    Write-Host ("{0,-10} {1,-30} {2,-12} {3}" -f $m.soldier_id, $m.objective, $m.status, $tokenShort)
}
Write-Host ""

# 5️⃣ Real-Time Updates Table
Write-Host "Starting live status tracking...`n"
$completed = $false
$check = 1

while (-not $completed) {
    Write-Host "------ Check #$check ------"
    Write-Host ("{0,-10} {1,-30} {2}" -f "Soldier", "Objective", "Status")
    Write-Host ("{0,-10} {1,-30} {2}" -f "--------", "----------------------------", "------------")

    $completed = $true

    foreach ($m in $missions) {
        try {
            $status = Invoke-RestMethod -Uri "$BASE_URL/missions/$($m.mission_id)" -Method Get
            $m.status = $status.status
        } catch {
            $m.status = "UNKNOWN"
        }

        Write-Host ("{0,-10} {1,-30} {2}" -f $m.soldier_id, $m.objective, $m.status)
        if ($m.status -ne "COMPLETED") { $completed = $false }
    }

    Write-Host "--------------------------------------------`n"
    if ($completed) { break }
    $check++
    Start-Sleep -Seconds 5
}

# 6️⃣ Final Token Snapshot + Comparison
Write-Host "`nFinal Token Snapshot:`n"
Write-Host ("{0,-10} {1,-30} {2,-12} {3,-25} {4}" -f "Soldier", "Objective", "Status", "Token ID", "Token Changed?")
Write-Host ("{0,-10} {1,-30} {2,-12} {3,-25} {4}" -f "--------", "----------------------------", "------------", "-------------------------", "----------------")

foreach ($m in $missions | Sort-Object soldier_id) {
    try {
        $finalTokenResp = Invoke-RestMethod -Uri "$BASE_URL/auth/token/$($m.soldier_id)" -Method Get
        $finalTokens[$m.soldier_id] = $finalTokenResp.token
        $finalShort = ShortToken $finalTokens[$m.soldier_id]
        $initialShort = ShortToken $initialTokens[$m.soldier_id]
        $changed = if ($initialTokens[$m.soldier_id] -ne $finalTokens[$m.soldier_id]) { "YES" } else { "NO" }
    } catch {
        $finalShort = "<N/A>"
        $changed = "ERROR"
    }

    Write-Host ("{0,-10} {1,-30} {2,-12} {3,-25} {4}" -f $m.soldier_id, $m.objective, $m.status, $finalShort, $changed)
}

Write-Host "`nAll missions completed successfully!"
