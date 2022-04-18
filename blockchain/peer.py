import os
import requests
from urllib.parse import urlparse

from apscheduler.schedulers.background import BackgroundScheduler
from blockchain import Blockchain
from block import Block
from wallet import Wallet

class Peer:
    _nodes = set()
    _scheduler: BackgroundScheduler = BackgroundScheduler()
    _blockchain = None
    _wallet = None

    def __init__(self, blockchain: Blockchain, wallet: Wallet):
        self._nodes = {}
        self._blockchain = blockchain
        self._wallet = wallet
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            # The reloader has already run - avoid flask debug mode to run scheduler twice
            self.start_worker()

    def __del__(self):
        # Shut down the scheduler when exiting the app
        self.stop_worker()
    
    def start_worker(self):
        self._scheduler.add_job(func=self.worker, trigger="interval", seconds=20)
        self._scheduler.start()

    def stop_worker(self):
        self._scheduler.shutdown()

    def worker(self):
        print("Worker working")
        message = {
            'chainlength': len(self._blockchain.chain)
        }
        self.broadcast("/ping", message)

    def register_node(self, address, name="unknown"):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            url = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            url = parsed_url.path
        else:
            raise ValueError('Invalid URL')
        
        if not url in self._nodes or name != "unknown":
            self._nodes[url] = name

    def broadcast(self, path, message = None):
        """
        Brodcast message to all nodes and use path as the endpoint

        :param path: Path of the endpoint
        :param  mesage: Payload in json format
        """

        delete_nodes = set()

        for node in self._nodes:
            if self._nodes[node] != self._wallet.public_key:
                print('Broadcasting to: http://' + node + path + ' (' + self._nodes[node] + ')')
                try:
                    response = requests.post('http://' + node + path, json = message, timeout=5)
                    values = response.json()
                    if "node" in values:
                        self._nodes[node] = values['node']
                    if "blocks" in values:
                        for json_block in values['blocks']:
                            block = Block.from_json(json_block)
                            print(block.index)
                            self._blockchain.add_block(block)
                except Exception as e:
                    print(e)
                    delete_nodes.add(node)
            else:
                print('Skipping myself ' + node)
        
        for node in delete_nodes:
            self._nodes.pop(node, None)