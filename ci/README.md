# CI helper

`release-workflow.yml` is the GitHub Actions workflow that builds
`AutoTyper.exe` on a Windows runner and attaches it to a GitHub Release.

It lives here rather than in `.github/workflows/` because the automation
account that created this branch does not hold the `workflows` permission and
GitHub therefore rejects pushes that add files under `.github/workflows/`.

## To enable it

```bash
mkdir -p .github/workflows
git mv ci/release-workflow.yml .github/workflows/release.yml
git commit -m "Enable release workflow"
git push
```

Then either push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

or run **Actions → Build and Release → Run workflow** and supply a tag.
The finished `AutoTyper.exe` is attached to the release automatically.
