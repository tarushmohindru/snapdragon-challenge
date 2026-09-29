# Participant handoff — ClipTrail final submission

The local Brief, Pitch, and 88-second demo are prepared. **No GitHub repository has been published, no video has been hosted, and no Unstop entry has been submitted.** Complete the steps below in order. The current submission candidate is on local branch `main` in `.publication.git`; the supplied `.git` directory is empty/read-only, so use the exact `GIT_DIR` and `GIT_WORK_TREE` prefixes below.

## 1. Review local files

Open and visually review, one at a time:

1. `ClipTrail-Brief-Project-Description.pdf` — recommended Brief upload.
2. `ClipTrail-Brief-Project-Description.docx` — editable backup.
3. `ClipTrail-Pitch.pdf` — seven slides.
4. `ClipTrail-Pitch.pptx` — same seven slides and speaker notes in PowerPoint.
5. `ClipTrail-Demo.mp4` — 88.000 seconds, 1920×1080 H.264/AAC, screen-only. The real search result is `sintel_trailer-480p.mp4` at 23.25 s; playback is shown.
6. The public README and architecture diagram after the GitHub push.

The video is supporting material unless the authenticated portal makes it mandatory. Music and film credits are in `demo/credits.md` and in the rendered video. The MP4 is intentionally Git-ignored and remains a local upload artifact.

## 2. Create and push a public GitHub repository

In your signed-in GitHub account, create an **empty public repository** named `cliptrail` (or another name you choose). Do not add a GitHub-generated README, `.gitignore`, or license: the local history already contains them. Copy the real repository HTTPS URL. From the project root:

```bash
REPO_URL='https://github.com/YOUR_ACCOUNT/cliptrail.git'
GIT_DIR=.publication.git GIT_WORK_TREE=. git remote add origin "$REPO_URL"
GIT_DIR=.publication.git GIT_WORK_TREE=. git push -u origin main
GIT_DIR=.publication.git GIT_WORK_TREE=. git rev-parse HEAD
GIT_DIR=.publication.git GIT_WORK_TREE=. git status --short
```

Replace `YOUR_ACCOUNT` with the owner displayed by GitHub. If `origin` already exists, run `GIT_DIR=.publication.git GIT_WORK_TREE=. git remote set-url origin "$REPO_URL"` instead of `remote add`. Authenticate using your normal GitHub credential manager or SSH setup; do not put a token into a command, file, or chat. If you use SSH, use the real `git@github.com:OWNER/REPO.git` URL as `REPO_URL`.

Before the public push, read `docs/public-repository-audit.md`: 16 preserved raw evidence files contain historical username-bearing absolute paths. They were kept byte-exact as frozen provenance; the scan found no credential pattern, and no such path appears in the user-facing exports or video. Review that limited disclosure as part of your publication decision.

Open the repository URL in a **signed-out/incognito browser**. Confirm the README renders, the architecture image appears, `LICENSE` and `THIRD_PARTY_NOTICES.md` are present, and the default branch is `main`. Record the URL and exact commit SHA in `final-manifest.md`. Keep the repo public through judging unless official instructions say otherwise.

If you want a frozen tag after visual review and final portal validation:

```bash
GIT_DIR=.publication.git GIT_WORK_TREE=. git tag submission-2026
GIT_DIR=.publication.git GIT_WORK_TREE=. git push origin submission-2026
```

## 3. Host the video only if you choose to share it

Recommended choices: [**YouTube unlisted**](https://support.google.com/youtube/answer/157177?hl=en-CA&ref_topic=9257440) for easy streaming, or a [**GitHub Release asset**](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository?tool=webui) attached to the public repository for a project-owned download link. [Google Drive “Anyone with the link → Viewer”](https://support.google.com/drive/answer/2494822?hl=en) is another option; Google notes that the file owner's name and email may be visible to viewers. Upload `ClipTrail-Demo.mp4`; use `ClipTrail-Demo-Poster.jpg` as a thumbnail if useful. Include the attribution in `demo/credits.md` with the video description or release notes. Open the final URL signed out and confirm that a judge can play or download it without login. Save that URL in `submission-values.md` only if the form offers a video field or you decide to include an optional link. Do not treat the video as a mandatory portal field without seeing one.

For a GitHub Release asset, create a release in the GitHub web UI from the frozen tag, attach the MP4, publish the release, and test the asset URL signed out. YouTube unlisted still requires the link to be shared; it is not private access control.

## 4. Complete the authenticated Unstop form

Use `submission-values.md` for copy/paste text and `unstop-field-map.md` for the known fields. Check the live form's exact accepted formats, size/character limits, required status, declarations, and submission deadline. Upload the Brief **PDF** unless the live instructions favor DOC/DOCX. Upload both Pitch files in their designated fields. If the PPT field rejects `.pptx`, make a legacy `.ppt` copy in Microsoft PowerPoint and visually review it before upload. Never guess a validator limit.

Confirm eligibility, Snapdragon laptop ownership, any employer permission, project/IP rights, any rule concerning a pre-existing proposal, attribution, and Official Rules personally. The public rules say one properly submitted entry cannot be changed. Review each upload preview and URL before pressing Submit. Save the confirmation screen, email, reference number, exact uploaded filenames, GitHub URL/SHA, video URL if used, and `checksums.txt` afterward. Fill `submission-record.md` from the actual receipt.

## 5. Preserve the submitted version

Keep the local exports and MP4, the final Git commit/tag, the portal receipt, and a copy of the exact uploaded files. If you continue development, use a branch or commits **after** the frozen submission tag.
