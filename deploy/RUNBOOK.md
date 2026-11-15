# Operations

See [SELF_HOSTING.md](../SELF_HOSTING.md) for initial installation.

## Update and rollback

Record the deployed commit. Wait for active uploads/jobs, stop API and worker,
back up SQLite with its online backup API, and deploy the reviewed source.
Preserve `/etc/choreo.env`, `/var/lib/choreo`, and models.

Run `uv sync --frozen --extra worker` with the installed uv binary, verify models,
run tests, then restart both services. Validate Caddy before proxy changes.
Roll back to the previous source/lockfile if needed. Review schema compatibility
before restoring old code; never blindly replace a live WAL database.

## Retention

The default is 90 days from upload for practice copies, instrument estimates,
analysis, and exports. Originals are deleted after successful analysis. API access ends at the project deadline.
The worker deletes expired objects and retries failures; R2's 90-day object
lifecycle provides a backstop.

When upgrading an older installation:

1. Increase the bucket lifecycle deletion to 90 days first.
2. Set `CHOREO_RETENTION_SECONDS=7776000` in `/etc/choreo.env`.
3. Back up SQLite and preview:
   `sudo .venv/bin/python scripts/extend-retention.py --days 90`.
4. Apply with `--apply`, then restart both services.

The migration extends only currently available projects to 90 days from their
original upload time. It never revives deleted, failed, or already expired
projects, and never shortens an existing longer deadline.

Run the worker continuously. Media requests recheck access, so holds, removal and expiry revoke previously issued links on the next request. Treat share links as view access.

## Inspect

```sh
systemctl status choreo-api choreo-worker caddy
journalctl -u choreo-worker --since '1 hour ago'
curl --fail https://YOUR_DOMAIN/healthz
df -h /var/lib/choreo
```

Caddy replaces CF-Connecting-IP with the direct peer address so clients cannot
spoof per-IP limits. Review the trust chain if adding a CDN or another proxy.
The supplied configuration assumes direct DNS to the host.

Access logging is disabled. Worker logs contain project IDs and bounded
diagnostics. Avoid posting private links or signed media URLs in reports.
Model-check errors mean assets differ from the manifest. Upload failures can
mean unsupported codecs, limits, or unusable music. Inspect recurring failures,
queue age, and free disk space before increasing quotas.

## Backups

Use SQLite's online backup API, not a copy of only the live database file.
Encrypt off-host backups, restrict permissions, and bound their retention:
records can contain filenames and analysis. R2 is live storage, not an independent
backup. No off-host backup destination is configured by the installer.

## Access and credentials

Accounts own isolated libraries. The admin needs account sign-in plus password/Turnstile step-up for moderation. Guests need a random project link and cannot enumerate the library, delete videos, or overwrite shared count settings.

`/etc/choreo.env` is the persistent application secret file. Rotating the password
hash and clearing session rows signs everyone out, but does not revoke share
links. Delete a project to revoke its link. Rotate R2/Turnstile credentials by
replacing their environment values and restarting both services.

Smoke scripts accept only explicit synthetic fixtures and exercise storage,
worker, signed playback, and exports. Run them as `choreo` with the production
EnvironmentFile. They do not bypass HTTP login or replace browser upload tests.

## KPI counters

The application records aggregate UTC daily counts and daily pseudonymous distinct-visitor hashes in its own SQLite database. The hashes are pruned by the worker cleanup loop and never appear in exports. No access logs are enabled. The app's KPI timer runs its exporter as the application user and writes its JSON under `/var/lib/kpi/data/`; see the separate KPI repository for metric meanings, deployment and how to add fixed metric names. Existing database backups include the counters. Exported counts are best effort and are not an audit log.

## Public launch M1 implementation — 14 November 2026

Legal pages are read from `CHOREO_LEGAL_DIR`; all three must be complete and the legal notice must include `id="report"`. Missing files or unresolved template tokens keep the routes unavailable. Install reviewed operator-specific files outside the repository.

`/healthz` checks the database, a worker heartbeat no older than 120 seconds and the local cost guard. Install `choreo-health.timer` with `/etc/choreo-health.env` containing `HC_HEALTH_URL`. The check verifies HTTPS health and 10 GB free disk.

For nightly backups install `age` and `rclone`, a bucket-scoped `/etc/choreo-backup.conf` (remote `backups`), and `/etc/choreo-backup.env` with `AGE_RECIPIENT` and `HC_BACKUP_URL`. Keep these files mode 0600 owned by choreo. Enable `choreo-backup.timer` for 03:40 UTC. Keep the private age key off the host. Restore quarterly on a separate machine and record the integrity and API checks.

Local foundation acceptance tests passed. The initial local-only assessment was superseded by the staged rollout recorded below. Recurring backups and the monitoring/alert drill subsequently passed on 15 November, as recorded below. The inspected host has 4 vCPU, 8 GB RAM and an 80 GB disk; M3 requires the design's larger host. Existing services were healthy during the read-only check.

## Public-launch implementation, 14 November 2026

See PUBLIC_LAUNCH.md for the authoritative new release procedure and IMPLEMENTATION_DECISIONS.md for security corrections to the handover. These additions supersede old shared-room login instructions for version 2.x. The 2.1 implementation is merged; production runs the staged 2.0.1 accounts release. See the verified status below for completed provider/recovery work and the remaining M3/legal/soft-launch gates.


### Recorded local verification

