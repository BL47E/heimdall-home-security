# Dashboard pages and visual redesign

Owner-requested change: separate Overview, Investigations, Activity and Settings pages, using a black/off-white terminal style and locally bundled JetBrains Mono. This replaces the earlier Tokyo Night styling.

## Implemented

- `/overview`, `/investigations`, `/activity` and `/settings` are direct page URLs. `/` opens Overview. Navigation uses ordinary links; the shared shell displays one page at a time.
- Login preserves the requested page. Each page requests its relevant dataset from the existing authenticated shell bridge.
- JetBrains Mono Regular and Medium are bundled under `web/static/fonts/`, with their OFL license. The HTTP server allows only the specific font files and existing static assets.
- Existing owner-token authentication, session cookies, CSRF and Origin checks remain in place. Records remain local; no monitoring rules or network response actions were added.

## Browser evidence

Checked through the T3 browser on the Mac at `http://localhost:8765`, using the isolated `/tmp/heimdall-dashboard-demo` **synthetic sample state**. This is not the live blue VM dashboard.

- Direct unauthenticated `/investigations` login retained that URL and displayed only Investigations.
- Alert selection displayed supporting evidence and review history. Mark reviewed changed the list and action to Reviewed/Reopen; reopening restored Needs review. Report access returned HTTP 200.
- Settings loaded the existing threshold of 4. Editing to 5 marked the form unsaved and caused the cancelable leave-page event to request a warning. Saving worked; the demonstration threshold was restored to 4.
- Clicking Activity changed the URL and displayed five sample events. Browser Back returned to Settings and Forward returned to Activity.
- Initial 390px phone and 1280px desktop checks showed no horizontal overflow. A 768px Settings check also fit within the viewport.
- After integration, navigation text measured 14px, the local font loaded, and the final 390px Overview still had no horizontal overflow. Navigation and report links have hover/focus line transitions; the stylesheet disables their transitions for reduced motion.
- An open investigation reflected review/reopen changes after refresh. A deliberately delayed alert response could not repopulate the hidden application after sign-out: alerts, selected alert, configuration and session state remained cleared.
- Clicking Sign out cleared Settings. Browser Back returned to Investigations with the login screen visible and no alert records loaded.

## Automated checks

The integration handler ran `python3 -m unittest tests.test_web -v`: **9 tests passed**, including actual HTTP-to-shell integration, direct page/font serving and rejected request paths. `python3 -m py_compile web/server.py`, `node --check web/static/app.js` and `git diff --check` passed. No shell detection behavior changed in this redesign.

## Limits

The checks above used synthetic state. The later deployment entry records authenticated HTTP verification against blue’s live state and the deployed sidebar update. Boot recovery, provider integration, and full accessibility and concurrent-session audits remain open. [Live deployment and sidebar evidence](../../diary.md)
