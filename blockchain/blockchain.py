import hashlib
import json
from json.decoder import JSONDecodeError
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey

import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.wallets = {}
        private_key = ""
        public_key = ""

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')


    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def generate_wallet(self, name='wallet'):
        private_key = SigningKey.generate()
        public_key = private_key.verify_key
        payload = {
            "private_key": private_key.encode(encoder=HexEncoder).decode(),
            "public_key": public_key.encode(encoder=HexEncoder).decode(),
        }
        with open(name + ".json", "w") as file:
            json.dump(payload, file)
        return payload

    def get_wallet(self):
        try:
            with open("wallet.json", "r") as file:
                keys = json.load(file)
        except (JSONDecodeError, FileNotFoundError):
            keys = self.generate_wallet()

        self.private_key = keys["private_key"]
        self.public_key = keys["public_key"]

        return self.public_key

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Update wallets
        for transaction in self.current_transactions:
            self.wallets[transaction['recipient']] = self.wallets.get(transaction['recipient'], 0) + transaction['amount']
            self.wallets[transaction['sender']] = self.wallets.get(transaction['sender'], 0) - transaction['amount']

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """

        transaction_block = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        self.current_transactions.append(transaction_block)

        return self.last_block['index'] + 1


    def validate_transaction(self, sender, recipient, amount, signature):
        """
        Validate if transaction is signed correctly

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :param signature: Signature
        :return: boolean
        """

        #return 1

        verify_key = VerifyKey(sender, encoder=HexEncoder)

        transaction_block = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        block_string = json.dumps(transaction_block, sort_keys=True).encode()
        signature_bytes = HexEncoder.decode(signature)

        return verify_key.verify(block_string, signature_bytes)

    def sign_transaction(self, sender, recipient, amount, signing_key):
        signing_key = SigningKey(signing_key, encoder=HexEncoder)

        transaction_block = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }
        block_string = json.dumps(transaction_block, sort_keys=True).encode()

        return signing_key.sign(block_string).signature.hex()

    def transactions_for(self, wallet):
        """
        Calculate the amount of open transactions for wallet

        :param wallet: A wallet id
        :return: value
        """

        amount = 0

        for transaction in self.current_transactions:
            if (transaction['recipient'] == wallet):
                amount += transaction['amount']
            if (transaction['sender'] == wallet):
                amount -= transaction['amount']

        return amount


    def wallet(self, wallet):
        """
        Return the amount of a wallet

        :param wallet: A wallet id
        :return: value
        """

        return self.wallets.get(wallet, 0)


    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
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
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.

        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Instantiate the Blockchain
blockchain = Blockchain()

# Generate a globally unique address for this node
#node_identifier = str(uuid4()).replace('-', '')
node_identifier = blockchain.get_wallet()

@app.route('/wallet', methods=['POST'])
def wallet():
    values = request.get_json()

    wallet = values.get('wallet')
    if wallet is None:
        return "Error: Please supply a wallet id", 400

    amount = blockchain.wallet(wallet)

    response = {
        'wallet': wallet,
        'amount': amount
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400

    if not blockchain.validate_transaction(values['sender'], values['recipient'], values['amount'], values['signature']):
        return 'Wrong signature', 400

    if blockchain.wallet(values['sender']) + blockchain.transactions_for(values['sender']) < values['amount']:
        return 'Wallet has not enough tokens', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}', 'signature': values['signature']}
    return jsonify(response), 201


@app.route('/transactions/sign', methods=['POST'])
def sign_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'signkey']
    if not all(k in values for k in required):
        return 'Missing values', 400

    response = {
        'message': 'for testing purposes only',
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount'],
        'signature': blockchain.sign_transaction(values['sender'], values['recipient'], values['amount'], values['signkey'])
    }
    return jsonify(response), 300


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
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
    parser.add_argument('-d', '--debug', default=0, type=int, help='run server in debug mode')
    args = parser.parse_args()
    port = args.port
    debug = args.debug == 1

    app.run(debug=debug, host='0.0.0.0', port=port)
