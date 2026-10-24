#!/bin/bash
# N:M MC-IPsec switchover test runner for the nm-mc-ipsec lab. See ../TEST-PLAN.md.
# usage: tests/nm_tests.sh T0 T1 ...   |   tests/nm_tests.sh all
set -u
exec 9>/tmp/nm_tests.lock
flock -n 9 || { echo "another nm_tests.sh run is in progress" >&2; exit 1; }
LAB=$(cd "$(dirname "$0")/.." && pwd)
cd "$LAB" || exit 1
RES=$LAB/results
mkdir -p "$RES"
SROS=$LAB/sros.sh
P=clab-nm-mc-ipsec
SEGS="seg1 seg2 seg3"
OUT=/dev/null
SUMMARY=$RES/SUMMARY.md
[ -f "$SUMMARY" ] || printf '| ID | Сценарий | Ожид. OA | Факт OA | enb1 потери / макс. разрыв | enb2 потери / макс. разрыв | IKE SA сохранён | Вердикт |\n|---|---|---|---|---|---|---|---|\n' > "$SUMMARY"

log() { echo "[$(date +%T)] $*" | tee -a "$OUT"; }

running() {
  local c="$P-$1-a"
  [ "$1" = ipmpls ] && c="$P-$1"
  [ "$(docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null)" = true ]
}

# cfg <node> <flat MD-CLI line>...  -- commit in a private candidate
cfg() {
  local node=$1; shift
  local o
  o=$({ echo "edit-config private"; printf '%s\n' "$@"; echo "exit all"; echo "commit"; echo "quit-config"; } | $SROS "$node")
  if grep -qE "MINOR|MAJOR|CRITICAL" <<<"$o"; then
    log "CFG ERROR on $node:"; grep -E "MINOR|MAJOR|CRITICAL" <<<"$o" | tee -a "$OUT"
    return 1
  fi
  log "cfg $node: $*"
}

op() { local node=$1; shift; $SROS "$node" "$@"; }

# dom <node> -> "act=.. prot=.. cur=segN inst=N dorm=N"
dom() {
  local n=$1 o
  running "$n" || { echo "DOWN"; return; }
  o=$(op "$n" 'show redundancy multi-chassis ipsec-domain 1')
  [ -n "$o" ] || { echo "NO-CLI"; return; }
  awk '
    /Activity State/      { sub(/.*Activity State *: */, ""); act=$1 }
    /Protection Status/   { sub(/.*Protection Status *: */, ""); prot=$1 }
    /Current Active/      { sub(/.*Current Active *: */, ""); cur=$1 }
    /^Installed/          { inst=$3 }
    /^Standby Dormant/    { dorm=$4 }
    END { sub(/^10\.0\.0\./, "seg", cur); printf "act=%s prot=%s cur=%s inst=%s dorm=%s", act, prot, cur, inst, dorm }' <<<"$o"
}

oa() {
  local n s
  for n in $SEGS; do
    s=$(dom "$n")
    # "eligible" = OA without election consensus (all peers lost), still forwarding
    [[ $s == act=active* || $s == act=eligible* ]] && { echo "$n"; return; }
  done
  echo "none"
}

best_paths() {
  local o
  o=$(op ipmpls 'show router route-table 198.51.100.1/32' 'show router "100" route-table 10.100.1.1/32')
  awk '/^198\.51\.100\.1\/32|^10\.100\.1\.1\/32/ { pfx=$1; getline; nh=$1; sub(/^172\.3[01]\./, "seg", nh); sub(/\.1$/, "", nh); printf "%s->%s  ", pfx, nh }' <<<"$o"
  echo
}

ike_spi() { docker exec "$P-$1" swanctl --list-sas 2>/dev/null | awk '/ESTABLISHED/ { print $5; exit }'; }

snapshot() {
  local n
  log "--- state: $1"
  for n in $SEGS; do log "  $n: $(dom "$n")"; done
  log "  ipmpls best: $(best_paths)"
  log "  IKE SPI: enb1=$(ike_spi enb1) enb2=$(ike_spi enb2)"
}

