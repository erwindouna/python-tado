# Asynchronous Python client for the Tado API

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code Coverage][codecov-shield]][codecov]
[![Quality Gate Status][sonarcloud-shield]][sonarcloud]
[![Documentation Status][readthedocs-shield]][readthedocs]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

Asynchronous Python client to control Tado devices.

## About

This package allows you to control Tado devices from within Python.
Although it can be used as a standalone package, it is current scope is to be used within Home Assistant.
Not all endpoints and features are fully supported.

## Documentation
A full documentation can be found at [Read the Docs][readthedocs].

## Installation

```bash
pip install tadoasync
```

## Usage

```python
import asyncio

from tadoasync import Tado


async def main() -> None:
    """Example on how to retrieve all devices."""
    async with Tado("username", "password") as tado:
        await tado.get_devices()


if __name__ == "__main__":
    asyncio.run(main())

```

Keep in mind that if you use `async with`, the `aenter` and `aexit` methods are called automatically. It's recommended you use session control, if you don't use `async with`, you need to call `tado.close()` to close the session.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality. The format of the log is based on
[Keep a Changelog][keepchangelog].

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](.github/CONTRIBUTING.md).

Thank you for being involved!

## Setting up a development environment

The easiest way to start, is by opening a CodeSpace here on GitHub, or by using
the [Dev Container][devcontainer] feature of Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

This Python project is fully managed using the [Poetry][poetry] dependency manager. But also relies on the use of NodeJS for certain checks during development.

You need at least:

- Python 3.12+
- [Poetry][poetry-install]
- NodeJS 18+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
poetry install
```

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

## Authors & contributors

The original setup of this repository is by [Erwin Douna][erwindouna].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2024 Erwin Douna

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[build-shield]: https://github.com/erwindouna/python-tado/actions/workflows/tests.yaml/badge.svg
[build]: https://github.com/erwindouna/python-tado/actions/workflows/tests.yaml
[codecov-shield]: https://codecov.io/gh/erwindouna/python-tado/branch/main/graph/badge.svg
[codecov]: https://codecov.io/gh/erwindouna/python-tado
[contributors]: https://github.com/erwindouna/python-tado/graphs/contributors
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/erwindouna/python-tado
[erwindouna]: https://github.com/erwindouna
[github-sponsors-shield]: https://erwindouna.dev/wp-content/uploads/2019/12/github_sponsor.png
[github-sponsors]: https://github.com/sponsors/erwindouna
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/erwindouna/python-tado.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com/
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/tadoasync/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/tado
[releases-shield]: https://img.shields.io/github/release/erwindouna/python-tado.svg
[releases]: https://github.com/erwindouna/python-tado/releases
[semver]: http://semver.org/spec/v2.0.0.html
[sonarcloud-shield]: https://sonarcloud.io/api/project_badges/measure?project=erwindouna_python-tado&metric=alert_status
[sonarcloud]: https://sonarcloud.io/summary/new_code?id=erwindouna_python-tado
[readthedocs-shield]: https://readthedocs.org/projects/python-tado/badge/?version=latest
[readthedocs]: https://python-tado.readthedocs.io/en/latest/index.html
