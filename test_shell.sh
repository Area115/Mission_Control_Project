#!/bin/bash
# ============================================================
#  Commander Mission Control - Multi Mission Rotating Token Test
# ============================================================

BASE_URL="http://localhost:8000"

# ---- Colors ----
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Commander Mission Control - Multi Mission Rotating Token Test${NC}"
echo "================================================================"

# ---- Check Commander ----
if ! curl -s "$BASE_URL/" >/dev/null; then
  echo -e "${RED}Commander not reachable! Make sure backend is running.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Commander reachable.${NC}"

# ---- Data ----
soldiers=(1 2)
objectives=(
  "Secure Tiger Hill" "Inspect Outpost" "Patrol Perimeter"
  "Monitor Radio Signals" "Defend Checkpoint"
  "Survey Supply Lines" "Scout North Sector"
  "Repair Communication Tower" "Guard Ammunition Depot"
  "Assist Civilian Evacuation"
)
priorities=("LOW" "MEDIUM" "HIGH")

declare -A mission_ids
declare -A mission_soldiers
declare -A mission_objectives
declare -A mission_status
declare -A initial_tokens
declare -A final_tokens

# ---- Helper to shorten JWT ----
short_token() {
  local token="$1"
  if [ ${#token} -gt 20 ]; then
    echo "${token:0:10}...${token: -10}"
  else
    echo "$token"
  fi
}

# ---- Assign Missions ----
echo -e "\nAssigning 10 missions alternately to Soldier 1 and 2...\n"

for ((i = 0; i < 10; i++)); do
  sid="${soldiers[$((i % 2))]}"
  objective="${objectives[$i]}"
  priority="${priorities[$((i % 3))]}"

  body=$(jq -n --arg sid "$sid" --arg obj "$objective" --arg pri "$priority" \
    '{soldier_id: $sid, objective: $obj, priority: $pri}')

  resp=$(curl -s -X POST "$BASE_URL/missions" -H "Content-Type: application/json" -d "$body")
  mid=$(echo "$resp" | jq -r '.mission_id')

  if [ "$mid" != "null" ]; then
    mission_ids["$mid"]="$mid"
    mission_soldiers["$mid"]="$sid"
    mission_objectives["$mid"]="$objective"
    mission_status["$mid"]="QUEUED"
    echo -e "🎯 Mission assigned → Soldier ${sid} | ${objective} | ID: ${mid}"
  else
    echo -e "${RED}❌ Failed assigning mission to Soldier ${sid}${NC}"
  fi
  sleep 1
done

# ---- Initial Mission Overview ----
echo -e "\n${YELLOW}Initial Mission Overview:${NC}\n"
printf "%-10s %-30s %-12s %-25s\n" "Soldier" "Objective" "Status" "Token ID"
printf "%-10s %-30s %-12s %-25s\n" "--------" "----------------------------" "------------" "-------------------------"

for mid in "${!mission_ids[@]}"; do
  sid="${mission_soldiers[$mid]}"
  objective="${mission_objectives[$mid]}"
  token=$(curl -s "$BASE_URL/auth/token/$sid" | jq -r '.token')
  initial_tokens["$sid"]="$token"
  tok_short=$(short_token "$token")
  printf "%-10s %-30s %-12s %-25s\n" "$sid" "$objective" "QUEUED" "$tok_short"
done

# ---- Live Mission Tracking ----
echo -e "\n${YELLOW}Starting live status tracking...${NC}\n"
completed=false
check=1

while [ "$completed" = false ]; do
  echo "------ Check #$check ------"
  printf "%-10s %-30s %-12s\n" "Soldier" "Objective" "Status"
  printf "%-10s %-30s %-12s\n" "--------" "----------------------------" "------------"

  completed=true
  for mid in "${!mission_ids[@]}"; do
    sid="${mission_soldiers[$mid]}"
    objective="${mission_objectives[$mid]}"
    status_resp=$(curl -s "$BASE_URL/missions/$mid" | jq -r '.status')
    mission_status["$mid"]="$status_resp"

    case "$status_resp" in
    "COMPLETED") color=$GREEN ;;
    "FAILED") color=$RED ;;
    "IN_PROGRESS") color=$YELLOW ;;
    *) color=$NC ;;
    esac

    echo -e "$(printf '%-10s %-30s %-12s' "$sid" "$objective" "${color}${status_resp}${NC}")"

    if [ "$status_resp" != "COMPLETED" ] && [ "$status_resp" != "FAILED" ]; then
      completed=false
    fi
  done

  echo "--------------------------------------------"
  [ "$completed" = false ] && sleep 5 && ((check++))
done

# ---- Final Token Snapshot ----
echo -e "\n${YELLOW}Final Token Snapshot:${NC}\n"
printf "%-10s %-30s %-12s %-25s %-15s\n" "Soldier" "Objective" "Status" "Token ID" "Token Changed?"
printf "%-10s %-30s %-12s %-25s %-15s\n" "--------" "----------------------------" "------------" "-------------------------" "----------------"

for mid in "${!mission_ids[@]}"; do
  sid="${mission_soldiers[$mid]}"
  objective="${mission_objectives[$mid]}"
  status="${mission_status[$mid]}"
  final_token=$(curl -s "$BASE_URL/auth/token/$sid" | jq -r '.token')
  final_tokens["$sid"]="$final_token"

  initial="${initial_tokens[$sid]}"
  changed="NO"
  if [ "$initial" != "$final_token" ]; then
    changed="YES"
  fi

  tok_short=$(short_token "$final_token")
  printf "%-10s %-30s %-12s %-25s %-15s\n" "$sid" "$objective" "$status" "$tok_short" "$changed"
done

echo -e "\n${GREEN}All missions completed successfully!${NC}"
