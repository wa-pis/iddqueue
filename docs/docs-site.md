# Documentation: edit, preview and publish

The site uses MkDocs, the built-in Read the Docs theme and search, matching
Agent Paranoid Android's documentation format. Source lives in `docs/`;
`mkdocs.yml` controls navigation. No docs framework is a runtime dependency.

## Edit manually

1. Open the relevant Markdown page in `docs/` in your editor.
2. Change text/examples; keep published version and behavior consistent with code.
3. For a new page, add it to the `nav` list in `mkdocs.yml`.
4. Preview locally, follow its links, and run the strict checks below.
5. Commit the change and push to `main`, or open a pull request. The Documentation
   workflow builds PRs; only `main` deploys the site.

## Local commands

```sh
git clone https://github.com/wa-pis/iddqueue.git
cd iddqueue
uv sync --locked --only-group docs --no-install-project
uv run --no-sync mkdocs serve
```

Open `http://127.0.0.1:8000/iddqueue/` (use the address printed by MkDocs).
Stop with Ctrl+C. Build without starting a server:

```sh
uv run --no-sync mkdocs build --strict
```

Output is `site/`. The full release gate additionally checks source links and
runtime/package behavior; see [contributing](https://github.com/wa-pis/iddqueue/blob/main/CONTRIBUTING.md).

## Enable GitHub Pages manually

Initial repository setup (already performed for this project):

1. Open `wa-pis/iddqueue` on GitHub.
2. Select **Settings → Pages**.
3. Under **Build and deployment**, choose **GitHub Actions** as the source.
4. Open **Actions → Documentation → Run workflow**, select `main`, and run it.
5. Wait for Build and Deploy to finish. The site is at
   `https://wa-pis.github.io/iddqueue/`.

The workflow uses the `github-pages` environment and GitHub's OIDC deployment,
without a personal access token. Normal pushes to `main` update the site.

## Equivalent commands

For initial setup, if Pages is not configured yet:

```sh
gh api --method POST repos/wa-pis/iddqueue/pages -f build_type=workflow
```

For an existing site whose source must be changed to Actions:

```sh
gh api --method PUT repos/wa-pis/iddqueue/pages -f build_type=workflow
```

Trigger and inspect deployment:

```sh
gh workflow run docs.yml --repo wa-pis/iddqueue --ref main
gh run list --repo wa-pis/iddqueue --workflow docs.yml
gh run watch RUN_ID --repo wa-pis/iddqueue --exit-status
curl --fail --location https://wa-pis.github.io/iddqueue/
```

Replace `RUN_ID` with the actual run returned by GitHub. A build passing alone
is not evidence that deployment succeeded: check Deploy and the public URL.

## If something fails

- **Broken links/nav/anchors:** run `mkdocs build --strict`, repair source links.
- **Pages 404:** verify the Pages source is GitHub Actions and Deploy succeeded.
- **Old content:** check the deployed run's commit and refresh the browser.
- **Permissions:** Build has read-only access; only Deploy gets `pages: write`
  and `id-token: write`. PRs do not deploy.

Historical upstream changelog remains an original RST file on GitHub. Current
how-to/reference pages are Markdown; Python examples stay executable source files.

Reference: [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
