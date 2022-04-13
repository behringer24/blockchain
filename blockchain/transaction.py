import json

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey

class Transaction:

    sender = ""
    recipient = ""
    amount = 0

    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    @classmethod
    def from_json(cls, json_transaction: json):
        return cls(json_transaction['sender'], json_transaction['recipient'], json_transaction['amount'])

    def signature_valid(self, signature):
        verify_key = VerifyKey(self.sender, encoder=HexEncoder)
        signature_bytes = HexEncoder.decode(signature)
        json_transaction = json.dumps(self.json(), sort_keys=True).encode()

        return verify_key.verify(json_transaction, signature_bytes)

    def sign(self, signing_key):
        signing_key = SigningKey(signing_key, encoder=HexEncoder)

        transaction_string = json.dumps(self.json(), sort_keys=True).encode()

        return signing_key.sign(transaction_string).signature.hex()

    def json(self):
        response = {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
        }
        return response