import hashlib
import json
from json.decoder import JSONDecodeError
import requests
from block import Block
from transaction import Transaction
from typing import List, Set, Tuple, Dict

class Blockchain:

    current_transactions: List[Transaction] = []
    chain: List[Block] = []
    nodes = set()
    wallets = {}
    private_key = ""
    public_key = ""

    def __init__(self, chain: List[Block] = []):
        self.current_transactions = []
        self.chain = chain
        self.nodes = set()
        self.wallets = {}

        # Create the genesis block
        if len(chain) == 0:
            self.new_block(1, '1')

    @classmethod
    def from_json(cls, json_chain: json):
        chain: List[Block] = []
        for json_block in json_chain:
            cls.chain.append(Block.from_json(json_block))
        return cls(chain)

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


    def valid_chain(self, chain: List[Block]):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # Check that the hash of the block is correct
            last_block_hash = last_block.hash()
            if block.previous_hash != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block.proof, block.proof, last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True


    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain: List[Block] = []

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = Blockchain.from_json(response.json()['chain'])

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

        block = Block(
            index=len(self.chain) + 1,
            proof=proof,
            previous_hash=previous_hash or self.chain[-1].hash(),
            transactions=self.current_transactions
            )

        # Update wallets
        for transaction in self.current_transactions:
            self.wallets[transaction.recipient] = self.wallets.get(transaction.recipient, 0) + transaction.amount
            self.wallets[transaction.sender] = self.wallets.get(transaction.sender, 0) - transaction.amount

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, transaction: Transaction):
        """
        Creates a new transaction to go into the next mined Block

        :param transaction: Transaction Transaction to add to chain
        :return: The index of the Block that will hold this transaction
        """

        self.current_transactions.append(transaction)

        return self.last_block.index + 1


    def transactions_for(self, wallet):
        """
        Calculate the amount of open transactions for wallet

        :param wallet: A wallet id
        :return: value
        """

        amount = 0

        for transaction in self.current_transactions:
            if (transaction.recipient == wallet):
                amount += transaction.amount
            if (transaction.sender == wallet):
                amount -= transaction.amount

        return amount


    def get_wallet_amount(self, wallet):
        """
        Return the amount of a wallet

        :param wallet: A wallet id
        :return: value
        """

        return self.wallets.get(wallet, 0)


    @property
    def last_block(self):
        """
        Returns last block in chain

        :return: Block
        """
        return self.chain[-1]


    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block.proof
        last_hash = last_block.hash()

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

    def json(self):
        json_chain = []
        for block in self.chain:
            json_chain.append(block.json())
        return json_chain