from modules.monitoring_agent import MonitorAgent
import openstack
from multiprocessing import  TimeoutError , cpu_count 
from multiprocessing.pool import ThreadPool
import time

try:
	conn = openstack.connect(cloud = 'openstack')
	conn.authorize()
	monitor_agent = MonitorAgent(conn) 
	namespaces = monitor_agent.get_namespaces()
	
	#for ns in namespaces:
	#	monitor_agent.check_namespace(ns)

	#for namespace in namespaces:
	#	router = MonitorAgent.__agent__.conn.network.get_router(namespace)
	#	print(router.external_gateway_info['external_fixed_ips'][0]['ip_address'])

	# monitor and update
	monitor_agent.monitoring()
except Exception as e:
	print(e)
finally:
	conn.close()


