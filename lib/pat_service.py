from flask import Flask, request
from modules.pat_agent import PatAgent
import json
import logging

formatter = logging.Formatter('%(asctime)s - %(name)s - Level:%(levelname)s - %(message)s')
logger = logging.getLogger('pat-agent')
logging.getLogger('pat-agent').setLevel(logging.DEBUG)
filename = '/var/log/praas/pat-agent.log'
handler = logging.FileHandler(filename, 'a')
handler.setFormatter(formatter)
logger.addHandler(handler)

from  configparser import ConfigParser
config = ConfigParser()
#config.read('praas.conf')
config.read('/usr/local/etc/praas/praas.conf')

port = config['praas']['port_app']
app = Flask(__name__)
pat_agent = PatAgent(logger)

# get all pat information on router
@app.route('/router_pat',methods=['GET'])
def list_PAT_mapping():
	try:
		router_id  = request.args['router_id']
		result = pat_agent.router_pat_info( router_id )
		response = app.response_class(
			response= json.dumps(result),
			status = 200,
			mimetype='application'
		)
		return response
	except Exception as e:
		print(e)
		return { 'status': 'API_ERROR', 'message': e }	

# get router pat information on router
@app.route('/router_server_pat',methods=['GET'])
def list_PAT_mapping_server_router():
        try:
                router_id = request.args['router_id']
		server_ip = request.args['server_ip']
                result = pat_agent.router_server_pat_info(router_id , server_ip)
                response = app.response_class(
                        response= json.dumps(result),
                        status = 200,
                        mimetype='application'
                )
		return response
        except Exception as e:
                print(e)
                return { 'status': 'API_ERROR', 'message': e } 

# create port address translation 
@app.route('/pat/create', methods = ['POST'])
def create_PAT_mapping():
	try:
		params = request.args
		result = pat_agent.add_nat(params['server_ip'], params['router_id'], params['create_server_port'], params['gateway'])
		response = app.response_class(
                        response= json.dumps(result),
                        status = 200,
                        mimetype='application'
                )
		return response 
	except Exception as e:
		print(e)
		logger.debug({ 'status': 'API_ERROR', 'message': e }) 
# remove port translate address
@app.route('/pat/remove', methods = ['POST'])
def remove_PAT_mapping():
        try:
                params = request.args
                response = pat_agent.remove_nat(params['server_ip'], params['router_id'], params['remove_server_port'], params['gateway'])
                return response
        except Exception as e:
                print(e)
                return { 'status': 'API_ERROR', 'message': e }
# modify port translate address
@app.route('/pat/modify', methods = ['POST'])
def modify_PAT_mapping():
        try:
                params = request.args
                response = pat_agent.modify_nat(params['server_ip'], params['router_id'], params['modify_server_port']
							, params['modify_router_port'], params['gateway'])
                return response
        except Exception as e:
                print(e)
                return { 'status': 'API_ERROR', 'message': e }
	

app.run(debug=True,host='0.0.0.0', port=port)
