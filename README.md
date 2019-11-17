# Nayra 2.0


# Installation
## Requirements
pocketsphinx requirements
```bash
sudo apt-get install -y python python-dev python-pip build-essential swig git libpulse-dev
```
extra pocketsphinx requirement
```bash
sudo apt-get install libasound2-dev
```

pyaudio requirement
```bash
sudo apt-get install portaudio19-dev
```

pyttsx requirement
```bash
sudo apt install espeak
sudo apt install libgirepository1.0-dev
```

## Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -r requirements
```

## Database
```bash
flask db upgrade
python3 nayra_setup.py
```

## Uplod folders
```bash
mkdir files
mkdir files/programs
mkdir files/audios
```

# Updating requirements
```bash
pip freeze -l | grep -v pkg-resources > requirements.txt
```
