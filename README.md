# Asynchronous Python client for the Tado API

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code Coverage][codecov-shield]][codecov]
[![Documentation][docs-shield]][docs]
[![Quality Gate Status][sonarcloud-shield]][sonarcloud]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

Asynchronous Python client to control Tado devices.

## About

This package allows you to control Tado devices from within Python.
Although it can be used as a standalone package, it is current scope is to be used within Home Assistant.
Not all endpoints and features are fully supported.
This is the continuation project of PyTado.

## Documentation

Full documentation is available at [GitHub Pages][docs].

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

## Usage

As of the 15th of March 2025, Tado has updated their OAuth2 authentication flow. It will now use the device flow, instead of a username/password flow. This means that the user will have to authenticate the device using a browser, and then enter the code that is displayed on the browser into the terminal.

PyTado handles this as following:

1. The `_login_device_flow()` will be invoked at the initialization of a PyTado object. This will start the device flow and will return a URL and a code that the user will have to enter in the browser. The URL can be obtained via the method `device_verification_url()`. Or, when in debug mode, the URL will be printed. Alternatively, you can use the `device_activation_status()` method to check if the device has been activated. It returns three statuses: `NOT_STARTED`, `PENDING`, and `COMPLETED`. Wait to invoke the `device_activation()` method until the status is `PENDING`.

2. Once the URL is obtained, the user will have to enter the code that is displayed on the browser into the terminal. By default, the URL has the `user_code` attached, for the ease of going trough the flow. At this point, run the method `device_activation()`. It will poll every five seconds to see if the flow has been completed. If the flow has been completed, the method will return a token that will be used for all further requests. It will timeout after five minutes.

3. Once the token has been obtained, the user can use the PyTado object to interact with the Tado API. The token will be stored in the `Tado` object, and will be used for all further requests. The token will be refreshed automatically when it expires.
The `device_verification_url()` will be reset to `None` and the `device_activation_status()` will return `COMPLETED`.

### Screenshots of the device flow

![Tado device flow: invoking](/screenshots/tado-device-flow-0.png)
![Tado device flow: browser](/screenshots/tado-device-flow-1.png)
![Tado device flow: complete](/screenshots/tado-device-flow-2.png)

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

This Python project is fully managed using the [uv][uv] dependency manager. But also relies on the use of NodeJS for certain checks during development.

You need at least:

- Python 3.12+
- [uv][uv-install]
- NodeJS 18+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
uv install
```

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
uv run prek run --all-files
```

To run just the Python tests:

```bash
uv run pytest
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
[docs]: https://erwindouna.github.io/python-tado/
[docs-shield]: https://github.com/erwindouna/python-tado/actions/workflows/deploy-docs.yaml/badge.svg
[erwindouna]: https://github.com/erwindouna
[github-sponsors-shield]: https://erwindouna.dev/wp-content/uploads/2019/12/github_sponsor.png
[github-sponsors]: https://github.com/sponsors/erwindouna
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/erwindouna/python-tado.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[uv-install]: https://docs.astral.sh/uv/getting-started/installation/
[uv]: https://docs.astral.sh/uv/
[pre-commit]: https://pre-commit.com/
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/tadoasync/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/tado
[releases-shield]: https://img.shields.io/github/release/erwindouna/python-tado.svg
[releases]: https://github.com/erwindouna/python-tado/releases
[semver]: http://semver.org/spec/v2.0.0.html
[sonarcloud-shield]: https://sonarcloud.io/api/project_badges/measure?project=erwindouna_python-tado&metric=alert_status
[sonarcloud]: https://sonarcloud.io/summary/new_code?id=erwindouna_python-tado
