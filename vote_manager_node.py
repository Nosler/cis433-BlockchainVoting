# Authors: Sam Champer, Andi Nosler
# Partially uses some code from Daniel van Flymen (https://github.com/dvf/blockchain)
# along with additional code by the authors to implement the specific needs of a blockchain enabled election.

from uuid import uuid4
from flask import Flask, jsonify, request, render_template
from argparse import ArgumentParser
from blockchain import Blockchain
import requests
from time import sleep
from werkzeug.contrib.fixers import ProxyFix
from urllib.parse import urlparse
import atexit


# Instantiate the blockchain node in flask:
app = Flask(__name__)

# Generate a globally unique address for this node:
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the blockchain for this node:
blockchain = Blockchain()


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/chain/', methods=['GET'])
def full_chain():
    """
    App route to call for a display of the entire chain.
    """
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/resolve/', methods=['GET'])
def consensus():
    """
    Call function to resolve conflicts between this node and other nodes.
    """
    replaced = blockchain.resolve_conflicts()

    # If, at some point in the past, there was a parallel operation that resulted in the node failing to respond
    # to another node's request, this node may have been incorrectly pruned from that node's list of active nodes.
    # To correct this, send a reciprocation request to all nodes that just responded by sending this node a chain.
    # This might add a tiny bit to server overhead, and it solves a parallelization problem that probably won't happen,
    # but it makes the system a tiny bit more robust:
    for node in blockchain.nodes:
        try:
            requests.post("http://" + node + "/recip", json={'port': port})
        except:
            continue

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


@app.route('/nodes/', methods=['GET'])
def send_node_list():
    """
    App route to call to return a list of all nodes this node is connected to.
    """
    response = {'nodes': list(blockchain.nodes)}
    return jsonify(response), 200


@app.route('/results/', methods=['GET'])
def send_results():
    # TODO: THIS PAGE CAUSES RESOLVE.
    # TODO: GET THE BALANCE OF EACH CANDIDATE FROM THE CURRENT CHAIN.
    return render_template('results.html')


@app.route('/vote', methods=['post'])
@app.route('/vote/', methods=['post'])
def submit_vote():
    vote_number = int(request.form["id"])
    signature = request.form["key"]
    recipient = request.form["candidate"]
    print("ID: ", vote_number)
    print("Key: " + signature)
    print("Candidate: " + recipient)
    sender = blockchain.get_transactor(vote_number)
    if not sender:
        return jsonify({"status": "fail"})

    vote = blockchain.new_transaction(
        sender=sender,
        recipient=recipient,
        amount=1,
        signature=signature,
        vote_number=vote_number
    )
    if not blockchain.valid_transaction(vote, blockchain.chain):
        return jsonify({"status": "fail"})
    if not blockchain.valid_balance(vote):
        return jsonify({"status": "fail"})
    # Do the above checks in order to display to html if the vote is valid.
    # Note: the blockchain will do these checks independently, so even if a malicous
    # party were to remove these checks from their code and then start a node and connect
    # to the other nodes, an illegitamate transaction still won't be accepted, since
    # each legitimate node will perform these checks on the transaction before
    # accepting a chain with this transaction in it.

    # Transaction appears valid. Add it and any pending transactions to a new block:
    # Run the proof of work algorithm to get the next proof:
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    # Return fail if transaction somehow was not properly placed in the block.
    if not block['transactions']:
        return jsonify({"status": "fail"})
    if vote not in block['transactions']:
        return jsonify({"status": "fail"})
    # Transaction successfully added to new block. Broadcast the new transaction to other nodes.
    # TODO: BROADCAST TO OTHER NODES. IMPLEMENT BROADCAST_VOTE FUNC. IMPLEMENT RCV VOTE APP ROUTE FUNC.///////////////////////////////
    # HTML will now redirect to page for checking vote.
    return jsonify({"status": "success"})


