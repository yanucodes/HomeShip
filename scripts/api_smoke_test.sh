#!/usr/bin/env bash
#
# HomeShip API smoke test.
#
# Drives the running API end-to-end with HTTPie, exercising the full lifecycle
# of a user, ship, membership, task and supply, and asserting the responses.
# It then adds a second user to the ship to prove shared crew visibility — both
# members see the same tasks and supplies, a deletion by either is visible to
# both — before tearing the whole fixture down.
#
# Requirements:
#   - The app running and reachable at $BASE_URL (default http://127.0.0.1:8000)
#   - httpie  (`http` on PATH)   -- https://httpie.io
#   - jq                          -- https://jqlang.github.io/jq
#
# Usage:
#   ./scripts/api_smoke_test.sh                              # local default
#   ./scripts/api_smoke_test.sh https://homeship-api.onrender.com   # remote
#   BASE_URL=http://127.0.0.1:8000 ./scripts/api_smoke_test.sh
#
# Exit code is 0 only if every assertion passed.

set -uo pipefail

# Precedence: first CLI argument, then $BASE_URL, then the local default.
BASE_URL="${1:-${BASE_URL:-http://127.0.0.1:8000}}"
BASE_URL="${BASE_URL%/}"   # tolerate a trailing slash on a pasted URL

# --- pretty output -----------------------------------------------------------
if [[ -t 1 ]]; then
  GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YELLOW=$'\033[0;33m'
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
  GREEN=""; RED=""; YELLOW=""; BOLD=""; DIM=""; RESET=""
fi

PASS_COUNT=0
FAIL_COUNT=0

step() { printf '\n%s== %s ==%s\n' "$BOLD" "$1" "$RESET"; }
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '  %s✓%s %s\n' "$GREEN" "$RESET" "$1"; }
fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf '  %s✗ %s%s\n' "$RED" "$1" "$RESET"
  [[ -n "${2:-}" ]] && printf '    %s%s%s\n' "$DIM" "$2" "$RESET"
}

assert_status() { # expected actual label
  if [[ "$2" == "$1" ]]; then pass "$3 (HTTP $2)"
  else fail "$3" "expected HTTP $1, got HTTP ${2:-<none>}; body: $BODY"; fi
}
assert_eq() { # expected actual label
  if [[ "$2" == "$1" ]]; then pass "$3"
  else fail "$3" "expected '$1', got '$2'"; fi
}
assert_ne() { # notexpected actual label
  if [[ "$2" != "$1" ]]; then pass "$3"
  else fail "$3" "expected something other than '$1'"; fi
}
assert_present() { # value label  -- fails on empty or literal "null"
  if [[ -n "$1" && "$1" != "null" ]]; then pass "$2"
  else fail "$2" "value missing (got '${1:-<empty>}')"; fi
}

# --- HTTP helper -------------------------------------------------------------
# Runs httpie, leaving the numeric status in STATUS and the JSON body in BODY.
STATUS=""
BODY=""
request() {
  local raw
  raw="$(http --ignore-stdin --pretty=none --print=hb "$@" 2>/dev/null)" || raw=""
  STATUS="$(printf '%s\n' "$raw" | sed -n '1s@^HTTP/[0-9.]* \([0-9]\{3\}\).*@\1@p')"
  BODY="$(printf '%s\n' "$raw" | awk 'body{print} /^[[:space:]]*$/{body=1}')"
}

jget() { printf '%s' "$BODY" | jq -r "$1" 2>/dev/null; }

# --- portable date arithmetic ------------------------------------------------
add_days() { # N  ->  YYYY-MM-DD, N days from today
  date -v+"${1}"d +%F 2>/dev/null || date -d "+${1} days" +%F
}

# --- preflight ---------------------------------------------------------------
command -v http >/dev/null 2>&1 || { echo "${RED}httpie ('http') not found.${RESET}"; exit 127; }
command -v jq   >/dev/null 2>&1 || { echo "${RED}jq not found.${RESET}"; exit 127; }

STAMP="$(date +%s)"
USERNAME="ada_${STAMP}"
EMAIL="ada_${STAMP}@example.com"
DISPLAY_NAME="Ada"
NEW_DISPLAY_NAME="Ada Lovelace"
PASSWORD="hunter2pass"

# Second crew member, added to the ship by the first user to prove that ships,
# tasks and supplies are shared across the crew.
USERNAME2="grace_${STAMP}"
EMAIL2="grace_${STAMP}@example.com"
DISPLAY_NAME2="Grace"
PASSWORD2="hopper2pass"

