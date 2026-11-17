# Durable delivery transitions. Imported only by the shell-owned state operations.
def discord_defaults:
  {enabled:false, configured:false, destination_kind:null, blocked:false,
   last_result:null, retry_after:0};

def discord_settings: discord_defaults + (.discord // {});

def discord_transport_allowed:
  (.mode != "fixture" or (discord_settings.destination_kind == "loopback_test"));

def enqueue_notice($alert; $event; $reason; $now):
  discord_settings as $settings |
  if $settings.enabled and $settings.configured and
     ($event.provenance == "journal" or $settings.destination_kind == "loopback_test") then
    ("discord:" + $event.id + ":" + $reason) as $id |
    .notifications = ((.notifications // []) |
      if any(.[]; .id == $id) then . else
        . + [{id:$id, alert_id:$alert, reason:$reason, created_at:$now,
              status:"pending", attempts:0, next_attempt_at:0,
              last_result:null, ambiguous:false, delivered_at:null}]
      end)
  else . end;

def discord_summary($now):
  discord_settings as $settings |
  [(.notifications // [])[] | select(.status == "pending")] as $pending |
  (discord_transport_allowed) as $allowed |
  $settings + {
    pending:($pending|length),
    delivered:([(.notifications // [])[] | select(.status == "delivered")]|length),
    transport_allowed:$allowed,
    provider_state:(if ($settings.enabled|not) or ($settings.configured|not) then "disabled"
      elif ($allowed|not) then "fixture_destination_mismatch"
      elif $settings.blocked then "needs_configuration"
      elif $settings.retry_after > $now then
        (if $settings.last_result == "rate_limited" then "rate_limited" else "delivery_error" end)
      elif ($pending|length) > 0 then "pending"
      elif $settings.last_result == "accepted" then "delivered"
      else "configured" end)
  };

def discord_snapshot($now):
  . as $state | discord_summary($now) as $summary |
  $summary + {mode:(.mode // "live"), items:(
    if $summary.enabled and $summary.configured and ($summary.blocked|not) and
       $summary.transport_allowed and $summary.retry_after <= $now then
      [(.notifications // [])[] |
        select(.status == "pending" and .next_attempt_at <= $now) |
        . as $notice |
        ($state.alerts[] | select(.id == $notice.alert_id)) as $alert |
        {id:$notice.id, reason:$notice.reason, created_at:$notice.created_at,
         attempts:$notice.attempts,
         alert:($alert | {id,source_ip,failure_count,severity,explanation,provenance,last_seen})}
      ] | sort_by(.created_at, .id) | .[:100]
    else [] end)};

def discord_apply_result($result; $now):
  .discord = discord_settings |
  .notifications = ((.notifications // []) | map(
    if .status == "pending" and (.id as $id | $result.ids | index($id) != null) then
      .attempts += 1 | .last_result=$result.outcome |
      .ambiguous=(.ambiguous or $result.ambiguous or $result.outcome == "ambiguous") |
      if $result.outcome == "accepted" then .status="delivered" | .delivered_at=$now
      else .next_attempt_at=($now + $result.delay_seconds) end
    else . end)) |
  .discord.last_result=$result.outcome |
  .discord.retry_after=($now + $result.delay_seconds) |
  if $result.outcome == "permanent_error" then .discord.blocked=true else . end;

def retention_cleanup($now):
  ($now - .config.retention_days*86400) as $cutoff |
  [(.notifications // [])[] | select(.status == "pending") | .alert_id] as $pending_alerts |
  .alerts |= map(select(.last_seen >= $cutoff or
    (.id as $id | $pending_alerts | index($id) != null))) |
  [.alerts[].event_ids[]] as $keep |
  .events |= map(select(((.timestamp // .received_at // $now) >= $cutoff) or
    (.id as $id | $keep | index($id) != null))) |
  .sources = ((.sources // {}) | with_entries(select(.value.last >= $cutoff))) |
  if has("notifications") then
    .notifications |= map(select(.status == "pending" or
      (.delivered_at // .created_at // $now) >= $cutoff))
  else . end;
