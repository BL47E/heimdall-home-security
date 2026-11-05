# Sourced only by the monitor lifecycle branch of bin/heimdall.
monitor_command() {
  [ "$#" = 1 ] || err 'Usage: monitor run|start|stop'
  action=$1
  "$ROOT/bin/heimdall" init >/dev/null
  case "$action" in
    start)
      if [ "$(jq -r '.mode' "$STATE")" = fixture ]; then err 'Fixture state cannot become live; use a separate live data directory'; fi
      nohup "$ROOT/bin/heimdall" monitor run >> "$DATA/monitor.log" 2>&1 < /dev/null &
      sleep 0.3
      "$ROOT/bin/heimdall" status ;;
    stop)
      pid=$(jq -r '.monitor.pid // empty' "$STATE")
      if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        ps -p "$pid" -o command= | grep -F "$ROOT/bin/heimdall monitor run" >/dev/null || err 'Refusing to signal an unrecognized process'
        kill -TERM "$pid"
        attempts=0
        while kill -0 "$pid" 2>/dev/null; do attempts=$((attempts+1)); [ "$attempts" -lt 30 ] || err 'Monitor did not stop promptly'; sleep 0.1; done
      fi
      "$ROOT/bin/heimdall" status ;;
    run) monitor_run ;;
    *) err 'Usage: monitor run|start|stop' ;;
  esac
}
monitor_run() {
  [ "$(jq -r '.mode' "$STATE")" != fixture ] || err 'Use a separate live data directory'
  MONITOR_LOCK=$DATA/.monitor-lock
  # The OS advisory singleton lock is held before reaching this point. Only this
  # monitor can own the scratch directory; clean known leftovers from a crash.
  if [ -L "$MONITOR_LOCK" ]; then err 'Monitor scratch directory must not be a symbolic link'; fi
  mkdir -p "$MONITOR_LOCK"
  rm -f "$MONITOR_LOCK/journal" "$MONITOR_LOCK/probe" "$MONITOR_LOCK/pid"
  printf '%s\n' "$$" > "$MONITOR_LOCK/pid"
  journal_pid=''; fifo=$MONITOR_LOCK/journal
  monitor_finish() {
    trap - EXIT HUP INT TERM
    if [ -n "$journal_pid" ]; then kill "$journal_pid" 2>/dev/null || :; wait "$journal_pid" 2>/dev/null || :; fi
    final_state=$(jq -r '.monitor.state' "$STATE")
    if [ "$final_state" = error ]; then
      "$ROOT/bin/heimdall" _monitor_state '{"pid":null,"coverage":"unavailable"}' >/dev/null || :
    else
      "$ROOT/bin/heimdall" _monitor_state '{"state":"stopped","pid":null,"coverage":"unavailable"}' >/dev/null || :
    fi
    rm -f "$fifo" "$MONITOR_LOCK/pid"; rmdir "$MONITOR_LOCK" 2>/dev/null || :
  }
  trap monitor_finish EXIT
  trap 'exit 0' HUP INT TERM
  "$ROOT/bin/heimdall" _monitor_state "{\"state\":\"running\",\"pid\":$$,\"coverage\":\"unavailable\",\"last_error\":null,\"coverage_since\":$(date +%s)}" >/dev/null
  if ! command -v journalctl >/dev/null 2>&1 || ! journalctl -u ssh --no-pager -n 1 -o json > "$MONITOR_LOCK/probe" 2> "$DATA/journal-error.log" || [ ! -s "$MONITOR_LOCK/probe" ]; then
    "$ROOT/bin/heimdall" _monitor_state '{"state":"error","last_error":"SSH journal unavailable or empty; check journal access and SSH service","coverage":"unavailable"}' >/dev/null
    rm -f "$MONITOR_LOCK/probe"; exit 1
  fi
  rm -f "$MONITOR_LOCK/probe"
  cursor=$(jq -r '.cursor // empty' "$STATE")
  if [ -n "$cursor" ]; then
    if ! journalctl -u ssh --no-pager -o json --cursor="$cursor" -n 1 > "$MONITOR_LOCK/probe" 2> "$DATA/journal-error.log" || ! jq -e --arg cursor "$cursor" '.__CURSOR == $cursor' "$MONITOR_LOCK/probe" >/dev/null 2>&1; then
      "$ROOT/bin/heimdall" _monitor_state '{"state":"error","last_error":"Saved journal cursor could not be verified; coverage gap requires owner inspection","coverage":"unavailable"}' >/dev/null
      rm -f "$MONITOR_LOCK/probe"; exit 1
    fi
    rm -f "$MONITOR_LOCK/probe"
  fi
  mkfifo "$fifo"
  if [ -n "$cursor" ]; then
    journalctl -u ssh --no-pager -o json --follow --after-cursor="$cursor" 9>&- > "$fifo" 2> "$DATA/journal-error.log" &
  else
    journalctl -u ssh --no-pager -o json --follow --since now 9>&- > "$fifo" 2> "$DATA/journal-error.log" &
  fi
  journal_pid=$!
  export HEIMDALL_INTERNAL_MONITOR=$$
  "$ROOT/bin/heimdall" _monitor_state '{"coverage":"available"}' >/dev/null
  while IFS= read -r record; do
    printf '%s\n' "$record" | "$ROOT/bin/heimdall" _journal_ingest - >/dev/null || {
      "$ROOT/bin/heimdall" _monitor_state '{"state":"error","last_error":"Journal event could not be persisted","coverage":"unavailable"}' >/dev/null; exit 1;
    }
  done < "$fifo"
  "$ROOT/bin/heimdall" _monitor_state '{"state":"error","last_error":"Journal reader exited; coverage interrupted. Inspect journal-error.log","coverage":"unavailable"}' >/dev/null
  exit 1
}
