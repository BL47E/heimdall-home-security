# Heimdall

Heimdall is a home security overview that receives selected events from personal systems and helps the owner understand which events merit attention.

## Security events

**Event**:
A timestamped observation emitted by a device or service, such as a failed login or configuration change.
_Avoid_: Alert, when referring to an individual source observation.

**Alert**:
A Heimdall finding that groups one or more events with a rule match and an explanation for the owner.
_Avoid_: Event, incident, case.

**Indicator**:
A technical value that may help identify suspicious activity, such as an IP address, domain, URL, or file hash.
_Avoid_: IOC in user-facing copy; expand “indicator of compromise” when needed in technical documents.

**Rule**:
A named, versioned condition that matches event facts and explains why Heimdall raised an alert.
_Avoid_: Detection, when referring to the configured condition itself.

**Enrichment**:
Optional context looked up for a selected indicator from a local or external source.
_Avoid_: Verification; an external reputation result is one signal, not proof that an event is safe or malicious.

**Recommendation**:
A suggested next step that the owner can review and carry out.
_Avoid_: Response action, when Heimdall has not actually changed a device.
