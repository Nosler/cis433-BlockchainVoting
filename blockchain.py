# Authors: Sam Champer, Andi Nosler
# Adapted, modified, and extended from code by Daniel van Flymen: https://github.com/dvf/blockchain

import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests
import cryptfuncs


def log(*args, **kwargs):
    logging = True
    if logging:
        print("LOG:: ", end="")
        print(*args, **kwargs)


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
        self.total_value = 0
        self.wallets = dict()

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
        Toggles the chain as locked, preventing this node from accepting any
        chain that has a higher total value than what this node already has.
        """
        self.lock = True

    def update_wallets(self, transaction):
        amount = transaction['amount']
        sender = transaction['sender']
        receiver = transaction['recipient']
        if sender in self.wallets:
            self.wallets[sender] -= amount
        else:
            self.wallets[sender] = -amount
        if receiver in self.wallets:
            self.wallets[receiver] += amount
        else:
            self.wallets[receiver] = amount

    def valid_wallets(self, new_chain):
        """
        Reads a valid chain and creates a dictionary of wallets from the chain.
        The dictionary of wallets is then suitable for checking the total value,
        of the chain and verifying if attempted purchases/votes are legitimate
        (e.g. does the attempted transferer have the right to transfer the amount
        they are attempting to transfer).
        :return: F if blockchain is locked and the new chain is not acceptable
                        (has a value that is higher than the locked in value.
                        or if the attempted transferer lacks the transfer balance).
                 T if the blockchain is not locked; also updates self.wallets.
                 T if locked and new chain is acceptable, also updates wallets.
                 Also returns the new wallets if T and new total value.
        """
        new_wallet = dict()
        new_chain_value = 0
        for block in new_chain:
            for transaction in block['transactions']:
                amount = transaction['amount']
                sender = transaction['sender']
                receiver = transaction['recipient']
                if sender in new_wallet:
                    new_wallet[sender] -= amount
                else:
                    new_wallet[sender] = -amount
                if receiver in new_wallet:
                    new_wallet[receiver] += amount
                else:
                    new_wallet[receiver] = amount
                if sender == "0":
                    new_chain_value += amount

        for owner in new_wallet:
            if owner != "0" and new_wallet[owner] < 0:
                # Prevent tranferer from spending more than they have.
                return False, dict(), 0
            print("Owner: {} has net value: {}".format(owner, new_wallet[owner]))
        if self.lock and new_chain_value != self.total_value:
            # If the chain is locked, return false if the chain
            # under consideration has a higher net value.
            return False, dict(), 0
        print("NEW CHAIN VALUE: ", new_chain_value)
        print(self.lock)
        print(self.total_value)
        self.wallets = new_wallet
        self.total_value = new_chain_value
        return True, new_wallet, new_chain_value

    def balance_check(self, name):
        """
        Check the balance held by 'name'. Can be used to check if an individual has voted,
        or count how many votes a candidate has.
        :param name: The name to lookup.
        :return: Value held by that individual.
        """
        if name in self.wallets:
            return self.wallets[name]
        else:
            return 0

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid.
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        last_block = chain[0]
        for current_index in range(1, len(chain)):
            block = chain[current_index]
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False
            # Check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False
            last_block = block
        # Return true only if all transactions on the chain are valid:
        log("CHAIN HASHES ARE CORRECT. CHECKING FOR VALID TRANSACTIONS.")
        return self.chain_transactions_valid(chain)

    def resolve_conflicts(self):
        """
        Resolves conflicts by replacing our chain with the longest one in the network.
        :return: True if chain was replaced, False if not.
        """
        log("RESOLVING CONFCLICTS: ")
        neighbours = list(self.nodes)
        new_chain = None
        new_wallets = self.wallets
        new_chain_value = self.total_value
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
                    log("COMPARING CHAIN WITH LENGTH {}.".format(length))
                    # Check if the length is longer and the chain is valid
                    log("VERIFYING CHAIN IS VALID.")
                    if length > max_length and self.valid_chain(chain):
                        log("CHAIN IS VALID. CHECKING THAT TRANSACTIONS RESULT IN POSITIVE BALANCES.")
                        valid_wallets, new_wallets, new_chain_value = self.valid_wallets(chain)
                        # If all blocks have correct hashes, and all blocks have valid
                        # transactions, and the new chain leads to valid wallets.
                        if valid_wallets:
                            max_length = length
                            new_chain = chain
        # Replace this node's chain if a new, valid, longer chain is discovered:
        if new_chain:
            self.chain = new_chain
            self.wallets = new_wallets
            self.total_value = new_chain_value
            return True
        return False

    def chain_transactions_valid(self, chain):
        """
        Checks the validity of a the transactions in a chain.
        Make sure transaction is not redundant in its chain.
        Make sure transaction key is valid.
        :param chain: The chain to be checked.
        :return: True if valid, else false
        """
        for block in chain:
            log("CHECKING BLOCK FOR VALID VALID TRANSACTIONS.")
            for transaction in block['transactions']:
                if not self.valid_transaction(transaction, chain):
                    return False
        return True

    def valid_transaction(self, transaction, chain):
        """
        Checks the validity of a requested transaction by:
        Ensuring transfer amount is positive.
        Checking that the key used to request transaction is correct.
        :return: True if valid, else false
        """
        # Ensure that transaction is not redundant:
        log("CHECKING THAT TRANSACTION IS NOT A DUPLICATE.")
        if not self.non_redundant_transaction(transaction, chain):
            return False
        # Ensure transfer amount is positive.
        log("CHECKING THAT TRANSACTION IS POSITIVE.")
        amount = transaction['amount']
        if amount < 0:
            return False
        sender = transaction['sender']
        if sender == "0":
            # Original vote producer node.
            log("ORIGINAL MINER TRANSACTIONS ARE CHECKED LATER.")
            return True

        log("CHECKING THAT TRANSFER IS VALID.")
        # If not an original vote producer vote, then the vote is being
        # transferred, e.g. being cast.
        # Ensure that the vote number is the correct one for this vote:
        vote_number = transaction['vote_number']
        if len(chain) < vote_number:
            return False
        target_node_transactions = chain[vote_number]['transactions']
        if len(target_node_transactions) != 1:
            # The initial vote nodes only have one transaction per block.
            return False
        referenced_voter = target_node_transactions[0]['recipient']
        if sender != referenced_voter:
            return False

        log("SENDER. MATCHES VOTE OWNER. CHECKING KEY.")
        # We now know that someone is trying to cast a vote that is indeed available
        # to be cast. Now we need to verify the signature that the voter provided in
        # order to ascertain that the transaction is actually valid. The signature is
        # the phrase "NO COLLUSION" encrypted with a private RSA key that corresponds
        # to the public key in the 'sender' field.
        voter_private_key = cryptfuncs.import_key(transaction['signature'])
        # A voters signature is the private key that is assigned to their vote.
        # Once used, it is no longer usable. Thus, it doesn't matter that users
        # are publicizing their private key, something one wouldn't want to do
        # in most contexts.
        voter_public_key = cryptfuncs.import_key(sender)

        verification_message = "NO COLLUSION"
        signature = cryptfuncs.sign(verification_message, voter_private_key)
        verification = cryptfuncs.verify(verification_message, signature, voter_public_key)
        log("{}".format("VERIFICATION SUCCESS." if verification else "VERIFICATION FAILED."))
        return verification

    def get_transactor(self, vote_number):
        """
        When a person issues a vote, they upload their vote number and signature.
        To finish assembling the attempted transaction, fetch the recipient of
        the vote from the block at the index corresponding to the vote number.
        This recipient will be the sender of the vote that is being cast when
        this function is called.
        :vote_number: The number corresponding to the vote being cast.
        :return: The public key of the person voting now. False if failed.
        """
        log(vote_number, type(vote_number))
        if len(self.chain) < vote_number:
            return False
        target_node_transactions = self.chain[vote_number]['transactions']
        if len(target_node_transactions) != 1:
            # The initial vote nodes only have one transaction per block.
            return False
        return target_node_transactions[0]['recipient']

    @staticmethod
    def non_redundant_transaction(transaction, chain):
        """
        Check to make sure a transaction isn't already on the chain.
        :param transaction: a pending transaction.
        :param chain: a blockchain to search for the transaction.
        :return: True if not redundant, else false.
        """
        transaction_time = transaction['timestamp']
        sender = transaction['sender']
        recipient = transaction['recipient']
        log("CHECKING FOR REDUNDANT TRANSACTION WITH THESE PROPERTIES:")
        log("SENDER: {} RECIPIENT: {} TIME: {}".format(sender, recipient, transaction_time))
        transaction_seen = False
        for block in chain:
            if block['transactions']:
                for other_transaction in block['transactions']:
                    other_time = other_transaction['timestamp']
                    other_sender = other_transaction['sender']
                    other_recipient = other_transaction['recipient']
                    if transaction_time == other_time and sender == other_sender and recipient == other_recipient:
                        # If we've already seen this transaction, it is redundant. If not, mark it as seen.
                        if transaction_seen:
                            # Transaction is redundant.
                            log("TRANSACTION IS REDUNDANT")
                            return False
                        transaction_seen = True
        return True

    def valid_balance(self, transaction):
        """
        Checks to see if a sender has sufficient balance
        (a vote left to cast) in order to make a transaction.
        :param transaction: A transaction with a sender, reciever, and amount.
        :return: True if balance is sufficient, else false.
        """
        amount = transaction['amount']
        sender = transaction['sender']
        if sender == "0" and not self.lock:
            # "0" sender, is the original source, and is allowed
            log("CHAIN NOT LOCKED, NEW VOTE GENERATION PERMITTED.")
            return True
        if sender in self.wallets:
            log("SENDER FOUND IN WALLET.")
            log("CHECKING SENDER BALANCE.")
            if self.wallets[sender] >= amount:
                log("BALANCE SUFFICIENT.")
                return True
        log("{} DOES NOT HAVE A SUFFICIENT BALANCE OR DOES NOT EXIST.".format(sender))
        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new block in the blockchain.
        Make sure not to add transaction to a block that already exist on the blockchain.
        Make sure that a would be transferer has sufficient balance to make a transfer.
        Check that the key used to request each transaction is correct.
        :param proof: The proof given by the proof of work algorithm
        :param previous_hash: Hash of previous block
        :return: A new block
        """
        valid_transactions = []
        for transaction in self.current_transactions:
            # Ensure proper vote signature and sufficient balance.
            if self.valid_transaction(transaction, self.chain) and self.valid_balance(transaction):
                self.update_wallets(transaction)
                valid_transactions.append(transaction)
                log("TRANSACTION ADDED TO NEW BLOCK.")
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': valid_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        log("NEW BLOCK ADDED TO CHAIN.")
        return block

    def new_transaction(self, sender, recipient, amount, signature=None, vote_number=0):
        """
        Creates a new transaction to go into the next mined block.
        Check the signature of attempted transferers.
        :param sender: Address of the sender
        :param recipient: Address of the recipient
        :param amount: Amount of transfer
        :param signature: A signature authorizing a transfer.
        :param vote_number: The vote block corresponding with the signature.
        :return: The index of the block that will hold this transaction.
        """
        new_t = {
            'sender': sender,
            'recipient': recipient,
            'timestamp': time(),
            'amount': amount,
            'signature': signature,
            'vote_number': vote_number
        }
        self.current_transactions.append(new_t)
        return new_t

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
        NOTE: For a blockchain used to store votes in an election, we don't care
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
