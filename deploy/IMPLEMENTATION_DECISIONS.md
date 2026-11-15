# Public-launch implementation decisions

The complete 14 November 2026 Claude design is the implementation baseline. These corrections close security or preservation gaps discovered while implementing it.

- Email plus and dot aliases are merged only for Gmail/Googlemail, whose mailbox alias semantics are known. Other providers may treat these as distinct addresses. This supersedes the universal plus-removal rule and its A1 expectation.
- First-time Google linking for third-party email addresses requires a fresh email confirmation unless Google provides a verified Workspace hosted-domain claim. Existing immutable Google subject links remain valid. Google can retain a verified third-party address after its mailbox changes hands.
- Account deletion preserves quarantined projects. Users cannot remove material under an operator preservation hold by deleting their account.
- Sign-in email success copy is deliberately conditional, because banned/closed sign-ups must not disclose account existence or claim that mail was sent when it was suppressed.
- No owner identity, legal approval, authority-reporting procedure, provider credentials, or calibration evidence is fabricated. Production gates remain closed until real evidence exists.

## Verification and release status

The full 2.1 implementation has been published and merged into the default branch. Production was first deployed to the compatible 1.2 foundation release. This 2.0.1 branch is the intermediate accounts release; it backports the default branch's explicit Google authorized-party validation and aggregate login metrics. Screening and monthly storage migration remain in M3 and must not be enabled as part of M2.

Before deploying this branch: verify its exact CI revision, take and restore-check an encrypted database backup, stop both five·six services, and migrate schema 0 to 1 atomically. Assign existing projects to the configured admin, retain the upload pause and cap sign-ups at five. Keep legal readiness false until reviewed content is installed. SMTP and Google must be configured, with Google in Testing. A rollback requires restoring the matching pre-migration database as well as the prior code.

The existing production host was checked read-only: 4 vCPU, about 8 GB RAM, 80 GB disk. It does not meet the design M3 requirement (6 vCPU, 16 GB RAM, 160 GB disk). Existing service health remained green at the check.
