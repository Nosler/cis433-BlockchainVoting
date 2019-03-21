# cis433-BlockchainVoting
Final Project for CIS 433


## Authors

Sam champer <br/> Andrea Nosler

## Installation

This project uses pipenv to create an environment.

To install pipenv, you must have python installed. This project uses Python 3.7.2.
Get it at: https://www.python.org/downloads/

After installing python-pip install pipenv by running:<br/>
```
pip install pipenv
```

Then instal project dependencies with:
```
pipenv install
```
This project also uses ngrok to give your server a public URL.
Get it at: https://ngrok.com/ and place your ngrok file in the project root directory.

## Usage
#### How to actually hold a vote using this system:
* 1: After installing, setup a node to mine as many votes as you'll need,
and build the initial blockchain. Do this by running ``init``. This has optional arguments:<br>
``-p`` to specify a port (default 4999) <br>``-n`` to specify number of votes (default 10)<br>
For example, to start an election with 20 people, run the startup server on port 7777,
and have one votes per person, run the following command:
```
pipenv run init -p 7777 -n 20
```
* 2: After the miner has finished generating the keys and mining the votes, a standard vote manager node can
be started and import the chain from the miner. To do so, *while the miner is still running,* use a separate terminal
to run ``node``. This command has optional arguments: <br>
``-p`` to specify a port (default 5000) <br>
``-src`` to specify an IP address of a server with the current blockchain (default http://127.0.0.1:4999) <br>
For example, to spool up a new vote manager node to take the blockchain generated by ``init`` above, run:
```
pipenv run node -p 5001 -src http://127.0.0.1:7777
```
* 3: Now, a server has been initialized and can accept votes. However, for people to vote, they must be given a vote.
Voting requires each voter to attach a message signed with a private RSA key. The signed messages have been generated
in advance and deposited in the ``/secret_keys`` folder. One must be sent to each voter See:
https://github.com/Nosler/cis433-BlockchainVoting/blob/master/secret_keys/secret_key_info.md

* 4:

* TLDR: Run ``pipenv install`` then specify the number of votes like ``pipenv run init -n 30``
and simultaneously ``pipenv run node`` then send all the people who get to vote a secret key
from the ``/secret_keys`` folder and have them all visit:
``http://your.ip.address.or.wherever.you.hosted.this:5000`` to vote.

## List of commands:

Server that mines inital votes:<br/>
```
pipenv run init <-p port_number> <-n number_of_votes> <-vpp votes_per_person> <-h help>
```
Server that operates as a node during an election:
```
pipenv run node <-p port_number> <-s source_ip> <-h help>
```
Give your locally hosted server a URL on the internet:
```
./ngrok https <Port#>
```
Run unit tests for the blockchain and cryptography functions:
```
pipenv run python -m unittest
```
<br>
