# Public Discord operations. Network work never holds the state transaction lock.
discord_command() {
  [ "$#" = 1 ] || err 'Usage: discord configure|configure-test|enable|disable|status|flush'
  discord_action=$1
  case "$discord_action" in
    configure|configure-test|enable|disable|status|flush) ;;
    *) err 'Usage: discord configure|configure-test|enable|disable|status|flush' ;;
  esac
  "$ROOT/bin/heimdall" init >/dev/null
  if [ "$discord_action" = status ]; then
    "$ROOT/bin/heimdall" _discord status
    return
  fi
  if [ "${HEIMDALL_DISCORD_LOCK_PID:-}" != "$$" ]; then
    exec python3 "$ROOT/lib/lock.py" "$DATA/.discord.lock" HEIMDALL_DISCORD_LOCK_PID 0 "$ROOT/bin/heimdall" discord "$discord_action"
  fi
  case "$discord_action" in
    configure|configure-test)
      # Disable durably before replacing the credential: interruption cannot
      # silently send to a newly written destination under old enabled state.
      "$ROOT/bin/heimdall" _discord disable >/dev/null
      metadata=$(python3 "$ROOT/lib/discord_http.py" "$DATA" "$discord_action")
      "$ROOT/bin/heimdall" _discord configure "$metadata"
      ;;
    enable|disable) "$ROOT/bin/heimdall" _discord "$discord_action" ;;
    flush)
      chunks=0
      # Bound this run to the initial queue. Findings appended during HTTP
      # remain pending for the next run, including when this batch is split.
      snapshot=$("$ROOT/bin/heimdall" _discord snapshot)
      while [ "$chunks" -lt 10 ]; do
        if ! printf '%s\n' "$snapshot" | jq -e '.enabled and .configured and (.blocked|not) and (.retry_after <= now) and (.items|length > 0)' >/dev/null; then break; fi
        result=$(printf '%s\n' "$snapshot" | python3 "$ROOT/lib/discord_http.py" "$DATA" send)
        if [ "$(printf '%s\n' "$result" | jq '.ids|length')" = 0 ]; then break; fi
        printf '%s\n' "$result" | "$ROOT/bin/heimdall" _discord result >/dev/null
        chunks=$((chunks + 1))
        if ! printf '%s\n' "$result" | jq -e '.outcome == "accepted" and .delay_seconds == 0' >/dev/null; then break; fi
        snapshot=$(printf '%s\n' "$snapshot" | jq --argjson result "$result" '.items |= map(select(.id as $id | $result.ids | index($id) == null))')
      done
      "$ROOT/bin/heimdall" _discord status
      ;;
  esac
}
