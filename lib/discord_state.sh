# Sourced after the CLI takes its ordinary state transaction lock.
discord_state_status() {
  jq -L "$ROOT/lib" --argjson now "$(date +%s)" \
    'include "notifications"; discord_summary($now)' "$STATE"
}
discord_state_command() {
  operation=${1:-}
  shift || :
  case "$operation" in
    status | snapshot)
      [ "$#" = 0 ] || err 'Unexpected Discord state arguments'
      if [ "$operation" = status ]; then discord_state_status
      else jq -L "$ROOT/lib" --argjson now "$(date +%s)" \
        'include "notifications"; discord_snapshot($now)' "$STATE"; fi
      ;;
    configure)
      [ "$#" = 1 ] || err 'Missing Discord configuration metadata'
      jq -en --argjson patch "$1" '$patch | type == "object" and
        (keys == ["configured","destination_kind"]) and .configured == true and
        (.destination_kind == "production" or .destination_kind == "loopback_test")' >/dev/null 2>&1 || err 'Invalid Discord configuration metadata'
      result=$(jq -L "$ROOT/lib" --argjson patch "$1" '
        include "notifications";
        .discord = (discord_defaults + $patch) |
        .notifications = ((.notifications // []) | map(
          if .status == "pending" then .next_attempt_at=0 else . end))' "$STATE")
      printf '%s\n' "$result" | save
      discord_state_status
      ;;
    enable | disable)
      [ "$#" = 0 ] || err 'Unexpected Discord state arguments'
      if [ "$operation" = enable ]; then
        jq -e '(.discord.configured == true) and (.discord.blocked != true)' "$STATE" >/dev/null || err 'Configure a valid Discord destination before enabling; reconfigure if correction is required'
      fi
      enabled=false
      [ "$operation" != enable ] || enabled=true
      result=$(jq -L "$ROOT/lib" --argjson enabled "$enabled" 'include "notifications"; .discord=discord_settings | .discord.enabled=$enabled' "$STATE")
      printf '%s\n' "$result" | save
      discord_state_status
      ;;
    result)
      [ "$#" = 0 ] || err 'Delivery result must be provided on stdin'
      patch=$(cat)
      printf '%s\n' "$patch" | jq -e 'type == "object" and
        (keys == ["ambiguous","delay_seconds","ids","outcome"]) and
        (.ids | type == "array" and length > 0 and length <= 100 and
          all(.[]; type == "string" and length <= 160) and (unique|length)==length) and
        (.outcome == "accepted" or .outcome == "rate_limited" or
         .outcome == "temporary_error" or .outcome == "ambiguous" or .outcome == "permanent_error") and
        (.delay_seconds | type == "number" and . >= 0 and (isnan|not) and (isinfinite|not)) and
        (.ambiguous | type == "boolean")' >/dev/null 2>&1 || err 'Invalid delivery result'
      # A helper cannot acknowledge a missing or already acknowledged record.
      jq -e --argjson patch "$patch" '([(.notifications // [])[] | select(.status == "pending") | .id]) as $pending |
        all($patch.ids[]; . as $id | $pending | index($id) != null)' "$STATE" >/dev/null || err 'Delivery result does not match pending work'
      result=$(jq -L "$ROOT/lib" --argjson patch "$patch" --argjson now "$(date +%s)" \
        'include "notifications"; discord_apply_result($patch; $now)' "$STATE")
      printf '%s\n' "$result" | save
      discord_state_status
      ;;
    *) err 'Unknown Discord state operation' ;;
  esac
}