On 14 November 2026, `uv run --frozen --extra dev --with 'scipy>=1.14,<2' pytest -q` passed all 138 tests. `node --test tests/*.test.cjs` passed 13 tests; every static JavaScript file passed `node --check`, and `git diff --check` passed. The SciPy-enabled run includes the four optional consensus tests omitted by the basic development environment. The localhost SDK-retry test requires permission to bind a local test socket.

Both timing benchmark suites passed all 12 cases (development seed 60117 and validation seed 841903). Hash-verified real screening models loaded locally and rejected a generated 10-second colour-bar/tone clip with `no_person` in 7.258 seconds (10 sampled frames, zero nudity flags, zero person detections). This is a negative smoke result, not a dance-video calibration or a production performance result.

Chrome verification against an isolated local test server completed email request, captured-mail confirmation, private library, quota display and admin password step-up. The confirmation fragment was removed before submission; the browser reported no console errors. Test storage, test Turnstile and captured email were used. Real Google/SMTP delivery subsequently passed on 15 November. Production-host calibration and a new authenticated production upload remain release gates. Linux isolation and existing production playback were subsequently verified below.

## Verified staged rollout — 15 November 2026

On 15 November 2026 the staged accounts release **2.0.1**, revision `05c8a1095723b1fd33a74da5465ac5de198f19da`, was deployed to both five·six processes. [PR #3](https://github.com/anopows/fivesix/pull/3) merged into `launch/m2`; [CI on that exact merge](https://github.com/anopows/fivesix/actions/runs/43675785834) passed. The release passed 99 Python tests (one skipped), 11 Node tests and JavaScript syntax checks. The full 2.1 screening/moderation implementation on `main` is not deployed.

The rehearsed, idempotent schema 0-to-1 migration preserved seven projects, 64 parts and six jobs, assigned all projects to the configured admin and invalidated the old room sessions. Real Google and delivered email-link sign-in both reached the same account and its four ready videos. The live database contains one user, one Google subject link and one consumed email link. Four existing share links and byte-range playback checks passed; anonymous library requests return 401. Public registration remains closed by missing reviewed legal files, the staging signup cap remains five, and uploads remain paused except for the admin. The full admin console and real upload/moderation smoke tests remain M3 work.

Resend Free is configured with verified sender DNS, a sending credential restricted to the notification subdomain, SMTP STARTTLS on port 587, and a 90-message application daily cap. Real sign-in mail and the abuse-forwarding delivery checks passed SPF, DKIM and DMARC. Google requests only OpenID/email, stays External/Testing and has only the owner as a test user. Ireland is the Resend sending region; provider documentation states email/log storage is in the United States. Tracking is disabled. Final legal text must reflect actual processing, not just the sending region.

Nightly encrypted backups now run at 03:40 UTC (five·six) and 03:50 UTC (Songfinder). Each service has its own Object Read/Write credential scoped to the private EU `site-backups` bucket and restricted to the host's IPv4/IPv6. Both credentials work on the host and returned HTTP 403 from the Mac. The bucket expires encrypted backups after 30 days. Fresh post-M2 ciphertext was retrieved, matched to R2 checksums, decrypted off-host and checked for SQLite integrity. Isolated restored APIs served all four practice records and 55 Songfinder results; a synthetic second account in the disposable restored copy had an empty library and received 404 on all 20 owner-route checks. Temporary plaintext copies were removed. The private age identity remains on the Mac only. Encrypted configuration and provider-credential recovery copies were also verified; these are separate from the nightly database archives.

All four Healthchecks monitors and timers are active, with verified failure and recovery email delivery. Health checks run every five minutes with ten minutes' grace; backup checks use one day plus six hours' grace. Both real workers were stopped from 04:15:20 to 04:30:27 UTC under independent automatic recovery timers. Their health endpoints became unhealthy, both DOWN emails arrived at 04:17:44 UTC, and both UP emails arrived at 04:30:39 UTC. APIs and existing media stayed available. Both workers recovered and all API/worker/Caddy services were subsequently active with zero automatic restarts.

The Cloudflare account budget policy is enabled at $60 with email and its existing authenticated webhook attached. Its test email was received; this does not by itself prove a real threshold-triggered webhook delivery. The media and backup tokens are restricted to the host's IPs. The deployed M2 guard still uses lifetime allowances; monthly windows, stored-byte backfill and the M3 limits are not yet installed. Budget notifications are delayed safeguards, not an invoice cap.

SSH now accepts public keys only, root SSH is disabled, UFW is active, and NTP/security updates are configured. Public TCP allowances are 22/80/443; existing Tailscale interface access and UDP 41641 are deliberately preserved. Fresh independent SSH and HTTPS checks passed before cancelling the firewall recovery timer. Automatic security reboots are configured for 04:30 UTC when required; no reboot was performed in this rollout.

The host remains 4 vCPU, approximately 8 GB RAM and 80 GB disk, so the M3 capacity gate remains open. CX43/CX53 capacity was unavailable at Nuremberg; an alternative CPX42 plan is prepared but not purchased. Forty distinct existing dance clips passed local CPU screening with verified model hashes and unchanged thresholds. This is useful calibration evidence, but the normalized existing-library set and ten-minute performance test still need to pass on the production host. Final legal review, the hosting DPA, the incident-reporting/preservation procedure, real M3 upload/moderation checks, Google production publication and the 14-day soft launch remain pending. Green health is not evidence that those gates passed.
