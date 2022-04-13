# Dockerized python blockchain
Inspired by Daniel van Flymen: https://github.com/dvf/blockchain

This is an experimental implementation of a simple blockchain I forked from Daniel van Flymen.

## Goal
The goal is to implement more of the basic technologies used in blockchains and experiment with features.

## Warning
This blockchain is by no means production ready as there are many security flaws.

# Usage and API
## Startup / Install
Clone this repo and `cd` into the checked out path.

Start the server by running `docker-compose up -d`

The server listens on port 5000 for http requests.

The server uses Get and Post requests. The payload is transmitted as json in the body.

## Wallets
The project provides simple wallets that use a private and public key for signing new transactions. Wallets are simple json files saved to the server root.

The public key of the wallet is also used as wallet ids. So you send transactions from public key to public key and you use the private key for signing your transaction for authenticity.

On server startup the server own `wallet.json` is created if not exists.

As cryptographical method we use PyNaCl / libsodium. See: https://github.com/pyca/pynacl

## Requests
### Mine new block
Endpoint: ``/mine``

Method: GET

Payload: none

Mines a new block by solving the proof of work challenge and inserts the block directly into the blockchain. This transfers all 'open' transactions into the chain too. The 'miner' (here always the server itself) receives one coin as a reward.

### Get wallet amoint
Endpoint: ``/wallet``

Method: POST

Payload:
```
{
    'wallet': '<pubkey of wallet>'
}
```

Returns the amount of couns associated with the pubkey of that wallet.

### Send transaction
Endpoint: ``/transactions/new``

Method: POST

Payload:
```
{
    "sender": "<pubkey of sender / yours>",
    "recipient": "<pubkey of recipient>",
    "amount": <amount to send>,
    "signature": "<signature for above three fields>"
}
```

Transfers a new transaction to the stack of open transactions. These Transactions are not written to the blockchain yet and wait for a new block to be mined.

The transaction needs to be signed with the senders private key as you can see in the following code:

```
import json
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

# transaction in json notation
transaction = {
    "sender": "<pubkey of sender / yours>",
    "recipient": "<pubkey of recipient>",
    "amount": <amount to send>
}

# transform json to string representation and sort keys to be consistent
transaction_string = json.dumps(transaction, sort_keys=True).encode()

# generate signing key
signing_key = SigningKey('<private key of sender>', encoder=HexEncoder)

# calculate signature
signature = signing_key.sign(transaction_string).signature.hex()
```

For more infos on signing transaction see https://github.com/pyca/pynacl/blob/main/docs/signing.rst

### Show whole chain
Endpoint: ``/chain``

Method: GET

Payload: None

Returns the whole blockchain in json representation.

### Sign transactions
Endpoint: ``/transactions/sign``

Method: POST

Payload:
```
{
    "sender": "public key of sender",
    "recipient": "<public key of recipient>",
    "amount": <amount to be sent>,
    "signkey": "<private key of sender>"
}
```

WARNING: For testing purposes only. Not intended for production! This should be done in a client application where the private key is kept secret.

Signs a transaction with the provided private key / signing key. See above on how transactions are signed.

Is used in development prior to sending transactions.