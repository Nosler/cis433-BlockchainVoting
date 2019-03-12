# Authors: Sam Champer, Andi Nosler
# Partially uses some code from Daniel van Flymen (https://github.com/dvf/blockchain)
# along with additional code by the authors to implement the specific needs of a blockchain enabled election. 

from os import path
from flask import Flask, jsonify, request
from argparse import ArgumentParser
from blockchain import Blockchain
from cryptfuncs import *

# Instantiate the app in flask:
app = Flask(__name__)

# Instantiate the blockchain. This node is the only node that ever mines.
# This node will mine as many blocks as we want votes, and then be destroyed by primary voting server.
blockchain = Blockchain()

# Vote

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Appp route for conducting a transfer of a coin (e.g. for voting for a recipient).
    """
    values = request.get_json(force=True)
    # Check that the required fields are in the POST:
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new transaction on the blockchain:
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    """
    App route to call for a display of the entire chain.
    """
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register a list of new nodes that share the blockchain.
    """
    values = request.get_json(force=True)
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """
    Call function to resolve conflicts between this node and other nodes.
    """
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


def mine_votes(num_votes, votes_per_person):
    """
    The app route to add a new coin/vote to the block.
    """
    for i in range(num_votes):
        print("Generating unique key pair for voter number: {}".format(i + 1))
        public, private = new_rsa(1024)

        # Run the proof of work algorithm to get the next proof:
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block)

        # Associate the vote with the public key of the voter.
        # The sender is "0" to signify that this is a newly mined coin, not a transfer.
        blockchain.new_transaction(
            sender = "0",
            recipient = public.export_key().decode(),
            amount = votes_per_person
        )
        # Forge the new block by adding it to the chain:
        previous_hash = blockchain.hash(last_block)
        blockchain.new_block(proof, previous_hash)

        verification_message = "NO COLLUSION"
        signature = sign(verification_message, private)

        script_path = path.dirname(path.abspath(__file__))
        relative_path = "secret_keys\key_{}.vote".format(i+1)
        final_path = path.join(script_path, relative_path)
        with open(final_path, 'wb') as f:
            f.write(signature)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-n', '--numvotes', default=10, type=int,
                        help='The number of votes generated for use in the election.')
    parser.add_argument('-vpp', '--votes_per_person', default=1, type=int,
                        help='For elections where individuals can cast multiple votes.')
    args = parser.parse_args()
    port = args.port
    num_votes = args.numvotes
    votes_per_person = args.votes_per_person
    mine_votes(num_votes, votes_per_person)

    print(blockchain.chain)
    # Initialize the app on the desired port:
    app.run(host='0.0.0.0', port=port)
