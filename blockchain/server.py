from flask import Flask, jsonify, request

from blockchain import Blockchain
from block import Block
from transaction import Transaction
from wallet import Wallet

# Instantiate the Node
app = Flask(__name__)

# Instantiate the Blockchain
blockchain = Blockchain()

# Read private and public key for wallet
wallet = Wallet('wallet')


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block: Block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    transaction = Transaction(
        sender="0",
        recipient=wallet.public_key,
        amount=1,
    )

    blockchain.new_transaction(transaction)

    # Forge the new Block by adding it to the chain
    previous_hash = last_block.hash()
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'block': block.json()
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    transaction = Transaction(values['sender'], values['recipient'], values['amount'])
    if not transaction.signature_valid(values['signature']):
        return 'Signature invalid', 500

    # Create a new Transaction
    index = blockchain.new_transaction(transaction)

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/transactions/sign', methods=['POST'])
def sign_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'signkey']
    if not all(k in values for k in required):
        return 'Missing values', 400

    transaction = Transaction(values['sender'], values['recipient'], values['amount'])
    signature = transaction.sign(values['signkey'])

    response = {
        'message': 'for testing purposes only',
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount'],
        'signature': signature
    }
    return jsonify(response), 300


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.json(),
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/wallet', methods=['POST'])
def wallet_amount():
    values = request.get_json()

    wallet_id = values.get('wallet')
    if wallet_id is None:
        return "Error: Please supply a wallet id", 400

    amount = blockchain.get_wallet_amount(wallet_id)

    response = {
        'wallet': wallet_id,
        'amount': amount
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

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


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-d', '--debug', default=0, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    debug = args.debug

    app.run(debug=debug, host='0.0.0.0', port=port)
