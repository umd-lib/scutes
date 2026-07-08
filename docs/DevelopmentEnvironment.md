# Development Environment

## Introduction

This document provides guidance on setting up a Scutes development environment
on a local workstation.

## Prerequisites

* Python 3.14

* Install `libxmlsec1`. This is required for SAML authentication using
  [djangosaml2].

  On macOS, it is available via Homebrew:

  ```zsh
  brew install xmlsec1
  ```

  On Debian or Ubuntu Linux, it is available via `apt`:

  ```zsh
  sudo apt-get install xmlsec1
  ```

* Update the `/etc/hosts` file to add:

  ```zsh
  127.0.0.1 scutes-local
  ```

* Scutes uses UMD SSO with Grouper for authorization.

  You must be a member of either the `Scutes-Administrator` or `Scutes-User`
  Grouper group to log in, even when running in the local development
  environment.

## Application Setup

1) Clone Scutes from GitHub:

    ```zsh
    git clone git@github.com:umd-lib/scutes
    cd scutes
    ```

2) Set up the Python virtual environment, and install the dependencies

    ```zsh
    python -m venv --prompt "scutes-py$(cat .python-version)" .venv
    source .venv/bin/activate
    pip install -e .
    ```

3) Download the `scutes-test-lib-umd-edu-sp.key` and
  `scutes-test-lib-umd-edu-sp.crt` files from the  "scutes-local-saml" entry in
   LastPass into the "scutes" project root directory.

    ℹ️ Note: These files can be placed in a directory outside the project,
    if desired. Also, when downloading the `scutes-test-lib-umd-edu-sp.crt`
    file, Google Chrome will modify the file extension, by default, to ".cer".
    Be sure to specify the ".crt" extension when downloading the file.
    Mozilla Firefox preserves the ".crt" extension.

4) Copy the `src/.env-dev-example` file to `src/.env`:

    ```zsh
    cp src/.env-dev-example src/.env
    ```

    and update the following variables with the appropriate values as needed.

    Relative directories (where used) are resolved from the directory where the
    `manage.py` script is run. The following examples assume `manage.py` is run
    from the project root as `src/manage.py` (so relative paths are relative to
    the project root):

    * `KEY_FILE` - relative (or absolute) file path to the
      `scutes-test-lib-umd-edu-sp.key` file

      Default in example file assumes key is in the project root:
      `'scutes-test-lib-umd-edu-sp.key'`

    * `CERT_FILE` - relative (or absolute) file path to the
      `scutes-test-lib-umd-edu-sp.crt` file

      Default in example file assumes cert is in the project root:
      `'scutes-test-lib-umd-edu-sp.crt'`

    * `MEDIA_ROOT` - relative (or absolute) file path to where user-uploaded
      files are saved.

      Default in example file is `'src/media/'`

    * `SECRET_KEY` - An (insecure) key is provided by default, which should
      **not** be used for production systems. For production, a source of
      sufficient randomness, such as `uuidgen | shasum -a 256 | cut -c-64`
      should be used to generate the key.

    * `WHITENOISE_ROOT` - relative (or absolute) file path to directory
      containing static files served by the "WhiteNoise" server

      Default in example file is `'src/static/'`

    * `XMLSEC1_PATH` - The full file path to the "xmlsec1" binary, (usually
      findable by running `which xmlsec1`).

      Default in example file assumes Homebrew install:
      `/opt/homebrew/bin/xmlsec1`

5) Initialize the database, using the `migrate` command:

    ```zsh
    src/manage.py migrate
    ```

6) Import Data

    Use either YAML test data or an .mbox file
    See Management Commands

7) Start the dev server

    ```zsh
    src/manage.py runserver
    ```

    The application will be running at <http://scutes-local:15000/>

    **Note:** Use ctrl+c to stop the server

    If the prompt is given back without stopping the server, you will need to
    kill the process:

    ```zsh
    lsof -t -i tcp:15000 | xargs kill -9
    ```

### Tests

To install test dependencies, install the `test` extra:

```zsh
pip install -e '.[test]'
```

This project uses [pytest] in conjunction with the [pytest-django] plugin
to run its tests. To run the test suite:

```zsh
pytest
```

To run with coverage information:

```zsh
pytest --cov src --cov-report term-missing
```

[djangosaml2]: https://djangosaml2.readthedocs.io/
[pytest]: https://pytest.org/
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/
