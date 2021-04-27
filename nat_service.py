from flask import Flask, request
from modules.nat_agent import NatAgent
import json

app = Flask(__name__)
nat_agent = NatAgent()


# List all ports of router has been opened 
@app.route('/router_allports',methods=['GET'])
def router_ports():
	try:
		router = request.args['router']
		result = nat_agent.show_router_port(router)
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
@app.route('/router_vm_ports',methods=['GET'])
def mapping_server_router_ports():
        try:
                router = request.args['router']
		server = request.args['server']
                result = nat_agent.show_server_router_port_mapping(router, server)
                response = app.response_class(
                        response= json.dumps(result),
                        status = 200,
                        mimetype='application'
                )
                return response
        except Exception as e:
                print(e)
                return e

# add port translate address 
@app.route('/pat/add', methods = ['POST'])
def add_pat():
	try:
		params = request.args
		response = nat_agent.add_nat(params['server'], params['router'], params['vmport'], params['gateway'])
		return response 
	except Exception as e:
		print(e)
		return e 
# remove port translate address
@app.route('/pat/remove', methods = ['POST'])
def remove_pat():
        try:
                params = request.args
                response = nat_agent.remove_nat(params['server'], params['router'], params['vmport'], params['gateway'])
                return response
        except Exception as e:
                print(e)
                return e
# modify port translate address
@app.route('/pat/modify', methods = ['POST'])
def modify_pat():
        try:
                params = request.args
                response = nat_agent.modify_nat(params['server'], params['router'], params['vmport'], params['new_router_port'], params['gateway'])
                return response
        except Exception as e:
                print(e)
                return e
	
app.run(debug=True,host='0.0.0.0', port=3000)
