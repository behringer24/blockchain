class block:
    def __init__(self, index, proof, previous_hash="", transactions=[]):
        self.index = index
        self.timestamp = time()
        self.transactions = transactions
        self.proof = proof
        self.previous_hash = previous_hash

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def json(self):
        return {
            'index':self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'proof': self.proof,
            'previous_hash': self.previous_hash,
        }