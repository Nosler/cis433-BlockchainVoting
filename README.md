# cis433-BlockchainVoting
Final Project for CIS 433

## Authors

Sam champer <br/> Andrea Nosler

## Installation

This project uses pipenv to create an environment.

To install pipenv, you must have python installed. This project uses Python 3.7.2.
Get it at: https://www.python.org/downloads/

After installing python-pip install pipenv by running:<br/>
```pip install pipenv```

Then instal project dependencies with:<br/>
```pipenv install```

## Available commands:

Start a vote server:<br/>
```pipenv run server```<br/>

Default port is 5000. To run on different port, such as 1234, use :<br/>
```pipenv run server -p 1234```<br/>

Run unit tests for the blockchain and cryptography functions:<br/>
```pipenv run python -m unittest```

## Usage
#### How to actually hold a vote using this system:
1. After installing, setup a node to mine as many votes as you'll need, 
and build the initial blockchain. Do this by running ``initialize``. This has optional arguments:
``-p`` to specify a port (default 5000), ``-n to specify number of votes (default 10),
and -vpp to specify the number of votes per person (default 1). For example, to start an
election with 20 people, run the startup server on port 4999, and have one votes per person, run the following command:<br/>
```pipenv run initialize -p 4999 -n 20 -vpp 1```
2. After the miner has finished generating the keys and mining the votes, a standard vote manager
node can be started and import the chain from the miner. To do so use 
