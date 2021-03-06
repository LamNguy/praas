from praas.monitoring_agent import MonitorAgent
import openstack
import time
import logging
import threading
formatter = logging.Formatter('%(asctime)s - %(name)s - Level:%(levelname)s - %(message)s')
logger = logging.getLogger('monitor-agent')
logging.getLogger('monitor-agent').setLevel(logging.DEBUG)
filename = '/var/log/praas/monitor-agent.log'
handler = logging.FileHandler(filename, 'a')
handler.setFormatter(formatter)
logger.addHandler(handler)

from  configparser import ConfigParser
config = ConfigParser()
config.read('/usr/local/etc/praas/praas.conf')


try:
	conn = openstack.connection.from_config(cloud = 'openstack')
	conn.authorize()
	monitor_agent = MonitorAgent(conn,logger) 
	sec = config['praas']['second_monitoring']	
	ticker = threading.Event()
	while not ticker.wait(int(sec)):
		logger.info('Monitor agent is doing job')
		for ns in monitor_agent.get_namespaces():
			monitor_agent.check_namespace(ns)
		monitor_agent.monitoring()
	
except Exception as e:
	logger.error(e)	
finally:
	conn.close()


