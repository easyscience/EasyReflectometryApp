# Development workflow

All development of `EasyReflectometryApp` happens on the `develop` branch of the git repository.
This branch holds the most up-to-date version of the application, which may include bugs; for production use, the [latest release](https://github.com/easyScience/EasyReflectometryApp/releases/latest) is advised.
Released versions are on the `master` branch.

Installation instructions for development are given in the [installation documentation](./INSTALLATION.md#development-installation).

## Related repositories

Many features need changes in more than one repository:

- [`reflectometry-lib`](https://github.com/easyscience/reflectometry-lib) (the `easyreflectometry` package): models, data loading, calculators and fitting.
- [`core`](https://github.com/easyscience/core) (the `easyscience` package): parameters, constraints and minimizers.
- [`gui-components`](https://github.com/easyscience/gui-components) (the `EasyApplication` package): shared QML components and styling.

The app depends on the `develop` branch of `reflectometry-lib` (see `pyproject.toml`).
When a change spans repositories, install local checkouts of them in editable mode, and open a pull request in each repository.
Merge the library change first, so the app's CI, which installs the library from GitHub, can pass.

## Feature and bug-fix contributions

To contribute a feature or bug fix, fork the GitHub repository, clone your fork to your local machine and add the upstream repository:

```
git clone git@github.com:<your-github-username>/EasyReflectometryApp.git
cd EasyReflectometryApp
git remote add upstream https://github.com/easyScience/EasyReflectometryApp.git
```

Create a feature branch from the up-to-date `develop` branch:

```
git fetch upstream
git switch -c my-feature-branch upstream/develop
```

Before opening a pull request:

- Run the test suite, which CI also runs on Windows, macOS and Linux with Python 3.12 and 3.13:
  ```
  python -m pytest tests
  ```
- Add or update tests for the behaviour you changed.
- Check the code style with [ruff](https://docs.astral.sh/ruff/) (`pip install ruff`), configured in `pyproject.toml`:
  ```
  ruff check EasyReflectometryApp tests
  ```
- Add a line describing the change to the `Unreleased` section of [CHANGELOG.md](./CHANGELOG.md).
- Update the user documentation in `docs/` if the change is visible to users.

Then push the branch to your fork and open a pull request against `develop` of the upstream repository.
Every push also builds the installers; a branch's builds are attached to a draft prerelease named after the branch, so they can be tested before merging.

## Release workflow

Periodically, or after major new features, a stable release of `EasyReflectometryApp` is made:

1. On `develop`, bump the version and update the release information:
    - `version` in the `[project]` section of `pyproject.toml`;
    - `release_date` in the `[release]` section of `pyproject.toml` (shown on the app's Home page);
    - in [CHANGELOG.md](./CHANGELOG.md), rename the `Unreleased` section to `Version <version-number> (<date>)`.

    If the release needs a released version of `reflectometry-lib`, change its dependency in `pyproject.toml` from the `develop` branch to that version.
    Let CI build the installers for `develop` and test them.
2. Open a pull request from `develop` to `master`, and paste the CHANGELOG section of the release into its description.
3. Once the pull request is merged, CI builds the installers from `master` and uploads them to a draft prerelease tagged `v<version-number>` and titled `Version <version-number> (<build date>)`. The release description is taken from [RELEASE.md](./RELEASE.md).
4. Test the installers from the draft release.
5. Edit the draft release: add the CHANGELOG section of the release to its description, untick _Set as a pre-release_, and publish it.
6. Publish the documentation: the release's tag is created by CI, which does not trigger other workflows, so run the _Build Documentation and Push to gh-pages Branch_ workflow (`documentation-build.yml`) by hand (Actions tab, _Run workflow_) on the release tag `v<version-number>`. Check the published site at <https://easyscience.github.io/EasyReflectometryApp/>.
7. Start a new, empty `Unreleased` section in CHANGELOG.md on `develop`.
