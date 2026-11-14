# Progress Bubble mobile and QR sharing

## Intent and prior decisions

Extend the existing desktop skill so a task running on a desktop or in a cloud coding session can be followed from another device. Keep the desktop-only mode working without hosting. The user has requested a `progress-bubble-mobile` branch, QR feasibility and implementation, and Cloudflare setup using the existing signed-in account. The user requires no hosting charges, no end-user accounts, private per-session links, and English project documentation. The existing mobile mockup establishes the visual direction.

## Approaches

1. GitHub Pages alone: static frontend, no reliable server-side authorization, updates or expiry. Rejected against the privacy and live-update requirements.
2. GitHub Pages plus Cloudflare Workers/D1: viable, but adds cross-origin deployment and configuration for no benefit here.
3. Cloudflare Workers Static Assets plus a Worker API and private D1 database: recommended continuation of the architecture already discussed. Keep code in this repository, deploy a dedicated application and database in the user's account, use the supplied workers.dev subdomain, and do not enable paid products, purchase a domain or alter existing applications/tunnels.

## User experience

- Desktop/local mode stays the default. Sharing is opt-in: the agent uses an explicit web-sharing argument after the user requests cross-device tracking, or the user enables sharing for that task from the native card.
- A task's sharing view displays its read-only link and a locally generated QR code. The QR opens that exact task on another device. Generate the QR on the device from bundled, licensed code; never send the secret URL to an external QR-generation service.
- Desktop users can open the sharing view from a discreet card action. A cloud-only user receives the same clickable HTTPS link in the conversation, with no Tkinter requirement.
- The responsive page has title, status, short message, agent-reported percentage, clearly labeled smooth visual estimate and time remaining. Preserve the 95% automatic visual ceiling and confirmed completion at 100%.
- English and Portuguese follow browser language. Preserve user-supplied title/message. No global directory, account dashboard or list of other sessions.
- Show useful loading, stale/offline, expired, revoked and unavailable/quota states. Never imply synchronization when updates fail. A reconnect refreshes the saved state. Cached content is cleared when access expires.
- Poll the API every 15 seconds while the page is visible, stop when hidden, and stop after expiry/revocation. Animate locally between polls. Fetch once on return to the foreground.

## Session lifecycle and data minimization

- One independent session per demand, with a random nonsequential ID and separate cryptographically random 256-bit read and write capabilities. No user accounts, names, emails, passwords or device fingerprints.
- Store only ID, capability hashes, short title/message, canonical status, actual percent, estimate/visual anchors, creation/update times, fixed hard expiry and first completion time. No source code, conversation text, local filesystem paths, executable paths or conversation links are uploaded.
- Default maximum lifetime is 24 hours from creation. First confirmed completion shortens access to the earlier of hard expiry and one hour after completion. Later requests cannot extend that deadline or revive an expired/revoked session.
- Every API read/write checks authorization and expiry server-side. A scheduled, indexed cleanup removes expired records in bounded batches. Logical access expiry is immediate even if physical cleanup or provider backup retention takes longer. Document D1 backup retention rather than promising erasure from every provider copy immediately.
- No endpoints list all sessions. Capability possession grants access, so forwarding a read link also grants access until expiry. This provides separation between sessions, not identity verification or end-to-end encryption.

## API and browser boundary

- `POST /api/sessions`: validate a small, strictly bounded JSON payload; create the record and return its ID, writer capability and reader URL exactly once. No persistent account credential is required for task creation.
- `GET /api/sessions/:id`: require the reader capability in an Authorization header, return only the public task payload, and never return either capability or its hash.
- `PATCH /api/sessions/:id`: require the writer capability, validate the same canonical status/percent rules as the Python helper, preserve fixed expiry, and update only this session.
- `DELETE /api/sessions/:id`: require the writer capability and revoke access immediately. Treat this as revocation for the caller's own task; final physical cleanup follows the session retention policy.
- Read capability is carried in the URL fragment, not the path/query. Frontend captures it locally, removes it from the displayed URL history entry and keeps it only in sessionStorage/in-memory state for reload; explicit copy/share regenerates the complete private link.
- API responses are `Cache-Control: no-store`; page and API use no-referrer and restrictive CSP. Serve all scripts, fonts and QR assets locally. Never insert title/message as HTML. No analytics or request-body/header/token logging.
- Invalid/missing credentials and nonexistent sessions do not expose other session metadata. Rate-limit creation and invalid requests, bound body sizes, use parameterized indexed SQL, and cap concurrent active records. Limits are implementation choices to document and test; public anonymous creation cannot guarantee resistance to distributed quota exhaustion.

