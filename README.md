# Welcome to Microblog!

This is an example application featured in my [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). See the tutorial for instructions on how to work with it.

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
