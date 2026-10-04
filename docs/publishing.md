# PyPI Trusted Publishing

The public GitHub prerelease is available at
[v0.13.0rc1](https://github.com/wa-pis/iddqueue/releases/tag/v0.13.0rc1).
The manual [publish workflow](../.github/workflows/publish.yml) uploads those
exact wheel/sdist files, after checking the recorded candidate SHA and fixed
SHA256 hashes. It does not rebuild the candidate or need a stored API token.

For the first PyPI upload, sign into [PyPI Publishing](https://pypi.org/manage/account/publishing/)
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

After registration, run **Publish RC to PyPI** on `main`, or:

```sh
gh workflow run publish.yml --repo wa-pis/iddqueue --ref main
```

Check actual job success, PyPI version `0.13.0rc1` and both file SHA256 values,
then install `iddqueue[binary]==0.13.0rc1` in a clean environment. Do not treat
workflow preparation or a queued job as successful publication. Do not paste
API tokens into issues or chat. This workflow is scoped to this exact first RC;
a future version needs its own verified candidate and hashes.

References: [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[uv publishing](https://docs.astral.sh/uv/guides/package/).