TODAY="$(date +%F)"
TASK_DUE_LATER="$(add_days 14)"     # > today+7 (initial task due), so postpone is valid
SUPPLY_DUE_FAR="$(add_days 10)"     # > yellow window (7d) -> green on creation
SUPPLY_DUE_NEAR="$(add_days 3)"     # within yellow (7d), outside red (1d) -> yellow

echo "${BOLD}HomeShip API smoke test${RESET}  ->  $BASE_URL"
echo "${DIM}user=$USERNAME  email=$EMAIL${RESET}"
echo "${DIM}crewmate=$USERNAME2  email=$EMAIL2${RESET}"

# =============================================================================
# 0. Sanity check
# =============================================================================
step "0. Sanity check"
request GET "$BASE_URL/"
assert_status 200 "$STATUS" "GET / reachable"
[[ "$STATUS" == "200" ]] && echo "  ${GREEN}App is running${RESET} — $(jget '.message')"

request GET "$BASE_URL/health"
assert_status 200 "$STATUS" "GET /health reachable"
assert_eq "ok" "$(jget '.status')" "database reports ok"
[[ "$STATUS" == "200" ]] && echo "  ${GREEN}Database is reachable${RESET}"

# =============================================================================
# 1. Create user
# =============================================================================
step "1. Create user"
request POST "$BASE_URL/users" \
  username="$USERNAME" email="$EMAIL" display_name="$DISPLAY_NAME" password="$PASSWORD"
assert_status 201 "$STATUS" "user created"
USER_ID="$(jget '.user_id')"
assert_present "$USER_ID" "user_id returned"
assert_eq "$USERNAME" "$(jget '.username')" "username echoed back"
assert_eq "$EMAIL" "$(jget '.email')" "email echoed back"
# UserRead must never leak the password hash.
assert_eq "null" "$(jget '.password_hash')" "no password_hash in response"
CREATED_USER="$BODY"
echo "  ${GREEN}User created${RESET} — id=$USER_ID"

# =============================================================================
# 2. Authenticate (JWT)
# =============================================================================
step "2. Authenticate via /auth/login"
request --form POST "$BASE_URL/auth/login" username="$EMAIL" password="$PASSWORD"
assert_status 200 "$STATUS" "login succeeded"
TOKEN="$(jget '.access_token')"
assert_present "$TOKEN" "JWT access_token returned"
assert_eq "bearer" "$(jget '.token_type')" "token_type is bearer"
AUTH=(Authorization:"Bearer $TOKEN")   # reuse on every authenticated call
echo "  ${GREEN}Authenticated${RESET} — token acquired"

# =============================================================================
# 3. GET /users/me matches creation
# =============================================================================
step "3. GET /users/me matches created user"
request GET "$BASE_URL/users/me" "${AUTH[@]}"
assert_status 200 "$STATUS" "fetched current user"
assert_eq "$USER_ID" "$(jget '.user_id')" "same user_id"
assert_eq "$USERNAME" "$(jget '.username')" "same username"
assert_eq "$EMAIL" "$(jget '.email')" "same email"
assert_eq "$DISPLAY_NAME" "$(jget '.display_name')" "same display_name"
# Whole object should be identical to what creation returned.
if [[ "$(printf '%s' "$BODY" | jq -S .)" == "$(printf '%s' "$CREATED_USER" | jq -S .)" ]]; then
  pass "/users/me identical to create response"
else
  fail "/users/me differs from create response"
fi

# =============================================================================
# 4. PATCH /users/me display name
# =============================================================================
step "4. Update user's name"
request PATCH "$BASE_URL/users/me" "${AUTH[@]}" display_name="$NEW_DISPLAY_NAME"
assert_status 200 "$STATUS" "user updated"
assert_eq "$NEW_DISPLAY_NAME" "$(jget '.display_name')" "display_name changed"
assert_eq "$USER_ID" "$(jget '.user_id')" "user_id unchanged"
echo "  ${GREEN}Updated user${RESET}:"
printf '%s\n' "$BODY" | jq .

# =============================================================================
# 5. Create a ship  (note: endpoint takes nested ship_data + ship_member_data)
# =============================================================================
step "5. Create a ship"
request POST "$BASE_URL/users/me/ships" "${AUTH[@]}" \
  ship_data:='{"shipname":"Homestead","timezone":"UTC"}' \
  ship_member_data:='{"role":"Crew Member"}'
