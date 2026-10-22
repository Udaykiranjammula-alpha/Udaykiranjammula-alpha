# Uday Kiran Jammula's GitHub profile

This public profile repository must be named exactly `Udaykiranjammula-alpha`, matching the account username. GitHub displays its root `README.md` at [Udaykiranjammula-alpha](https://github.com/Udaykiranjammula-alpha).

## Local generation

Python 3.11 or newer is sufficient; no packages need to be installed.

```bash
python scripts/fetch_contributions.py
python scripts/render_heatmap.py
```

The fetcher reads GitHub's public contribution SVG without a personal access token, validates its date/count data, and writes normalized data to `data/contributions.json`. The renderer reads only that JSON and writes `assets/contrib-heatmap.svg`.

If GitHub changes the response shape, returns no days, or rate-limits the request, fetching exits with an error and does not overwrite the last valid data file. Wait and retry, then update the parser only after inspecting the public response. A token is intentionally not required or stored by this project.

## GitHub Actions

`.github/workflows/update-contributions.yml` runs daily at 04:17 UTC and on **Run workflow** manual dispatch. GitHub may delay scheduled workflows.

In **Settings → Actions → General → Workflow permissions**, select **Read and write permissions** and save. The workflow scopes `contents: write` to itself, then commits only `data/contributions.json` and `assets/contrib-heatmap.svg` when their contents changed.

## Troubleshooting

- If the profile README is not shown, confirm the repository name and owner match `Udaykiranjammula-alpha` and the repository is public.
- If the heatmap is stale, use manual dispatch or run the commands above.
- The animation is progressive enhancement: viewers that disable animation still receive a readable static heatmap.
- The chart reflects only GitHub's public calendar response; it does not calculate or display unverified totals, streaks, followers, stars, or repository counts.
