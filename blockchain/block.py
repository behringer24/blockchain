from time import time
import hashlib
import json

from transaction import Transaction
from typing import List, Set, Tuple, Dict

class Block:

    index = 0
    timestamp = 0
    transactions: List[Transaction] = []
    proof = 0
    previous_hash = ""

    def __init__(self, index, proof, previous_hash="", transactions: List[Transaction]=[]):
        self.index = index
        self.timestamp = time()
        self.transactions = transactions
        self.proof = proof
        self.previous_hash = previous_hash

    @classmethod
    def from_json(cls, json_block: json):
        transactions: List[Transaction] = []
        for json_transaction in json_block['transactions']:
            transactions.append(Transaction.from_json(json_transaction))
        return cls(json_block['index'], json_block['proof'], json_block['previous_hash'], transactions)

    def hash(self):
        """
        Creates a SHA-256 hash of this Block

        :return: str
        """
        json_block = json.dumps(self.json(), sort_keys=True).encode()
        return hashlib.sha256(json_block).hexdigest()

    def json(self):
        json_transactions = []
        for transaction in self.transactions:
            json_transactions.append(transaction.json())
        
        response = {
            'index':self.index,
            'timestamp': self.timestamp,
            'transactions': json_transactions,
            'proof': self.proof,
            'previous_hash': self.previous_hash,
        }
        return response