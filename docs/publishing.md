# PyPI Trusted Publishing

The public GitHub prerelease is available at
[v0.13.0rc2](https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc2).
The manual [publish workflow](https://github.com/wa-pis/iddqueue/blob/main/.github/workflows/publish.yml) uploads those
exact wheel/sdist files, after checking the recorded candidate SHA and fixed
SHA256 hashes. It does not rebuild the candidate or need a stored API token.

RC2 GitHub assets are verified; the PyPI publication is in progress. RC1 was already published successfully through this workflow.
The trusted publisher is configured; do not add it again or rerun the same
immutable release upload. For a new release, prepare a verified candidate and
update the workflow's version, candidate SHA and hashes first.

## Initial setup reference

The following records the setup used for the first upload. To configure a new
project, sign into [PyPI Publishing](https://pypi.org/manage/account/publishing/)
and add a pending GitHub publisher:

| Field | Value |
| --- | --- |
| PyPI project name | `iddqueue` |
| GitHub owner | `wa-pis` |
| Repository name | `iddqueue` |
| Workflow filename | `publish.yml` |
| Environment name | `pypi` |

If you already own the PyPI project, add the same publisher in its project
Publishing settings instead. A pending publisher creates the project on first
successful upload; it does not reserve the name beforehand.

For the initial upload after registration, run **Publish RC to PyPI** on `main`, or:

```sh
gh workflow run publish.yml --repo wa-pis/iddqueue --ref main
```

Check actual job success, PyPI version `0.13.0rc2` and both file SHA256 values,
then install `iddqueue[binary]==0.13.0rc2` in a clean environment. Do not treat
workflow preparation or a queued job as successful publication. Do not paste
API tokens into issues or chat. This workflow is scoped to the exact configured RC;
a future version needs its own verified candidate and hashes.

References: [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[uv publishing](https://docs.astral.sh/uv/guides/package/).

## Publish a future verified candidate manually

1. Complete the [release checks](release.md), using a new version.
2. Open the repository's **Releases**, create the matching prerelease and attach
   the verified wheel and sdist. Record the candidate commit and file hashes.
3. Update `publish.yml` to that version, commit and hashes; commit and push to
   `main`. Keep the existing `pypi` environment and trusted publisher.
4. Open **Actions → Publish RC to PyPI → Run workflow**, select `main` and run.
5. Open the completed run. Both validation and publication must succeed. Check
   the new version and file hashes on PyPI, then install it in a fresh environment.

## Run and inspect publication through commands

After preparing the new verified candidate and updating the workflow:

```sh
gh workflow run publish.yml --repo wa-pis/iddqueue --ref main
gh run list --repo wa-pis/iddqueue --workflow publish.yml --limit 5
# Replace RUN_ID with the run just dispatched.
gh run watch RUN_ID --repo wa-pis/iddqueue --exit-status
```

Use the new version in the final clean-install check:

```sh
uv venv /tmp/iddqueue-release-check
uv pip install --python /tmp/iddqueue-release-check/bin/python \
  "iddqueue[binary]==NEW_VERSION"
/tmp/iddqueue-release-check/bin/iddqueue --version
```

`RUN_ID` and `NEW_VERSION` are placeholders, not literal arguments. Publication
needs the maintainer's authorization; preparing documentation does not publish
a new version.
