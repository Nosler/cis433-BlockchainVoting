# Authors: Sam Champer, Andi Nosler
# Partially uses some code from Daniel van Flymen (https://github.com/dvf/blockchain)
# along with additional code by the authors to implement the specific needs of a blockchain enabled election.

# This node is the only type of node that ever "mines" in an election. This node will
# mine as many blocks as we want votes, and then be destroyed by a primary voting server.

from os import path
from flask import Flask, jsonify, request
from argparse import ArgumentParser
from blockchain import Blockchain
from cryptfuncs import *

# Instantiate the app in flask:
app = Flask(__name__)

# Instantiate the blockchain.
blockchain = Blockchain()


@app.route('/chain/', methods=['GET'])
def send_chain_and_terminate():
    """
    App route to call to send the chain to another node and then terminate this miner.
    """
    # Send the newly mined chain, along with the length of the chain.
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    print("\n  ***Block chain has been disseminated. Initialization server has completed its work. Shutting down.***\n")
    terminate_function = request.environ.get('werkzeug.server.shutdown')
    # The terminate function will be called as well as the miner returning the jsonified response.
    terminate_function()
    return jsonify(response), 200


@app.route('/nodes/', methods=['GET'])
def no_other_nodes():
    """
    Since this miner node has no peers, send back nothing.
    """
    return jsonify(dict()), 204


def mine_votes(votes_per_participant):
    """
    The app route to add a new coin/vote to the block.
    """
    public, private = new_rsa(1024)

    # Run the proof of work algorithm to get the next proof:
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Associate the vote with the public key of the voter.
    # The sender is "0" to signify that this is a newly mined coin, not a transfer.
    blockchain.new_transaction(
        sender="0",
        recipient=public.export_key().decode(),
        amount=votes_per_participant
    )
    # Adding the new block to the chain:
    previous_hash = blockchain.hash(last_block)
    blockchain.new_block(proof, previous_hash)

    verification_message = "NO COLLUSION"
    signature = sign(verification_message, private)

    script_path = path.dirname(path.abspath(__file__))
    relative_path = "secret_keys\\key_{}.vote".format(i+1)
    final_path = path.join(script_path, relative_path)
    with open(final_path, 'wb') as f:
        f.write(signature)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=4999, type=int, help='port to listen on')
    parser.add_argument('-n', '--numvotes', default=10, type=int,
                        help='The number of votes generated for use in the election.')
    parser.add_argument('-vpp', '--votes_per_person', default=1, type=int,
                        help='For elections where individuals can cast multiple votes.')
    args = parser.parse_args()
    port = args.port
    num_votes = args.numvotes
    votes_per_person = args.votes_per_person
    print()
    for i in range(num_votes):
        print("   Generating unique key pair for voter number: {}".format(i + 1))
        mine_votes(votes_per_person)

    # Initialize the app on the desired port:
    app.run(host='0.0.0.0', port=port)