assert_status 201 "$STATUS" "ship created"
SHIP_ID="$(jget '.ship_id')"
assert_present "$SHIP_ID" "ship_id returned"
assert_eq "Homestead" "$(jget '.shipname')" "shipname set"
echo "  ${GREEN}Ship created${RESET} — id=$SHIP_ID"

# =============================================================================
# 6. Ship appears in GET /users/me/ships
# =============================================================================
step "6. Ship is listed for the user"
request GET "$BASE_URL/users/me/ships" "${AUTH[@]}"
assert_status 200 "$STATUS" "listed ships"
if [[ "$(printf '%s' "$BODY" | jq --arg id "$SHIP_ID" '[.[].ship_id] | index($id) != null')" == "true" ]]; then
  pass "new ship present in list"
else
  fail "new ship missing from list" "$BODY"
fi

# =============================================================================
# 7. Update ship name
# =============================================================================
step "7. Update ship name"
request PATCH "$BASE_URL/users/me/ships/$SHIP_ID" "${AUTH[@]}" shipname="Horizon"
assert_status 200 "$STATUS" "ship updated"
assert_eq "Horizon" "$(jget '.shipname')" "shipname changed"
UPDATED_SHIP="$BODY"

# =============================================================================
# 8. GET /ships/{ship_id} matches the update
# =============================================================================
step "8. GET /ships/{ship_id} matches previous response"
request GET "$BASE_URL/ships/$SHIP_ID" "${AUTH[@]}"
assert_status 200 "$STATUS" "fetched ship"
if [[ "$(printf '%s' "$BODY" | jq -S .)" == "$(printf '%s' "$UPDATED_SHIP" | jq -S .)" ]]; then
  pass "GET /ships/{id} identical to update response"
else
  fail "GET /ships/{id} differs from update response" "$BODY"
fi

# =============================================================================
# 9. List members; user is a member
# =============================================================================
step "9. User is a member of the ship"
request GET "$BASE_URL/ships/$SHIP_ID/members" "${AUTH[@]}"
assert_status 200 "$STATUS" "listed members"
if [[ "$(printf '%s' "$BODY" | jq --arg id "$USER_ID" '[.[].user.user_id] | index($id) != null')" == "true" ]]; then
  pass "user present in member list"
else
  fail "user missing from member list" "$BODY"
fi
assert_eq "Crew Member" "$(printf '%s' "$BODY" | jq -r --arg id "$USER_ID" '.[] | select(.user.user_id==$id) | .role')" "initial role is Crew Member"

# =============================================================================
# 10. Update own role  Crew Member -> Tester
# =============================================================================
step "10. Change role to Tester"
request PATCH "$BASE_URL/ships/$SHIP_ID/members/me" "${AUTH[@]}" role="Tester"
assert_status 200 "$STATUS" "membership updated"
assert_eq "Tester" "$(jget '.role')" "role is now Tester"
request GET "$BASE_URL/ships/$SHIP_ID/members" "${AUTH[@]}"
assert_eq "Tester" "$(printf '%s' "$BODY" | jq -r --arg id "$USER_ID" '.[] | select(.user.user_id==$id) | .role')" "role persisted in member list"

# =============================================================================
# 11. Task list starts empty
# =============================================================================
step "11. Task list is empty"
request GET "$BASE_URL/ships/$SHIP_ID/tasks" "${AUTH[@]}"
assert_status 200 "$STATUS" "listed tasks"
assert_eq "0" "$(jget 'length')" "no tasks yet"

# =============================================================================
# 12. Create a task  (recurring, weekly)
# =============================================================================
step "12. Create a task"
request POST "$BASE_URL/ships/$SHIP_ID/tasks" "${AUTH[@]}" \
  content="Water the plants" frequency="P7D"
assert_status 201 "$STATUS" "task created"
TASK_ID="$(jget '.task_id')"
assert_present "$TASK_ID" "task_id returned"
assert_eq "green" "$(jget '.alert_state')" "new weekly task is green"
echo "  ${GREEN}Task created${RESET} — id=$TASK_ID, due $(jget '.date_due')"

# =============================================================================
# 13. Task list now non-empty
# =============================================================================
step "13. Task list is non-empty"
request GET "$BASE_URL/ships/$SHIP_ID/tasks" "${AUTH[@]}"
assert_eq "1" "$(jget 'length')" "exactly one task"