@app.route('/recip/', methods=['post'])
def reciprocate_acknowledgement():
    """
    App route to call to return a list of all nodes this node is connected to.
    """
    values = request.get_json(force=True)
    blockchain.register_node(request.remote_addr + ":" + str(values['port']))
    response = {
        'message': 'New node added',
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200


@app.route('/remove/', methods=['post'])
def remove_node():
    """
    App route to call to remove a node that is terminating itself.
    """
    values = request.get_json(force=True)
    blockchain.remove_node(request.remote_addr + ":" + str(values['port']))
    response = {
        'message': 'Node removed',
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200


def initialize(chain_source):
    """
    Link to a specified manager or miner node and import a blockchain from that node.
    """
    if chain_source[-1] != '/':
        chain_source += '/'
    input_source = chain_source[:]

    parsed_url = urlparse(chain_source)
    if parsed_url.netloc:
        chain_source = parsed_url.netloc
    elif parsed_url.path:
        # Accepts a URL like '192.168.0.5:5000'.
        chain_source = parsed_url.path
    else:
        raise ValueError('Invalid source URL. Maybe it was a typo?')

    blockchain.register_node(input_source)
    print("\n   Querying source: {}".format("http://" + chain_source + "/nodes/"))
    response = None
    for i in range(5):
        try:
            response = requests.get("http://" + chain_source + "/nodes/")
            if response.status_code:
                break
        except:
            print("   Connection to {} source failed, retrying. Attempt {} of 5".format(
                "default" if input_source == "http://127.0.0.1:4999/" else "specified", i + 1))
            sleep(2)
            i += 1
            if i == 4:
                print("\n  ***Connection failed. Maybe that server isn't alive right now? Please try again. ***")
                quit()

    # Nodes only respond 200 if they are peer nodes, not an initiation node,
    # which simply shuts down after it passes on the blockchain.
    if response.status_code == 200:
        # List of nodes connected to our target source.
        connected_nodes = response.json()['nodes']
        # Ask for recip with target source:
        response = requests.post("http://" + chain_source + "/recip", json={'port': port})
        if len(connected_nodes):
            print("   Registering nodes connected to target node and requesting reciprocation.")
            for node in connected_nodes:
                response = None
                try:
                    response = requests.post("http://" + node + "/recip/", json={'port': port})
                    if response:
                        blockchain.register_node(node)
                except:
                    continue
        print("   Connected established with the following nodes:")
        for node in blockchain.nodes:
            print("      {}".format(node))

    initialize_from_source = blockchain.resolve_conflicts()
    # A key feature of using blockchains in an election is that votes cannot be 'mined' after the
    # initial blockchain is set up, though transactions can still be added to blocks with zero value.

    blockchain.value_lock()
    if initialize_from_source:
        print("\n  ***Local blockchain has been initialized to match the specified source!***\n")
    else:
        print("\n  ***Failed to import blockchain from the specified source. "
              "Try a different source or maybe just panic?***")
        quit()

    if response.status_code == 204:
        # If the target node was an initialization type node, it is terminated after it passes on a chain.
        blockchain.remove_node(input_source[:-1])  # The [:-1] removes the slash from the end of the source address.


def exit_func():
    print("\n   Shutting down node...")
    for node in blockchain.nodes:
        # Have one of the other nodes resolve the chain, so that if this node has the longest chain,
        # the chain is sent off to a node that is not exiting.
        try:
            response = requests.get("http://" + node + "/resolve/")
            if response:
                break
        except:
            continue
    # Tell other nodes to remove this node from their lists of nodes. Not strictly necessary, just less time wasted
    # pinging this address later.
    for node in blockchain.nodes:
        try:
            requests.post("http://" + node + "/remove/", json={'port': port})
        except:
            continue
    print("   Have a nice day.")


app.wsgi_app = ProxyFix(app.wsgi_app)


if __name__ == '__main__':
    atexit.register(exit_func)
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-src', '--source', default="http://127.0.0.1:4999/", type=str,
                        help='port to listen on')
    args = parser.parse_args()
    port = args.port
    source = args.source
    initialize(source)
    # Initialize the app on the desired port:
    app.run(host='0.0.0.0', port=port, threaded=True)
