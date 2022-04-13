import json
from json.decoder import JSONDecodeError

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

class Wallet:

    private_key = ""
    public_key = ""

    def __init__(self, name: str):
        try:
            with open(name + ".json", "r") as file:
                keys = json.load(file)
        except (JSONDecodeError, FileNotFoundError):
            keys = self.generate_wallet(name)

        self.private_key = keys["private_key"]
        self.public_key = keys["public_key"]


    def generate_wallet(self, name: str):
        private_key = SigningKey.generate()
        public_key = private_key.verify_key
        payload = {
            "private_key": private_key.encode(encoder=HexEncoder).decode(),
            "public_key": public_key.encode(encoder=HexEncoder).decode(),
        }
        with open(name + ".json", "w") as file:
            json.dump(payload, file)
        return payload