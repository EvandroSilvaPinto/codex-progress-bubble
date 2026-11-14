# Mobile hosting and privacy

The deployment at https://progress-bubble-mobile.dev-evandrosilvapinto.workers.dev serves a static viewer and private session API from one Cloudflare Worker. A dedicated D1 database is bound as `DB`; hourly cron deletes expired records in bounded batches. Existing unrelated resources are not used.

## Deploy your own free instance

Requirements: Node 24+, npm and a Cloudflare account on Workers Free. Desktop-only tracking still requires only Python and has no npm or pip dependencies.

1. Run `npm ci` and `npm test`.
2. Run `npx wrangler login --scopes account:read user:read workers_scripts:write d1:write --use-keyring`. Review the OAuth consent. Background access is required for token refresh. Follow Wrangler's official keyring setup when prompted; do not commit its local configuration.
3. Run `npx wrangler d1 create progress-bubble-mobile`. Replace `database_id` in `wrangler.jsonc` with the returned ID. This repository's ID belongs to its existing deployment; a fork must create its own database. Change the Worker/database names and rate-limit namespace IDs if those names already exist in your account.
4. Run `npx wrangler d1 migrations apply DB --remote`, then `npx wrangler deploy`.
5. Set `PROGRESS_BUBBLE_WEB_URL` to the exact HTTPS origin printed by deploy, or replace the public `url` in `skills/progress-bubble/web-service.json` before installation. Explicit CLI opt-in uses `--web-url`.

No paid subscription, custom domain, tunnel or inbound connection to the user's machine is needed. Do not enable Workers Paid, paid integrations or analytics to use this feature. Application observability is disabled. Cloudflare still operates the underlying infrastructure and may retain its own service/security metadata under its policies.

## Quotas and predictable failure

Workers Free permits 100,000 requests/day and 10 ms CPU/request; D1 Free includes 5 million rows read/day, 100,000 rows written/day and 5 GB total storage (500 MB per database). These are account-wide allocations and can change; verify the linked documentation before changing deployment plans. Free quotas are limits, not an automatic paid upgrade. When exhausted, updates/viewing can fail; the local tracker continues to work and the viewer never bypasses authorization.

One visible viewer polls every 15 seconds (roughly 5,760 API reads/day if kept visible continuously). Hidden viewers pause. The application also restricts creation to 5 requests/minute/IP, API requests to 120/minute/IP and live sessions to 500. Cloudflare rate limits are local/best-effort, not a billing meter or a substitute for authentication.

## Session lifecycle

Each session has independent 256-bit reader/writer secrets. D1 stores SHA-256 hashes; only the reader is included in the link/QR. A timestamp plus 80 random bits identifies creation attempts. New creation identities must be within five minutes of server time: keep the publishing machine clock synchronized. Existing idempotent retries can outlive this acceptance window while the original session remains active.

An expired/revoked identity cannot be reused to revive the original reader link. Early revocations retain an inaccessible tombstone for at least ten minutes, beyond the creation window including clock skew, before cleanup. Cancellation is persisted even when the first create response was lost or the POST is still in flight. Fixed lifetime is at most 24 hours from server creation and at most one hour after first completion. Updating a completed task cannot reopen it or extend that lifetime.

Expiry is enforced on every request, independently of cleanup. Hourly cleanup removes at most 500 expired rows; D1 Free Time Travel recovery backups can retain prior data for seven days. This is logical expiry, not immediate physical erasure. Don't put sensitive information in titles/messages.

Readers are bearer links: anyone you share one with can view that task until expiry/revocation. They cannot update it. The browser keeps the reader token in memory/sessionStorage for reload and removes its fragment from the visible address. Copy/QR reconstructs the read-only URL. It never calls a QR provider, CDN or analytics service. The writer stays in user application configuration, outside deliverables; back up and protect that directory appropriately.

The page distinguishes a reachable API from recent agent updates. After 90 seconds without an agent update it labels the data stale, without adding a last-update clock to the interface. The exact percentage reported by the agent is shown separately from smooth estimated progress. Reconnection cannot infer actual task progress: the executing agent still needs to publish updates.

The Python publisher identifies itself as `ProgressBubble/1.0`. Cloudflare rejects the default urllib user agent on managed workers.dev hosts with error 1010; no browser impersonation or security-setting changes are needed. See [Cloudflare error 1010](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/).

## Validation and maintenance

Run `python -m unittest discover -s tests -v` and `npm test` before deployment. Tests use in-memory SQLite, capability isolation, malformed input, expiry/replay, atomic completion/cancellation races, HTTPS failures, browser lifecycle, independent QR decoding and the original desktop regressions. Update README with every delivered behavior change.

Redeploy with `npx wrangler deploy`. Review migrations before applying them to an existing database. Never commit credentials, private sidecars or real task links. The checked-in service URL/database ID are public configuration, not credentials.

Sources: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [D1 limits](https://developers.cloudflare.com/d1/platform/limits/), [D1 Time Travel](https://developers.cloudflare.com/d1/reference/time-travel/), [rate limits](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/), [Wrangler](https://developers.cloudflare.com/workers/wrangler/commands/general/).