# =============================================================================
# 14. Postpone -> alert escalates green -> yellow
# =============================================================================
step "14. Postpone the task (alert should change)"
request POST "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID/postpone" "${AUTH[@]}" \
  date_due="$TASK_DUE_LATER"
assert_status 200 "$STATUS" "task postponed"
assert_eq "yellow" "$(jget '.alert_state')" "alert escalated green -> yellow"
assert_eq "$TASK_DUE_LATER" "$(jget '.date_due')" "due date pushed out"

# =============================================================================
# 15. Change frequency -> reschedules, alert back to green
# =============================================================================
step "15. Change task frequency"
request POST "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID/change_frequency" "${AUTH[@]}" \
  frequency="P3D"
assert_status 200 "$STATUS" "frequency changed"
assert_eq "green" "$(jget '.alert_state')" "alert recomputed to green"
echo "  ${DIM}frequency now $(jget '.frequency'), due $(jget '.date_due')${RESET}"

# =============================================================================
# 16. Complete the task
# =============================================================================
step "16. Complete the task"
request POST "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID/complete" "${AUTH[@]}"
assert_status 200 "$STATUS" "task completed"
assert_eq "$TODAY" "$(jget '.date_last')" "date_last is today"
assert_eq "green" "$(jget '.alert_state')" "completed task is green"

# =============================================================================
# 17. Deactivate the task
# =============================================================================
step "17. Deactivate the task"
request POST "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID/deactivate" "${AUTH[@]}"
assert_status 200 "$STATUS" "task deactivated"
assert_eq "inactive" "$(jget '.alert_state')" "alert is inactive"
assert_eq "null" "$(jget '.date_due')" "due date cleared"
assert_eq "null" "$(jget '.frequency')" "frequency cleared"

# =============================================================================
# Supplies (18-24) — mirror the task lifecycle on a scheduled "candles for the
# cake" supply: a deadline-driven item the crew must buy before a birthday.
# =============================================================================

# 18. Supply list starts empty
step "18. Supply list is empty"
request GET "$BASE_URL/ships/$SHIP_ID/supplies" "${AUTH[@]}"
assert_status 200 "$STATUS" "listed supplies"
assert_eq "0" "$(jget 'length')" "no supplies yet"

# 19. Create a supply: not in stock, party still far off -> green
step "19. Create a supply"
request POST "$BASE_URL/ships/$SHIP_ID/supplies" "${AUTH[@]}" \
  name="Candles for the cake" stock_state="out_of_stock" quantity:=0 date_due="$SUPPLY_DUE_FAR"
assert_status 201 "$STATUS" "supply created"
SUPPLY_ID="$(jget '.supply_id')"
assert_present "$SUPPLY_ID" "supply_id returned"
assert_eq "green" "$(jget '.alert_state')" "deadline far out -> green"
echo "  ${GREEN}Supply created${RESET} — id=$SUPPLY_ID, buy by $(jget '.date_due')"

# 20. Supply is listed and fetchable
step "20. Supply is listed and fetchable"
request GET "$BASE_URL/ships/$SHIP_ID/supplies" "${AUTH[@]}"
assert_eq "1" "$(jget 'length')" "exactly one supply"
request GET "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID" "${AUTH[@]}"
assert_status 200 "$STATUS" "fetched supply"
assert_eq "Candles for the cake" "$(jget '.name')" "supply name matches"

# 21. Reschedule closer (party moved up) -> alert green -> yellow
step "21. Reschedule the supply (alert should change)"
request POST "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID/reschedule" "${AUTH[@]}" \
  date_due="$SUPPLY_DUE_NEAR"
assert_status 200 "$STATUS" "supply rescheduled"
assert_eq "yellow" "$(jget '.alert_state')" "closer deadline -> yellow"
assert_eq "$SUPPLY_DUE_NEAR" "$(jget '.date_due')" "deadline updated"

# 22. Buy the candles: stock state in_stock -> back to green
step "22. Change stock state (restocked)"
request POST "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID/change_stock_state" "${AUTH[@]}" \
  stock_state="in_stock"
assert_status 200 "$STATUS" "stock state changed"
assert_eq "in_stock" "$(jget '.stock_state')" "now in_stock"
assert_eq "green" "$(jget '.alert_state')" "in-stock item -> green"

