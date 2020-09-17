import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    
    #creating a block chain
    
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.genesis=self.create_block(proof=1,previous_hash='0')
        #add nodes(address of nodes) of peer to peer into sets
        self.nodes=set()
        
        
    def create_block(self, proof, previous_hash):
        block={'index':len(self.chain)+1, 
               'timestamp': str(datetime.datetime.now()), 
               'proof':proof, 
               'previous_hash': previous_hash,
               'transaction':self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block 
    
    
    def get_previous_block(self):
        return self.chain[-1]
    
    
    def proof_of_work(self, previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            #func should be assymetric
            hash_operation = hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1      
        return new_proof
    
    
    def hash(self,block):
        encoded_block = json.dumps(block,sort_keys = True).encode()#did not get this
        return hashlib.sha256(encoded_block).hexdigest()
    
    
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        block_index=1
        while block_index < len(chain):
            block=chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof=previous_block['proof']
            current_proof=block['proof']
            hash_operation = hashlib.sha256(str(current_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]!='0000':
                return False
            
            previous_block=chain[block_index]
            block_index+=1
            
            
        return True
    
    def add_transaction(self,sender,receiver,amount):
        self.transactions.append({'sender':sender,
                                  'receiver':receiver,
                                  'amount':amount})
        prev_block= self.get_previous_block()
        return prev_block['index']+1   
    
    
    def add_node(self,address):
        parsed_url= urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
        
    def replace_chain(self):
        network=self.nodes
        longest_chain = None
        max_len = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                lenn=response.json()['len']
                chain = response.json()['chain']
                if lenn>max_len and self.is_chain_valid(chain):
                    max_len=lenn
                    longest_chain=chain
                    
        if longest_chain:
            self.chain=longest_chain
            return True
        
        return False
                    
    
#Mining blockchain
app = Flask(__name__)

#creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-','')
           
bc = Blockchain()

#http://127.0.0.1:5000/mine_block
@app.route('/mine_block', methods=['GET',])
def mine_block():
    previous_block = bc.get_previous_block()
    previous_proof = previous_block['proof']
    proof = bc.proof_of_work(previous_proof)
    previous_hash = bc.hash(previous_block)
    bc.add_transaction(sender=node_address,receiver='spoo3',amount=1)
    block = bc.create_block(proof,previous_hash)
    response = {'message':'congo, u just mined a block',
                'index':block['index'],
                'timestamp': block['timestamp'], 
                'proof': block['proof'],  
                'previous_hash':block['previous_hash'],
                'transaction':block['transaction']}
    return jsonify(response),200 


@app.route('/get_chain', methods=['GET',])
def get_chain():
    response = {'chain':bc.chain,
                'len':len(bc.chain)}
    return jsonify(response),200


@app.route('/is_valid', methods=['GET',])
def is_valid():
    return_val = bc.is_chain_valid(bc.chain)
    response = {'return_val':return_val}
    return jsonify(response),200

#adding a new transaction to the blockchain
@app.route('/add_transaction',methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'Some of the elements of the transaction are missing',400
    index=bc.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {'message': f'transaction is added in the block number {index}'}
    return jsonify(response),201


#connecting new node
@app.route('/add_node', methods=['POST'])
def add_node():
    json=request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'Its empty',400
    for node in nodes:
        bc.add_node(node)
    response = {'message':'nodes are added into the peer to peer network',
                'total_nodes':list(bc.nodes)}
    return jsonify(response),201

#Replacing the chain by the longest chain
@app.route('/check_chain',methods=['GET',])
def check_chain():
    check_value = bc.replace_chain()
    if check_value == True:
        response = {'message':'The chain was replaced',
                    'new_chain':bc.chain}
    else:
        response ={'message':'The chain is the largtest one',
                   'actual_chain':bc.chain}
    return jsonify(response),200


app.run(host = '0.0.0.0', port = 5003)
    
    
    
    


            
