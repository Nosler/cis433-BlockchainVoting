# Authors: Sam Champer, Andi Nosler
# Adapted, modified, and extended from code by Daniel van Flymen: https://github.com/dvf/blockchain

import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests


class Blockchain:
    def __init__(self):
        """
        Constructor. Create a new blockchain with a genesis block.
        """
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.new_block(proof=100, previous_hash=1)
        self.lock = False

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address to be added. Eg. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def remove_node(self, address):
        """
        Remove a node from the list of connected nodes.
        Might be useful for pruning deactivated servers from the list.
        :param address: Address to be removed.
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.discard(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.discard(parsed_url.path)
        else:
            self.nodes.discard(address)

    def value_lock(self):
        """
        Toggles the chain as locked, preventing this node from excepting any chain that has a higher total
        value than what this node already has.
        """
        self.lock = True

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        for current_index in range(1, len(chain)):
            block = chain[current_index]
            # print(f'{last_block}')
            # print(f'{block}')
            # print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False
            # Check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False
            last_block = block
        return True

    def resolve_conflicts(self):
        """
        Resolves conflicts by replacing our chain with the longest one in the network.
        :return: True if chain was replaced, False if not.
        """
        neighbours = list(self.nodes)
        new_chain = None
        # Only looking for longer chains:
        max_length = len(self.chain)
        # Grab and verify the chains from all the nodes in the network
        for node in neighbours:
            response = None
            for i in range(5):
                try:
                    response = requests.get(f'http://{node}/chain')
                    if response:
                        break
                except:
                    if i == 4:
                        # Remove unresponsive nodes.
                        self.nodes.discard(node)
                    continue
            if response:
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
        # Replace this node's chain if a new, valid, longer chain is discovered:
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new block in the blockchain
        :param proof: The proof given by the proof of work algorithm
        :param previous_hash: Hash of previous block
        :return: A new block
        """
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined block
        :param sender: Address of the sender
        :param recipient: Address of the recipient
        :param amount: Amount of transfer
        :return: The index of the block that will hold this transaction.
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'timestamp': time(),
            'amount': amount
        })
        # Return the index of the next block (which this transaction will be appended to) for output purposes.
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a block
        :param block: The block to be hashed.
        """
        # Must make sure that the dictionary is ordered, or hashes will be inconsistent.
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple proof of work algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
        For a blockchain used to store votes in an election, we don't care
        very much about proof of work at all. Indeed, it might be optimal to
        completely remove proof of work for non-currency blockchain applications.
        However, this function is kept here for now.
        :param last_block: <dict> last block
        :return: <int> proof of work.
        """
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates a proof of work
        :param last_proof: <int> Previous proof
        :param proof: <int> Current proof
        :param last_hash: <str> The hash of the previous block
        :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
