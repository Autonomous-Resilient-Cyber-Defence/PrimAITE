# PrimAITE

## Getting Started with PrimAITE


### Pre-Requisites

In order to get **PrimAITE** installed, you will need to have the following installed:

- `python3.8+`
- `python3-pip`
- `virtualenv`

**PrimAITE** is designed to be OS-agnostic, and thus should work on most variations/distros of Linux, Windows, and MacOS.

### Installation from source (Developer Install)
#### 1. Create a new python virtual environment (venv)

```unix
python3 -m venv venv
```

#### 2. Activate the venv

##### Unix
```bash
source venv/bin/activate
```

##### Windows (Powershell)
```powershell
.\venv\Scripts\activate
```

#### 3. Install `primaite` with the dev extra into the venv along with all of it's dependencies

```bash
python3 -m pip install -e .[dev]
```

#### 4. Perform the PrimAITE setup:

```bash
primaite setup
```

## Building documentation
The PrimAITE documentation can be built with the following commands:

##### Unix
```bash
cd docs
make html
```

##### Windows (Powershell)
```powershell
cd docs
.\make.bat html
```

This will build the documentation as a collection of HTML files which uses the Read The Docs sphinx theme. Other build
options are available but may require additional dependencies such as LaTeX and PDF. Please refer to the Sphinx documentation
for your specific output requirements.