events() {
  local n
  log "--- MC_REDUNDANCY events (log 99, newest first)"
  for n in $SEGS; do
    running "$n" || continue
    op "$n" 'show log log-id 99 application mc_redundancy count 5 descending' \
      | awk -v n="$n" '/^[0-9]+ 20[0-9][0-9]\// { h = $2 " " $3; getline; printf "  %s %s %s\n", n, h, $0 }' \
      | tee -a "$OUT"
  done
}

traffic_start() {
  local n
  for n in 1 2; do
    docker exec "$P-enb$n" sh -c "pkill ping; rm -f /tmp/ping.log"
    docker exec -d "$P-enb$n" sh -c "ping -D -O -i 0.1 -W 1 -I 10.100.$n.1 10.200.0.10 > /tmp/ping.log 2>&1"
  done
  sleep 3
}

# traffic_stop -> sets LOSS1 LOSS2 (lost/maxgap_ms)
traffic_stop() {
  local n r
  for n in 1 2; do docker exec "$P-enb$n" pkill -INT ping; done
  sleep 1
  for n in 1 2; do
    docker exec "$P-enb$n" cat /tmp/ping.log > "$RES/$ID-enb$n.ping"
    # max gap between replies, including the tail from the last reply to the last "no answer" line
    r=$(awk '
      /^\[[0-9.]+\]/ { last = substr($1, 2, length($1) - 2) + 0 }
      /bytes from/   { if (p) { g = last - p; if (g > mg) mg = g }; p = last }
      /packets transmitted/ { tx = $1; rx = $4 }
      END { if (p && last - p > mg) mg = last - p; printf "%d/%dms", tx - rx, mg * 1000 }' "$RES/$ID-enb$n.ping")
    log "  enb$n traffic: lost/max-gap = $r  ($(grep 'packets transmitted' "$RES/$ID-enb$n.ping"))"
    eval "LOSS$n=\$r"
  done
}

wait_for() {  # wait_for <timeout-s> <description> <cmd...>
  local to=$1 desc=$2 t0=$SECONDS; shift 2
  until "$@"; do
    if (( SECONDS - t0 > to )); then log "TIMEOUT ($to s) waiting for: $desc"; return 1; fi
    sleep 3
  done
  log "ok after $((SECONDS - t0)) s: $desc"
}

all_nominal() {
  local n s
  for n in $SEGS; do
    s=$(dom "$n")
    [[ $s == *prot=nominal* ]] || return 1
  done
}
oa_is() { [ "$(oa)" = "$1" ]; }
seg_tunnels() { [[ $(dom "$1") == *inst=2* ]]; }
cli_up() { running "$1" && op "$1" 'show system information' | grep -q 'System Name'; }
enb_sas_up() {
  local n ok=0
  for n in 1 2; do
    if [ -z "$(ike_spi enb$n)" ]; then docker exec "$P-enb$n" swanctl --initiate --child s1u >/dev/null 2>&1; ok=1; fi
  done
  return $ok
}

switch_to() {  # switch_to <segN>
  local cur
  cur=$(oa)
  [ "$cur" = "$1" ] && return 0
  [ "$cur" = none ] && return 1
  log "force-switchover on $cur -> $1"
  op "$cur" "tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 to 10.0.0.${1#seg} now" | tee -a "$OUT" | grep -E "MINOR|MAJOR"
  wait_for 90 "$1 becomes OA" oa_is "$1"
}

ensure_baseline() {
  local n
  OUT=/dev/null
  log "=== ensure baseline (seg1 OA, all nominal)"
  for n in $SEGS ipmpls; do wait_for 400 "$n CLI up" cli_up "$n" >/dev/null; done
  wait_for 600 "protection nominal on all SeGWs" all_nominal
  switch_to seg1
  wait_for 120 "eNB IKE SAs up" enb_sas_up
  wait_for 120 "2 tunnels installed on seg1" seg_tunnels seg1
  wait_for 180 "protection nominal on all SeGWs" all_nominal || sync_recovery_workaround
}

# Protection status can stay notReady after a (re)joining standby node; recovery documented in SR OS
# release notes = disable/enable "peer mc-ipsec domain" on all peers. See RESULTS.md, finding F4.
sync_recovery_workaround() {
  local n p st
  log "WORKAROUND sync-recovery: protection stuck notReady -> flapping peer mc-ipsec domain 1 on all SeGWs"
  for st in disable enable; do
    for n in $SEGS; do
      local lines=()
      for p in 1 2 3; do
        [ "seg$p" = "$n" ] && continue
        lines+=("/configure redundancy multi-chassis peer 10.0.0.$p mc-ipsec domain 1 admin-state $st")
      done
      cfg "$n" "${lines[@]}"
    done
    sleep 5
  done
  wait_for 300 "protection nominal on all SeGWs (after workaround)" all_nominal
  echo "$(date +%T) sync-recovery workaround applied before next test" >> "$RES/workarounds.log"
}

routes_on_oa() {
  local o b
  o=$(oa); b=$(best_paths)
  [[ $b == *"198.51.100.1/32->$o"* && $b == *"10.100.1.1/32->$o"* ]]
}

begin() {  # begin <ID> <title> <expectation>
  ID=$1; TITLE=$2
  wait_for 120 "ipmpls best paths point to current OA" routes_on_oa
  OUT=$RES/$ID.md
  : > "$OUT"
  log "# $ID — $TITLE"
  log "Ожидание: $3"
  snapshot before
  SPI_BEFORE="$(ike_spi enb1)/$(ike_spi enb2)"
  traffic_start
}

# finish <expected-OA|-> <loss: none|any|some>
finish() {
  local exp=$1 lossexp=$2 act verdict=PASS kept
  traffic_stop
  snapshot after
  events
  act=$(oa)
  [ "$(ike_spi enb1)/$(ike_spi enb2)" = "$SPI_BEFORE" ] && kept=yes || kept=no
  [ "$exp" != "-" ] && [ "$exp" != "$act" ] && verdict=FAIL
  case $lossexp in
    none) [[ $LOSS1 == 0/* && $LOSS2 == 0/* ]] || verdict=FAIL ;;
    some) [[ $LOSS1 == 0/* && $LOSS2 == 0/* ]] && verdict=FAIL ;;
  esac
  [ "$exp" = "-" ] && [ "$verdict" = PASS ] && verdict=OBSERVED
  log "RESULT: expected OA=$exp actual OA=$act, IKE SA kept=$kept, verdict=$verdict"
  printf '| %s | %s | %s | %s | %s | %s | %s | %s |\n' "$ID" "$TITLE" "$exp" "$act" "$LOSS1" "$LOSS2" "$kept" "$verdict" >> "$SUMMARY"
  OUT=/dev/null
}

# ---------------------------------------------------------------- scenarios
T0() {
  begin T0 "Baseline" "seg1 active/nominal, seg2 Installed, seg3 Standby Dormant, MED 100 via seg1"
  sleep 10
  finish seg1 none
}

T1() {
  begin T1 "force-switchover auto на OA" "DA preferred over DS -> seg2"
  op seg1 "tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 auto now" | tee -a "$OUT" | grep -E "MINOR|MAJOR"
  wait_for 90 "seg2 becomes OA" oa_is seg2
  sleep 20
  finish seg2 any
  begin T1b "force-switchover to seg1" "back to seg1"
  op seg2 "tools perform redundancy multi-chassis mc-ipsec force-switchover domain 1 to 10.0.0.1 now" | tee -a "$OUT" | grep -E "MINOR|MAJOR"
  wait_for 90 "seg1 becomes OA" oa_is seg1
  sleep 20
  finish seg1 any
}

T2() {
  begin T2 "Отказ ISA на OA (seg1 mda 1/2 down)" "seg1 notEligible -> seg2 OA"
  cfg seg1 '/configure card 1 mda 2 admin-state disable'
  wait_for 90 "seg2 becomes OA" oa_is seg2
  sleep 20
  finish seg2 any
}

T3() {
  begin T3 "Восстановление ISA, revertive=false" "seg1 standby/nominal, OA stays seg2, no loss"
  cfg seg1 '/configure card 1 mda 2 admin-state enable'
  wait_for 300 "all nominal" all_nominal
  sleep 30
  finish seg2 none
}

T4() {
  begin T4 "revertive=true на seg1" "after >=60 s standby+nominal seg1 takes OA"
  local t0=$SECONDS
  cfg seg1 '/configure redundancy multi-chassis ipsec-domain 1 revertive true'
  wait_for 240 "seg1 becomes OA (revertive)" oa_is seg1
  log "revert took $((SECONDS - t0)) s after enabling revertive"
  sleep 15
  finish seg1 any
  cfg seg1 '/configure redundancy multi-chassis ipsec-domain 1 revertive false'
}

T5() {
  begin T5 "Отказ 1 из 2 линков seg1-seg2" "no switchover, nominal, no loss"
  cfg seg1 '/configure port 1/1/1 admin-state disable'
  sleep 30
  log "  seg1->seg2 adjacency: $(op seg1 'show redundancy multi-chassis mc-ipsec peer 10.0.0.2 domain 1' | grep -E 'Oper State')"
  log "  seg1 sync seg2: $(op seg1 'show redundancy multi-chassis sync peer 10.0.0.2' | grep -E 'DB Sync State')"
  finish seg1 none
  cfg seg1 '/configure port 1/1/1 admin-state enable'
  sleep 15
}

T6() {
  begin T6 "Отказ обоих линков seg1-seg2" "observe: seg3 still meshed with both"
  cfg seg1 '/configure port 1/1/1 admin-state disable' '/configure port 1/1/2 admin-state disable'
  sleep 45
  log "  seg1 adjacencies: $(op seg1 'show redundancy multi-chassis ipsec-domain 1' | awk '/^10\.0\.0\./ {printf "%s %s %s %s; ", $1, $2, $3, $4}')"
  log "  seg2 adjacencies: $(op seg2 'show redundancy multi-chassis ipsec-domain 1' | awk '/^10\.0\.0\./ {printf "%s %s %s %s; ", $1, $2, $3, $4}')"
  finish - any
  cfg seg1 '/configure port 1/1/1 admin-state enable' '/configure port 1/1/2 admin-state enable'
}

T7() {
  begin T7 "Отказ узла OA (docker kill seg1)" "BFD detect -> seg2 OA"
  docker kill "$P-seg1-a" "$P-seg1-1" >/dev/null
  log "seg1 killed"
  wait_for 90 "seg2 becomes OA" oa_is seg2
  sleep 20
  finish seg2 any
  docker start "$P-seg1-1" "$P-seg1-a" >/dev/null
  log "seg1 restarted"
  wait_for 400 "seg1 CLI up" cli_up seg1
  begin T7r "Возврат seg1 после отказа" "non-revertive: seg2 stays OA, no loss"
  wait_for 300 "all nominal" all_nominal
  sleep 20
  finish seg2 none
  begin T7b "force-switchover to seg1" "back to seg1"
  switch_to seg1
  sleep 20
  finish seg1 any
}

double_failure() {  # double_failure <ID> <title>
  begin "$1" "$2" "DS seg3 becomes OA (ISA from pool)"
  docker kill "$P-seg1-a" "$P-seg1-1" "$P-seg2-a" "$P-seg2-1" >/dev/null
  log "seg1 + seg2 killed"
  wait_for 120 "seg3 becomes OA" oa_is seg3
  sleep 30
  finish seg3 any
  docker start "$P-seg1-1" "$P-seg1-a" "$P-seg2-1" "$P-seg2-a" >/dev/null
  log "seg1 + seg2 restarted"
  wait_for 400 "seg1 CLI up" cli_up seg1
  wait_for 400 "seg2 CLI up" cli_up seg2
  wait_for 300 "all nominal" all_nominal
  log "OA after recovery: $(oa)"
}

T8() { double_failure T8 "Двойной отказ seg1+seg2 (DS, обычный pool)"; }

T9() {
  OUT=/dev/null
  cfg seg3 '/configure isa tunnel-member-pool "pool1" high-availability tunnel-limit-32k' || return
  wait_for 300 "all nominal" all_nominal
  log "seg3 with HA pool: $(dom seg3)"
  double_failure T9 "Двойной отказ seg1+seg2 (DS, pool high-availability)"
  ensure_baseline
  cfg seg3 '/configure isa tunnel-member-pool "pool1" high-availability none'
}

T10() {
  cfg ipmpls \
    '/configure policy-options prefix-list "segw-gw" prefix 198.51.100.1/32 type exact' \
    '/configure policy-options policy-statement "reject-gw" entry 10 from prefix-list ["segw-gw"]' \
    '/configure policy-options policy-statement "reject-gw" entry 10 action action-type reject' \
    '/configure policy-options policy-statement "reject-gw" default-action action-type accept'
  begin T10 "Shunting public: ESP приходит на standby" "standby shunts ESP to seg1 via shunt-pub, no loss"
  cfg ipmpls '/configure router "Base" bgp neighbor "172.31.1.1" import policy ["reject-gw"]'
  sleep 20
  log "  ipmpls best: $(best_paths)"
  sleep 10
  finish seg1 any
  begin T10b "Shunting public выключен на standby" "ESP arriving at standby is dropped"
  cfg seg2 'delete /configure service ies "public" interface "pub" multi-chassis-shunting-profile'
  cfg seg3 'delete /configure service ies "public" interface "pub" multi-chassis-shunting-profile'
  sleep 20
  finish seg1 some
  cfg seg2 '/configure service ies "public" interface "pub" multi-chassis-shunting-profile "shunt-pub"'
  cfg seg3 '/configure service ies "public" interface "pub" multi-chassis-shunting-profile "shunt-pub"'
  cfg ipmpls 'delete /configure router "Base" bgp neighbor "172.31.1.1" import'
  sleep 15
}

T11() {
  cfg ipmpls \
    '/configure policy-options prefix-list "enb-inner" prefix 10.100.0.0/16 type longer' \
    '/configure policy-options policy-statement "reject-enb" entry 10 from prefix-list ["enb-inner"]' \
    '/configure policy-options policy-statement "reject-enb" entry 10 action action-type reject' \
    '/configure policy-options policy-statement "reject-enb" default-action action-type accept'
  begin T11 "Shunting private: clear-text приходит на standby" "standby shunts to seg1 via shunt-priv, no loss"
  cfg ipmpls '/configure service vprn "mobile" bgp neighbor "172.30.1.1" import policy ["reject-enb"]'
  sleep 20
  log "  ipmpls best: $(best_paths)"
  sleep 10
  finish seg1 any
  begin T11b "Shunting private выключен на standby" "mme->eNB traffic arriving at standby is dropped"
  cfg seg2 'delete /configure service vprn "mobile" interface "priv" multi-chassis-shunting-profile'
  cfg seg3 'delete /configure service vprn "mobile" interface "priv" multi-chassis-shunting-profile'
  sleep 20
  finish seg1 some
  cfg seg2 '/configure service vprn "mobile" interface "priv" multi-chassis-shunting-profile "shunt-priv"'
  cfg seg3 '/configure service vprn "mobile" interface "priv" multi-chassis-shunting-profile "shunt-priv"'
  cfg ipmpls 'delete /configure service vprn "mobile" bgp neighbor "172.30.1.1" import'
  sleep 15
}

ALL="T0 T1 T2 T3 T4 T5 T6 T7 T8 T9 T10 T11"
[ "${1:-}" = all ] && set -- $ALL
for t in "$@"; do
  case $t in
    T3|T4) ;;                       # chained after T2/T3
    *) ensure_baseline ;;
  esac
  "$t"
done
OUT=/dev/null
log "done: $*  -> $SUMMARY"
