def scalar: if type == "string" then . else null end;
def parse_record($provenance):
  . as $r |
  ($r.MESSAGE | scalar) as $m |
  ([try ($m | capture("^(?<verb>Accepted|Failed) password for (?:(?<invalid>invalid user) )?(?<user>.*?) from (?<ip>\\S+) port [0-9]+ ssh2(?: .*)?$")) catch null][0] // null) as $p |
  ($r.__REALTIME_TIMESTAMP | if type == "string" and test("^[0-9]{1,16}$") then . else null end) as $us |
  {id:null,cursor:($r.__CURSOR|scalar),timestamp:(if $us != null then ($us|tonumber)/1000000 else null end),
   timestamp_us:$us, source_ip:($p.ip // null), username:(if ($p.user // "") == "" then null else $p.user end),
   outcome:(if $p.verb == "Failed" then "failure" elif $p.verb == "Accepted" then "success" else "unsupported" end),
   invalid_user:(if $p.invalid == "invalid user" then true else null end),
   message:($m // ""), notes:[],provenance:$provenance,preceding_failures:null} |
  if $p == null then .notes += ["Authentication interpretation unsupported; not counted as an attempt"] else . end |
  if .source_ip == null then .notes += ["Source address unavailable; excluded from the source rule"] else . end |
  if .username == null then .notes += ["Username unavailable; success correlation is unknown"] else . end |
  if .timestamp == null then .notes += ["Time unavailable; excluded from the time-window rule"] else . end;
if type == "object" then parse_record($provenance) else error("Journal record must be an object") end
