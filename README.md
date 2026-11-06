# SmartTube for Gen5W — Abro fork

This fork of [KramerTech/gen5-SmartTube](https://github.com/KramerTech/gen5-SmartTube)
omits the application's Park-only restriction while retaining the Android 4.4
compatibility fixes, bundled Conscrypt TLS and left-edge swipe-back gesture.
It changes SmartTube only; it does not disable a vehicle-wide regulation service.
**Do not watch or operate video while driving.**

Requires NEMESIS 1.16+ and [Video Codec Fix (`media.codecs`) 2.1+](https://github.com/KramerTech/gen5-codec-patch).
Vehicle playback, audio routing and compatibility with other plugins are not yet
verified. Passing a build is not a vehicle test.

## Keeping the fork through updates

- `tools/patch.py` omits the regulation injection entirely.
- `tools/verify_fork.py` checks the patch set and fork identity, then checks both
  the patched tree and rebuilt APK for known regulation classes, service calls,
  broadcasts and permissions. It also checks the retained compatibility fixes.
- The APK's update feed points to `Abro86/gen5-SmartTube`. A distinct NEMESIS ID,
  `local.abro.smarttube`, separates the fork from the original package listing.
- All releases use one private signing key whose public certificate digest is
  pinned in `smarttube.conf`. Keep a private backup of this key and password.
- A twice-weekly workflow checks for a newer stable upstream APK and builds a
  **draft** candidate. Existing candidates are not rebuilt. Unknown source
  layouts or a changed Gen5W port commit stop the build for review.
- After inspecting a newer Gen5W port, merge its needed changes without restoring
  the injection, update `upstream-base.json`, run tests, and build again.

This cannot guarantee compatibility with arbitrary future releases or detect an
entirely different restriction implementation. Review remains necessary. Installing
someone else's APK, overwriting this branch, or changing the checks can restore
the restriction. Scheduled GitHub workflows can also be disabled after inactivity.

## Builds and validation

GitHub Actions → **Build fork candidate** → **Run workflow**. Use `32.68s` for
the initial candidate, or leave the upstream tag blank to check the latest stable
release. Fork revisions are 51–99; increment the revision when rebuilding the same
upstream version after a source change. The workflow records exact source and APK
provenance and verifies the upstream download against GitHub's SHA-256 digest.

Repository secrets required: `SMARTTUBE_KEYSTORE_B64` and `SMARTTUBE_KEY_PASS`.
Never commit private keys or passwords. Builds holding the key have read-only
repository permissions; a separate job saves the draft release.

Run local contract tests with `python -m unittest discover -s tests -v`.
The complete build also verifies the API 19 signature, update URL, APK contents
and ZIP checksums. Candidate releases remain drafts until separately tested.
Once validated, publish an appropriate stable release to make it available through
the fork's update feed. Updates are installed as NEMESIS packages, not through
SmartTube's built-in APK installer.

## Installation and recovery

Revision 52 includes KramerTech's per-app modem guard from commit
`6b56e7610eb3615ac40274e2805f7741700c43ea`. The NEMESIS package starts
a root service that filters outbound IPv4 and IPv6 traffic by SmartTube's
Android UID. It permits loopback, Wi-Fi and Bluetooth/USB tethering. Connections
over the built-in modem are blocked once the rules are active. System DNS
uses its own UID. Install the package ZIP to get the service.

NEMESIS runs a cleanup hook before update or removal. Cleanup requires firewall
privileges. When an uninstall runs with reduced ADB capabilities, a full head-unit
reboot clears residual rules.

Back up the head unit's current affected files and settings first. Install the
codec dependency before the SmartTube package through supported NEMESIS methods.
Use the plain package ZIP for `nemesis install --update`; the `-usb.zip` is a
different wrapper intended for extraction at a USB drive's root.

Do not co-install the original `smarttube` package: both contain Android package
`org.smarttube.stable`. Changing from another signing key may require uninstalling
that app and lose its settings/sign-in. Subsequent builds of this fork retain the
same key. NEMESIS Manager shows this package as **SmartTube (Abro)**.

Validate playback, sound, Back, clean exit and return to normal audio while parked.
Verify existing head-unit features before and after restart. Package/file checks
alone do not establish functional compatibility. No workflow connects to or
installs anything on a vehicle.

To remove, uninstall `local.abro.smarttube` through NEMESIS first. Remove
`media.codecs` only if no other installed package needs it; its own documented
recovery restores the media files it owns. Preserve independent backups.

## Attribution

Based on KramerTech commit `41c0fb59443f6008fb2f1a186b14427d936c6346` and
[yuliskov/SmartTube](https://github.com/yuliskov/SmartTube). Original MIT licenses
and notices are retained. Fork changes are documented here and in the package's
`notices/NOTICE.txt`. No private vehicle captures or proprietary firmware belong
in this repository.