# 23. Update quantity on hand (independent of the alert) via PATCH
step "23. Update supply quantity"
request PATCH "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID" "${AUTH[@]}" quantity:=5
assert_status 200 "$STATUS" "supply updated"
assert_eq "5" "$(jget '.quantity')" "quantity is now 5"
assert_eq "Candles for the cake" "$(jget '.name')" "name unchanged by quantity edit"

# 24. Deactivate -> inactive, deadline and quantity cleared
step "24. Deactivate the supply"
request POST "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID/deactivate" "${AUTH[@]}"
assert_status 200 "$STATUS" "supply deactivated"
assert_eq "inactive" "$(jget '.alert_state')" "alert is inactive"
assert_eq "null" "$(jget '.date_due')" "deadline cleared"
assert_eq "null" "$(jget '.quantity')" "quantity cleared"

# =============================================================================
# Shared crew (25-29) — a second user joins the ship and must see exactly the
# same tasks and supplies as the first. This is the core "shared visibility"
# promise: the ship's contents belong to the crew, not to whoever created them.
# =============================================================================

# 25. Create a second user
step "25. Create a second user"
request POST "$BASE_URL/users" \
  username="$USERNAME2" email="$EMAIL2" display_name="$DISPLAY_NAME2" \
  password="$PASSWORD2"
assert_status 201 "$STATUS" "second user created"
USER_ID2="$(jget '.user_id')"
assert_present "$USER_ID2" "second user_id returned"
assert_ne "$USER_ID" "$USER_ID2" "second user is distinct from the first"
echo "  ${GREEN}Second user created${RESET} — id=$USER_ID2"

# 26. First user adds the second user to the ship's crew, by email
step "26. First user adds the second user to the crew"
request POST "$BASE_URL/ships/$SHIP_ID/members" "${AUTH[@]}" \
  email="$EMAIL2" role="Crew Member"
assert_status 201 "$STATUS" "second user added as a member"
assert_eq "$USER_ID2" "$(jget '.user.user_id')" "membership references the second user"
assert_eq "Crew Member" "$(jget '.role')" "second user's role is Crew Member"
request GET "$BASE_URL/ships/$SHIP_ID/members" "${AUTH[@]}"
assert_eq "2" "$(jget 'length')" "ship now has two crew members"

# 27. Second user authenticates on their own account
step "27. Second user authenticates"
request --form POST "$BASE_URL/auth/login" username="$EMAIL2" password="$PASSWORD2"
assert_status 200 "$STATUS" "second user login succeeded"
TOKEN2="$(jget '.access_token')"
assert_present "$TOKEN2" "second user's JWT returned"
AUTH2=(Authorization:"Bearer $TOKEN2")   # the second crew member's calls
echo "  ${GREEN}Second user authenticated${RESET}"

# 28. Second user sees the task and supply the first user created
step "28. Second user sees the ship's tasks and supplies"
request GET "$BASE_URL/ships/$SHIP_ID/tasks" "${AUTH2[@]}"
assert_status 200 "$STATUS" "second user can list the ship's tasks"
assert_eq "1" "$(jget 'length')" "second user sees exactly one task"
assert_eq "$TASK_ID" "$(jget '.[0].task_id')" "it is the first user's task"
TASKS_AS_USER2="$BODY"
request GET "$BASE_URL/ships/$SHIP_ID/supplies" "${AUTH2[@]}"
assert_status 200 "$STATUS" "second user can list the ship's supplies"
assert_eq "1" "$(jget 'length')" "second user sees exactly one supply"
assert_eq "$SUPPLY_ID" "$(jget '.[0].supply_id')" "it is the first user's supply"
SUPPLIES_AS_USER2="$BODY"

# 29. First user sees byte-for-byte the same lists as the second user
step "29. First user sees the same tasks and supplies"
request GET "$BASE_URL/ships/$SHIP_ID/tasks" "${AUTH[@]}"
assert_status 200 "$STATUS" "first user can list the ship's tasks"
if [[ "$(printf '%s' "$BODY" | jq -S .)" == "$(printf '%s' "$TASKS_AS_USER2" | jq -S .)" ]]; then
  pass "task list is identical for both crew members"
else
  fail "task list differs between crew members" "$BODY"
fi
request GET "$BASE_URL/ships/$SHIP_ID/supplies" "${AUTH[@]}"
assert_status 200 "$STATUS" "first user can list the ship's supplies"
if [[ "$(printf '%s' "$BODY" | jq -S .)" == "$(printf '%s' "$SUPPLIES_AS_USER2" | jq -S .)" ]]; then
  pass "supply list is identical for both crew members"
