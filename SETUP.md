# Tim-1e Profile README Setup

This folder is intended to become the GitHub profile repository:

```text
Tim-1e/Tim-1e
```

## Required Repository Settings

1. Create a GitHub repository named exactly `Tim-1e`.
2. Upload this folder's contents into that repository.
3. Open `Settings -> Actions -> General`.
4. Under `Workflow permissions`, choose `Read and write permissions`.
5. Run `GitHub Profile 3D Contrib` once from the Actions tab.

## Tokens

- No custom token is required for the current public-profile version.
- The workflow uses GitHub's built-in `GITHUB_TOKEN`.
- If you later want private contribution data or more advanced GraphQL-based reports, add a personal access token as a repository secret and update the workflow.

## Expected Generated File

The README references:

```text
profile-3d-contrib/profile-season-animate.svg
```

The current file is a placeholder. It will be replaced by real output after the first successful workflow run.
