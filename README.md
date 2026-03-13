# Fork Purpose
This fork was created to provide support for Python 3.13 and newer without having to publish binary wheels for each version. The repository and QuickJS version are identical to the original repository. Only the [setup.py](setup.py) and [pyproject.toml](pyproject.toml) files have been modified to use `zig cc` to compile the C extension. This means you should be able to install this package without needing a C compiler installed already. The `ziglang` package is installed from PyPI as a build dependency.

To install this package, run `pip install git+https://github.com/AlexStanglEmerson/quickjs`.

This fork will not be maintained. It's simply provided as a quick fix to continue using the `quickjs` package on Python 3.13 and newer.

# ~~Archived~~
This repository has been **archived** due to lack of maintenance.

[![CircleCI](https://circleci.com/gh/PetterS/quickjs.svg?style=svg)](https://circleci.com/gh/PetterS/quickjs) [![PyPI version fury.io](https://badge.fury.io/py/quickjs.svg)](https://pypi.python.org/pypi/quickjs/)

Just install with

	pip install quickjs

Binaries are provided for:
 - 1.19.2 and later: Python 3.7-3.10, 64-bit for Windows, macOS and GNU/Linux.
 - 1.18.0-1.19.1: None.
 - 1.5.1–1.17.0: Python 3.9, 64-bit for Windows.
 - 1.5.0 and earlier: Python 3.7, 64-bit for Windows.

# Usage

```python
from quickjs import Function

f = Function("f", """
    function adder(a, b) {
        return a + b;
    }
    
    function f(a, b) {
        return adder(a, b);
    }
    """)

assert f(1, 2) == 3
```

Simple types like int, floats and strings are converted directly. Other types (dicts, lists) are converted via JSON by the `Function` class.
The library is thread-safe if `Function` is used. If the `Context` class is used directly, it can only ever be accessed by the same thread.
This is true even if the accesses are not concurrent.

Both `Function` and `Context` expose `set_memory_limit` and `set_time_limit` functions that allow limits for code running in production.

## API
The `Function` class has, apart from being a callable, additional methods:
- `set_memory_limit`
- `set_time_limit`
- `set_max_stack_size`
- `memory` – returns a dict with information about memory usage.
- `add_callable` – adds a Python function and makes it callable from JS.
- `execute_pending_job` – executes a pending job (such as a async function or Promise).

## Documentation
For full functionality, please see `test_quickjs.py`

# Developing
This project uses a git submodule for the upstream code, so clone it with the `--recurse-submodules` option or run `git submodule update --init --recursive` afterwards.

Use a `poetry shell` and `make test` should work from inside its virtual environment.
