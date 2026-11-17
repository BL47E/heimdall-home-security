# State transitions for supported SSH password outcomes. Input events are data.
include "notifications";
def apply_event($incoming; $now):
  if any(.events[]; .id == $incoming.id) then .stats.duplicates += 1
  else
    .stats.processed += 1 |
    ($incoming + {received_at:$now}) as $e | .config as $config |
    (if $e.provenance == "journal" and $e.cursor != null then .cursor = $e.cursor else . end) |
    if $e.outcome == "unsupported" then .stats.unsupported += 1 | .events += [$e]
    elif $e.timestamp == null or $e.source_ip == null then .events += [$e]
    else
      ($e.source_ip + ":" + $e.provenance) as $key |
      (.sources[$key] // {last:null,burst_start:null,active_alert:null}) as $source |
      if $source.last != null and $e.timestamp < $source.last then
        .events += [$e + {notes:($e.notes + ["Late record retained as evidence; excluded from current rule transitions"])}]
      elif $e.outcome == "success" then
        ($e.provenance == "journal" and ((.monitor.coverage_since // $e.timestamp) > ($e.timestamp - $config.window_seconds))) as $incomplete |
        .events += [$e + {notes:($e.notes + if $incomplete then ["Full preceding window is not covered; preceding failure count is unknown"] else [] end),preceding_failures:(if $e.username == null or $incomplete then null else
          [.events[] | select(.outcome == "failure" and .source_ip == $e.source_ip and .username == $e.username and .provenance == $e.provenance and .timestamp != null and .timestamp >= ($e.timestamp - $config.window_seconds) and .timestamp <= $e.timestamp)] | length end)}]
      else
        .config as $config |
        (if $source.last == null or ($e.timestamp - $source.last) >= $config.window_seconds
         then {last:$e.timestamp,burst_start:$e.timestamp,active_alert:null}
         else $source + {last:$e.timestamp} end) as $next |
        .events += [$e] |
        [.events[] | select(.outcome == "failure" and .source_ip == $e.source_ip and .provenance == $e.provenance and .timestamp != null and .timestamp >= $next.burst_start and .timestamp >= ($e.timestamp - $config.window_seconds) and .timestamp <= $e.timestamp)] as $window |
        if $next.active_alert != null then
          (any(.alerts[]; .id == $next.active_alert and .review_status == "reviewed")) as $reopens |
          .alerts |= map(if .id == $next.active_alert then
            .last_seen = $e.timestamp | .failure_count += 1 | .event_ids += [$e.id] |
            if .review_status == "reviewed" then .review_status = "needs_review" | .review_history += [{timestamp:$now,status:"needs_review",reason:"new_failure"}] else . end |
            .explanation = "\(.failure_count) failed password attempts in this continuous burst; rule initially matched \(.rule.threshold) failures within \(.rule.window_seconds) seconds."
          else . end) | .sources[$key] = $next |
          if $reopens then enqueue_notice($next.active_alert; $e; "reopened"; $now) else . end
        elif ($window|length) >= $config.threshold then
          ("ssh-" + $e.id[0:24]) as $aid |
          .alerts += [{id:$aid,source_ip:$e.source_ip,severity:"MEDIUM",review_status:"needs_review",
            first_seen:$window[0].timestamp,last_seen:$e.timestamp,failure_count:($window|length),
            rule:{id:"ssh-password-burst",version:1,threshold:$config.threshold,window_seconds:$config.window_seconds},
            explanation:"\($window|length) failed password attempts from this source within \($config.window_seconds) seconds.",
            recommendation:"Review the attempted accounts and supporting SSH records. This rule is not proof of compromise.",
            event_ids:[$window[].id],review_history:[],provenance:$e.provenance}] |
          .sources[$key] = ($next + {active_alert:$aid}) |
          enqueue_notice($aid; $e; "created"; $now)
        else .sources[$key] = $next end
      end
    end
  end;
.stats = {processed:0,duplicates:0,unsupported:0,malformed:$malformed} |
reduce $incoming[] as $event (.; apply_event($event; $now))
