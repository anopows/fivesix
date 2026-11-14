# Public-launch implementation decisions

The complete 14 November 2026 Claude design is the implementation baseline. These corrections close security or preservation gaps discovered while implementing it.

- Email plus and dot aliases are merged only for Gmail/Googlemail, whose mailbox alias semantics are known. Other providers may treat these as distinct addresses. This supersedes the universal plus-removal rule and its A1 expectation.
- First-time Google linking for third-party email addresses requires a fresh email confirmation unless Google provides a verified Workspace hosted-domain claim. Existing immutable Google subject links remain valid. Google can retain a verified third-party address after its mailbox changes hands.
- Account deletion preserves quarantined projects. Users cannot remove material under an operator preservation hold by deleting their account.
- Sign-in email success copy is deliberately conditional, because banned/closed sign-ups must not disclose account existence or claim that mail was sent when it was suppressed.
- No owner identity, legal approval, authority-reporting procedure, provider credentials, or calibration evidence is fabricated. Production gates remain closed until real evidence exists.

## Verification and release status

The user explicitly authorized publication, merges, encrypted Mac backups and deployment. Both tested PRs are merged; the compatible five·six 1.2 and Songfinder 0.3 foundations are deployed. The full 2.1 implementation remains gated. See PUBLIC_LAUNCH.md and RUNBOOK.md for evidence and remaining inputs.

The existing production host was checked read-only: 4 vCPU, about 8 GB RAM, 80 GB disk. It does not meet the design M3 requirement (6 vCPU, 16 GB RAM, 160 GB disk). Existing service health remained green at the check.

- Per-video egress checks the proposed total, rather than permitting one request to overshoot. Stored-byte admission includes the incoming reservation, and derived-file totals are reserved before upload so partial work cannot bypass the hard cap.
- Removal notices say files are queued for deletion, matching asynchronous cleanup. The original design's immediate-deletion wording was inaccurate.
- Failed screening writes result=error as an additional diagnostic state; failures never publish a video. No error is represented as a passing screen.
