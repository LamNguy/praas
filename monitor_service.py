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
	

	for ns in namespaces:
		monitor_agent.start_monitoring(ns)
except Exception as e:
	print(e)
finally:
	conn.close()


