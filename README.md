# cis433-BlockchainVoting
Final Project for CIS 433

## Authors

Sam champer
Andi Nosler

## Installation

This project uses pipenv to create an environment.

To install pipenv, you must have python installed. This project uses Python 3.7.2.
Get it at https://www.python.org/downloads/

After installing python install pipenv by running:
``pip install pipenv``

Then instal project dependencies with:
``pipenv install``

Then project commands can be executed with:
``pipenv run [command]``

## Usage
How to have an election using this system, from A-Z:
[Pending]

## Available commands:

Commands that are available right now include:
Start a server (with options to specify a port):
``pipenv run python voteserver.py``
``$ pipenv run python voteserver.py -p 5001``
``$ pipenv run python voteserver.py --port 5002``
Run a few temporary tests cryptography functions:
``pipenv run python cryptfuncs.py``
Run unit tests for the blockchain:
``pipenv run python -m unittest``