## Desktop/cloud client integration

- Keep Python 3.10+ for the skill. Existing desktop installation remains usable without the web feature or new services.
- A small standard-library HTTPS client handles create/update/revoke. A server URL is explicitly configured; validate HTTPS and reject redirects that could forward writer credentials elsewhere.
- Writer capabilities are stored only in a private per-user session sidecar outside the repository/deliverables; POSIX mode 0600 and the user's application-data directory on Windows. Never embed writer credentials in HTML/QR/status JSON, print them, commit them or put them in the model-visible final output.
- Local files remain the primary progress source. After sharing is enabled, successful agent updates send only the allowlisted fields to the API. Network failure must not prevent local progress or desktop completion; record a local sync error and support retry without silently creating duplicate sessions.
- Copy/QR presentation may use a narrowly scoped, bundled third-party QR encoder with its license. The QR dependency must not add network requests at viewing time. Choose the smallest maintained encoder that can be independently decoded in tests.

## Deployment, cost and authorization

- Dedicated Worker `progress-bubble-mobile` and D1 database `progress-bubble-mobile`, subject to availability. One same-origin deployment serves assets and /api routes, using Workers Free and D1 Free only.
- Current account was observed to have the free daily request quota and an existing workers.dev subdomain. Keep existing apps, tunnels, routes, account settings and billing untouched.
- Free-tier quota exhaustion must deny requests, not bypass authorization or switch to paid service. Stop polling inactive/completed pages, enforce limits and surface temporary unavailability. Do not promise unlimited availability or zero agent-subscription costs.
- Use existing Cloudflare authorization if available. If new OAuth/API-token access, billing changes, terms acceptance or broader repository permissions are required, present the concrete requested access to the user before that action. Never extract browser cookies/session credentials.
- New public deployment contains only application code/assets and synthetic validation tasks. Actual user task metadata is uploaded only when task sharing is requested/enabled.
- Deployment will be manually reproducible with documented commands/configuration. Credentials are not committed. Git branch stays separate from main; no merge to main is requested.

## Implementation boundaries

Keep each new first-party feature at approximately 350 implementation lines or less; separate independently testable responsibilities (session API, storage/lifecycle, frontend viewer, QR presentation, Python transport and native entry point). Avoid rewriting unrelated rendering or existing progress behavior.

## Validation and delivery

- Preserve the existing 53 Python tests. Add session isolation/read-write role tests, expiry/revocation/retention tests, malformed/oversized payload and injection tests, anonymous creation limit tests, stale/concurrent update handling, and no-secret-output tests.
- Test QR decoding against the exact generated reader URL, without network QR services.
- Test the viewer's loading/active/completed/expired/offline states, both languages, responsive widths and polling visibility behavior. Check Python/JS smooth progress consistency.
- Use local Worker/D1 integration tests before deployment. After deployment, use synthetic sessions to verify one session cannot access or update another, reader cannot write, writer cannot read as a reader, wrong/expired keys fail and no credentials appear in URLs/log output.
- Verify both desktop sharing and a cloud-compatible CLI invocation; physical mobile scanning remains a user/device acceptance check unless a device is available. Provide a working synthetic demo and visible QR, deployment URL, branch and exact checks.
- Update README in English and skill instructions with setup, optional sharing, privacy/capability limitations, retention, free quotas and deployment commands in the same delivery.

## Builder decisions and explicit exclusions

Builder chooses small internal libraries, precise per-request/active-session limits, file/module layout and testing harness. No login system, payments, permanent history, push notifications, mobile OS overlays, custom domain, general-purpose file uploads or cross-user session directory in this version. No PWA/service-worker caching of private responses. No automatic sharing of all existing desktop tasks.

## Approval status

Approved by the user on November 14, 2026 (America/Cuiaba): "Aprovar e implementar". Independent builder check: nothing important left. Implementation and free-tier Cloudflare configuration are authorized; any new security-sensitive access grant remains subject to its own action-time approval.
