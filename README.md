# PrimAITE

PrimAITE (Primary-level AI Training Environment) is a simulation environment for training AI under the ARCD programme.

The ARCD Primary-level AI Training Environment (PrimAITE) provides an effective simulation capability for the purposes of training and evaluating AI in a cyber-defensive role. It incorporates the functionality required of a primary-level ARCD environment, which includes: 

- The ability to model a relevant platform / system context; 

- The ability to model key characteristics of a platform / system by representing connections, IP addresses, ports, traffic loading, operating systems, services and processes; 

- Operates at machine-speed to enable fast training cycles.

PrimAITE presents the following features: 

- Highly configurable (via YAML files) to provide the means to model a variety of platform / system laydowns, mission profiles and adversarial attack scenarios; 

- A Reinforcement Learning (RL) reward function based on (a) the ability to counter the specific modelled adversarial cyber-attack, and (b) the ability to ensure mission success; 

- Provision of logging to support AI evaluation and metrics gathering; 

- Uses the concept of Information Exchange Requirements (IERs) to model background pattern of life, adversarial behaviour and mission data (on a sliding scale of criticality); 

- An Access Control List (ACL) function, mimicking the behaviour of a network firewall, is applied across the model, following standard ACL rule format (e.g. DENY/ALLOW, source IP address, destination IP address, protocol and port);  

- Application of IERs to the platform / system laydown adheres to the ACL ruleset; 

- Presents an OpenAI gym or RLLib interface to the environment, allowing integration with any OpenAI gym compliant defensive agents;  

- Full capture of discrete logs relating to agent training (full system state, agent actions taken, instantaneous and average reward for every step of every episode)​; 

- NetworkX provides laydown visualisation capability.  

## Getting Started with PrimAITE

### 💫 Install & Run
**PrimAITE** is designed to be OS-agnostic, and thus should work on most variations/distros of Linux, Windows, and MacOS.
Currently, the PRimAITE wheel can only be installed from GitHub. This may change in the future with release to PyPi.

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
