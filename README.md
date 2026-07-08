# Virality-on-Shorts

This repository uses **uv** for Python environment and dependency management.

## Prerequisites

Make sure you have **Python 3.11+** (or the version required by the project) and **uv** installed.

To install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the installation:

```bash
uv --version
```

---

## Project Setup

Clone the repository and move into the project directory:

```bash
git clone <repository-url>
cd Virality-on-Shorts
```

Create the virtual environment:

```bash
uv venv
```

This creates a virtual environment in the `.venv/` directory.

---

## Activate the Environment

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

Once activated, your terminal prompt should begin with:

```text
(.venv)
```

---

## Install Dependencies

Install all project dependencies:

```bash
uv sync
```

If a `uv.lock` file is present, `uv` installs the exact dependency versions specified in the lock file, ensuring a reproducible environment.



## Adding New Dependencies

To add a package to the project:

```bash
uv add package-name
```

Example:

```bash
uv add pandas
```

This updates the project configuration and installs the package automatically.

---

## Updating the Environment

Whenever `pyproject.toml` or `uv.lock` changes, synchronize your environment with:

```bash
uv sync
```

---

## Deactivating the Environment

When you finish working:

```bash
deactivate
```

---

## Project Structure

```text
Virality-on-Shorts/
├── .venv/              # Virtual environment (local)
├── pyproject.toml      # Project configuration
├── uv.lock             # Locked dependency versions (if present)
├── README.md
└── ...
```

---

## Notes

* Do **not** commit the `.venv/` directory to Git.
* Commit `pyproject.toml` and `uv.lock` so everyone working on the project gets the same environment.
* After pulling new changes from the repository, run:

```bash
uv sync
```

to ensure your local environment matches the project's dependencies.

