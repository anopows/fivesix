# Operating the public beta

## Owner decision, 15 November 2026

The owner explicitly declined hiring a lawyer and authorized a best-effort public beta, to be improved over the following weeks. This supersedes the previous professional-review launch gate. It does not establish legal compliance, waive third-party rights, or complete a provider agreement. The operator-specific notices are maintained outside the source repository and published at `/terms`, `/privacy` and `/legal` on both sites.

Use the existing host. No Hetzner upgrade is authorized. Keep the 100-account cap, five uploads per rolling day and twenty per rolling 30 days, 500 MB/ten-minute input limit, ten-job admission queue and 10 GB daily source-byte allowance. Keep screening, quotas, signed media, monthly R2 limits, the budget latch and nightly encrypted backups enabled. Do not reset counters to regain allowances. Cloudflare notifications are not a hard invoice cap.

The Google client requests only `openid email`. Google's [audience documentation](https://support.google.com/cloud/answer/15549945?hl=en) explicitly exempts those basic identity scopes from the Testing allowlist restriction. The consent screen can be promoted when console access is available; do not claim it has been promoted until observed. The latest beta validation record distinguishes actual OAuth success from this documented exception.

## Guest uploads

Guest videos are private to the browser that uploaded them and expire after 48 hours. Admission counts reservations, including cancelled uploads, against both the browser and the keyed network address (IPv6 /64). The defaults are one per rolling 24 hours and two per rolling seven days. Account and site capacity limits still apply. A successful email or Google sign-in in the same browser moves unexpired guest videos to the account and extends expiry to the usual 90 days from upload. The owner must select Share to enable a link for a guest-origin video. Existing account links keep working. Keep the operator-owned Terms and Privacy pages in sync with these limits and the essential guest cookie.

## Daily operation

The operator is responsible for checking the abuse mailbox and admin report list daily. Notification mail can be rate-limited, so an empty inbox does not prove the report list is empty. Aim to review illegal reports within 24 hours and other reports within 72 hours; pause uploads if this cannot be covered. Monitor health alerts, costs, disk free space and queue wait during the first 14 days. The observation period starts at actual beta opening, not at code deployment, and cannot be declared complete in advance.

Open `/admin`, sign in as the configured owner, and unlock with the existing admin password. Real password entry remains an owner check; the authenticated host CLI is the tested fallback. Never send the password in chat. Run CLI actions using `systemd-run --quiet --wait --pipe --collect --uid=choreo -p EnvironmentFile=/etc/choreo.env -p WorkingDirectory=/opt/choreo /opt/choreo/.venv/bin/python /opt/choreo/scripts/admin.py` followed by a command from RUNBOOK.md.

For an ordinary privacy or copyright report: record its URL, reporter's description/contact, receipt time and relevant IDs; hold access if credible; assess the rights/consent explanation; remove or restore with a concise reason; offer review within 30 days. Do not disclose the reporter's identity to the uploader unnecessarily. Repeat or serious abuse can warrant an account ban. There is no registered US DMCA agent or claim of safe-harbour status.

## Suspected illegal sexual material or immediate danger

1. Block access immediately. Five·Six illegal reports automatically hold the video. Use `quarantine PID --reason ...` for suspected child sexual abuse or another case requiring authority guidance; record only the minimum factual reason, without graphic descriptions. Pause uploads or ban the source if needed to stop ongoing abuse.
2. Do not download, screenshot, forward or repeatedly view suspected material. Do not include it in email, support tickets, or the Mac backup. Record the URL, project/account ID, timestamps, existing upload hash and actions taken. Database backups contain no media.
3. Promptly use [fedpol's illegal pornography reporting page](https://www.fedpol.admin.ch/en/reporting-illegal-pornography), providing the URL and discovery date/time. For a victim, an immediate threat or a criminal complaint, contact the relevant cantonal police; call 117 for an emergency in Switzerland. The service does not file reports automatically, and the engineer must not submit one without explicit authorization.
4. Tell the authority that access is blocked, the uploaded original is normally deleted after processing, and R2 deletes objects at 90 days even if the application says quarantined. Ask for explicit instructions on any lawful retention, deletion or secure transfer. Act before that deadline. Do not promise indefinite evidence preservation or retain a new copy just in case. If instructions require longer preservation, arrange it specifically and securely; do not disable lifecycle rules for the whole bucket.
5. Record the authority reference and instructions, the next review date and eventual resolution. Review an unresolved quarantine daily until guidance arrives. Follow lawful instructions, document any extension and remove/release when appropriate. Never restore merely because a report is unanswered.

For a suspected personal-data breach, contain the problem, restrict affected access, preserve minimal operational evidence and assess harm promptly. The [FDPIC breach guidance](https://www.edoeb.admin.ch/en/databreach-4) explains Swiss reporting; additional notification duties may apply to affected users. Do not claim every incident has the same reporting threshold or deadline.

## Known work remaining

- The owner must review and personally accept the [Hetzner DPA](https://accounts.hetzner.com/account/dpa) if they agree; the engineer has not signed it. Describe account/contact data, log data, uploaded media/recognition information, users, depicted people and reporters. Save confirmation. This is separate from publishing a home address; none is published.
- Provider processing locations and contracts, any postal-address obligation, EU/UK territorial applicability and recognition-provider licensing have not received professional legal review. Notices disclose known processing and do not certify compliance. Reassess if audience, features, payments or scale change.
- Review operational log, recognizer-cache and local encrypted-recovery retention. Current bounded storage is not a guaranteed age-based deletion rule. Privacy notices describe this limitation. Apply relevant erasures and revoke old sessions/tokens before exposing restored backups.
- The first 14 days require real observation. Reconsider capacity only if the seven-day median queue wait exceeds ten minutes; keep the ten-minute video cap unless the full memory/performance test is repeated.

## Emergency closure

`pause-uploads --reason TEXT` stops new uploads while preserving playback. To also close registrations set `CHOREO_SIGNUP_CAP` no higher than the current user count (at least one) in `/etc/choreo.env`, then restart only `choreo-api`. Keep legal pages available. Do not restore an old database to undo a launch, because it could discard new accounts, erase reports and roll back usage. Use the guarded storage stop for an actual spending incident; inspect the reason and bill before `resume --reviewed`.
