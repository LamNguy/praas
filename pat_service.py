from flask import Flask, request
from modules.nat_agent import NatAgent
import json

app = Flask(__name__)
nat_agent = NatAgent()

@app.route('/router_pat',methods=['GET'])
def list_PAT_mapping():
	try:
		router_id  = request.args['router_id']
		result = nat_agent.router_pat_info( router_id )
		response = app.response_class(
			response= json.dumps(result),
			status = 200,
			mimetype='application'
		)
		return response
	except Exception as e:
		print(e)
		return e
# List ports which has been opened for a specified server on a router
@app.route('/router_server_pat',methods=['GET'])
def list_PAT_mapping_server_router():
        try:
                router_id = request.args['router_id']
		server_ip = request.args['server_ip']
                result = nat_agent.router_server_pat_info(router_id , server_ip)
                response = app.response_class(
                        response= json.dumps(result),
                        status = 200,
                        mimetype='application'
                )
		return result 
        except Exception as e:
                print(e)
                return e

# add port translate address 
@app.route('/pat/create', methods = ['POST'])
def create_PAT_mapping():
	try:
		params = request.args
		response = nat_agent.add_nat(params['server_ip'], params['router_id'], params['create_server_port'], params['gateway'])
		return response 
	except Exception as e:
		print(e)
		return e 
# remove port translate address
@app.route('/pat/remove', methods = ['POST'])
def remove_PAT_mapping():
        try:
                params = request.args
                response = nat_agent.remove_nat(params['server_ip'], params['router_id'], params['remove_server_port'], params['gateway'])
                return response
        except Exception as e:
                print(e)
                return e
# modify port translate address
@app.route('/pat/modify', methods = ['POST'])
def modify_PAT_mapping():
        try:
                params = request.args
                response = nat_agent.modify_nat(params['server_ip'], params['router_id'], params['modify_server_port']
							, params['modify_router_port'], params['gateway'])
                return response
        except Exception as e:
                print(e)
                return e
	

app.run(debug=True,host='0.0.0.0', port=3000)