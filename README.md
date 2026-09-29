# iCloud Drive Archive

Small, dependency-free macOS helper for copying iCloud exports into Google Drive for Desktop, checking each file's SHA-256 and byte size, and listing only cloud-uploaded matches as safe to remove.

It does not sign in to Apple or Google, handle credentials, or operate Notes/Voice Memos. Export or copy the files yourself first. Notes exports can be verified as files, but the tool cannot map exported files back to individual Notes entries; delete Notes manually only when you can identify the matching originals.

## Requirements

- macOS with `fileproviderctl` (included by Apple)
- Google Drive for Desktop, signed in and showing the destination folder
- Python 3.9+

## Use

```sh
python3 icloud_archive.py scan ~/iCloud-export manifest.json
python3 icloud_archive.py copy ~/iCloud-export manifest.json "$HOME/Library/CloudStorage/GoogleDrive-ACCOUNT/My Drive/iCloud Archive" --wait
python3 icloud_archive.py verify ~/iCloud-export manifest.json "$HOME/Library/CloudStorage/GoogleDrive-ACCOUNT/My Drive/iCloud Archive"
```

Inspect the verification totals and sample paths. To remove only files that have matching names, sizes, hashes, and completed Drive upload state:

```sh
python3 icloud_archive.py verify ~/iCloud-export manifest.json "$HOME/Library/CloudStorage/GoogleDrive-ACCOUNT/My Drive/iCloud Archive" --delete --min-bytes 5000000000
```

`--delete` is opt-in. The threshold is a guard: if the verified total is lower, no source files are deleted. Successful deletion uses ordinary filesystem removal; items in an iCloud-synced source may go to Recently Deleted and need a separate purge before capacity is reclaimed. Confirm your backup independently before purging.

Manifests contain filenames and content hashes. Keep them private; do not publish manifests from personal archives.

## Limits

- `fileproviderctl` upload state is available only on macOS and depends on Drive for Desktop's provider integration.
- SHA-256 compares the local source with the DriveFS copy; upload state is checked separately. For critical archives, also inspect the files in Drive on the web before deletion.
- This tool cannot promise a particular iCloud storage reduction. Apple may update storage totals later, and shared or deduplicated data may affect the amount.

MIT licensed. See [LICENSE](LICENSE).
