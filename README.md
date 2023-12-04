# PrimAITE

![image](./PrimAITE_logo_transparent.png)

The ARCD Primary-level AI Training Environment (**PrimAITE**) provides an effective simulation capability for the purposes of training and evaluating AI in a cyber-defensive role. It incorporates the functionality required of a primary-level ARCD environment, which includes:

- The ability to model a relevant platform / system context;

- The ability to model key characteristics of a platform / system by representing connections, IP addresses, ports, traffic loading, operating systems and services;

- Operates at machine-speed to enable fast training cycles.

PrimAITE presents the following features:

- Highly configurable (via YAML files) to provide the means to model a variety of platform / system laydowns and adversarial attack scenarios;

- A Reinforcement Learning (RL) reward function based on (a) the ability to counter the specific modelled adversarial cyber-attack, and (b) the ability to ensure success;

- Provision of logging to support AI evaluation and metrics gathering;

- Realistic network traffic simulation, including address and sending packets via internet protocols like TCP, UDP, ICMP, and others

- Routers with traffic routing and firewall capabilities

- Support for multiple agents, each having their own customisable observation space, action space, and reward function definition, and either deterministic or RL-directed behaviour

## Getting Started with PrimAITE

### 💫 Install & Run
**PrimAITE** is designed to be OS-agnostic, and thus should work on most variations/distros of Linux, Windows, and MacOS.
Currently, the PrimAITE wheel can only be installed from GitHub. This may change in the future with release to PyPi.

#### Windows (PowerShell)

**Prerequisites:**
* Manual install of Python >= 3.8 < 3.11

**Install:**

``` powershell
mkdir ~\primaite
cd ~\primaite
python3 -m venv .venv
attrib +h .venv /s /d # Hides the .venv directory
.\.venv\Scripts\activate
pip install https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/releases/download/v2.0.0/primaite-2.0.0-py3-none-any.whl
primaite setup
```

**Run:**

``` bash
primaite session
```

#### Unix

**Prerequisites:**
* Manual install of Python >= 3.8 < 3.11

``` bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.10
sudo apt-get install python3-pip
sudo apt-get install python3-venv
```
**Install:**

``` bash
mkdir ~/primaite
cd ~/primaite
python3 -m venv .venv
source .venv/bin/activate
pip install https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/releases/download/v2.0.0/primaite-2.0.0-py3-none-any.whl
primaite setup
```

**Run:**

``` bash
primaite session
```


### Developer Install from Source
To make your own changes to PrimAITE, perform the install from source (developer install)

#### 1. Clone the PrimAITE repository
``` unix
git clone git@github.com:Autonomous-Resilient-Cyber-Defence/PrimAITE.git
```

#### 2. CD into the repo directory
``` unix
cd PrimAITE
```
#### 3. Create a new python virtual environment (venv)

```unix
python3 -m venv venv
```

#### 4. Activate the venv

##### Unix
```bash
source venv/bin/activate
```

##### Windows (Powershell)
```powershell
.\venv\Scripts\activate
```

#### 5. Install `primaite` with the dev extra into the venv along with all of it's dependencies

```bash
python3 -m pip install -e .[dev]
```

#### 6. Perform the PrimAITE setup:

```bash
primaite setup
```

## 📚 Building documentation
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