else
  fail "supply list differs between crew members" "$BODY"
fi

# =============================================================================
# 30. Deletion endpoints — a deletion by any crew member is visible to all.
# =============================================================================
step "30. Deletion is shared across the crew"

# First user deletes the task; it must be gone for both crew members.
request DELETE "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID" "${AUTH[@]}"
assert_status 204 "$STATUS" "first user deleted the task"
request GET "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID" "${AUTH[@]}"
assert_status 404 "$STATUS" "task gone for the first user (404)"
request GET "$BASE_URL/ships/$SHIP_ID/tasks/$TASK_ID" "${AUTH2[@]}"
assert_status 404 "$STATUS" "task gone for the second user too (404)"

# Second user deletes the supply; it must be gone for both crew members.
request DELETE "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID" "${AUTH2[@]}"
assert_status 204 "$STATUS" "second user deleted the supply"
request GET "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID" "${AUTH2[@]}"
assert_status 404 "$STATUS" "supply gone for the second user (404)"
request GET "$BASE_URL/ships/$SHIP_ID/supplies/$SUPPLY_ID" "${AUTH[@]}"
assert_status 404 "$STATUS" "supply gone for the first user too (404)"

# =============================================================================
# 31. First user leaves the ship. As one of two members they only give up their
# own seat — the ship stands for the second user, but is now off-limits to the
# one who left.
# =============================================================================
step "31. First user leaves the ship"
request DELETE "$BASE_URL/users/me/ships/$SHIP_ID" "${AUTH[@]}"
assert_status 204 "$STATUS" "first user left the ship"
# No longer a member: the ship and its contents are off-limits to them (404).
request GET "$BASE_URL/ships/$SHIP_ID" "${AUTH[@]}"
assert_status 404 "$STATUS" "former member cannot fetch the ship (404)"
request GET "$BASE_URL/ships/$SHIP_ID/tasks" "${AUTH[@]}"
assert_status 404 "$STATUS" "former member cannot list the ship's tasks (404)"
request GET "$BASE_URL/ships/$SHIP_ID/supplies" "${AUTH[@]}"
assert_status 404 "$STATUS" "former member cannot list the ship's supplies (404)"
# The ship stands: the second user is still aboard, now as its sole member.
request GET "$BASE_URL/ships/$SHIP_ID" "${AUTH2[@]}"
assert_status 200 "$STATUS" "ship still exists for the second user"
request GET "$BASE_URL/ships/$SHIP_ID/members" "${AUTH2[@]}"
assert_eq "1" "$(jget 'length')" "ship now has a single member"
assert_eq "$USER_ID2" "$(jget '.[0].user.user_id')" "the remaining member is the second user"

# =============================================================================
# 32. Tear down both users. The first has already left, so their deletion is a
# plain account removal; the second is the ship's last member, so deleting them
# cascades the ship, its membership, tasks and supplies away.
# =============================================================================
step "32. Delete both users"

request DELETE "$BASE_URL/users/me" "${AUTH[@]}"
assert_status 204 "$STATUS" "first user deleted"
# Token now points at a deleted user; /users/me should no longer resolve.
request GET "$BASE_URL/users/me" "${AUTH[@]}"
assert_ne "200" "$STATUS" "deleted first user can no longer fetch /users/me (HTTP $STATUS)"

request DELETE "$BASE_URL/users/me" "${AUTH2[@]}"
assert_status 204 "$STATUS" "second user deleted"
request GET "$BASE_URL/users/me" "${AUTH2[@]}"
assert_ne "200" "$STATUS" "deleted second user can no longer fetch /users/me (HTTP $STATUS)"
# The second user was the ship's last member, so the ship is cascade-deleted.
# With both users gone there is no longer an authorized caller to observe it.

# =============================================================================
# Summary
# =============================================================================
printf '\n%s---------------------------------------------%s\n' "$BOLD" "$RESET"
printf '%sPassed: %d%s   %sFailed: %d%s\n' \
  "$GREEN" "$PASS_COUNT" "$RESET" \
  "$( ((FAIL_COUNT)) && printf '%s' "$RED" || printf '%s' "$DIM" )" "$FAIL_COUNT" "$RESET"

if ((FAIL_COUNT)); then
  printf '%sSMOKE TEST FAILED%s\n' "$RED" "$RESET"
  exit 1
fi
printf '%sALL CHECKS PASSED%s\n' "$GREEN" "$RESET"
