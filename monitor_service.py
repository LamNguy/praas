from modules.monitoring_agent import MonitorAgent
import openstack
import time
import logging
formatter = logging.Formatter(
                '%(asctime)s - %(name)s - Level:%(levelname)s - %(message)s')
logger = logging.getLogger('monitor-agent')
logging.getLogger('monitor-agent').setLevel(logging.DEBUG)
filename = '/var/log/praas/monitor-agent.log'
handler = logging.FileHandler(filename, 'a')
handler.setFormatter(formatter)
logger.addHandler(handler)
import threading
try:
	conn = openstack.connection.from_config(cloud = 'openstack')
	conn.authorize()
	monitor_agent = MonitorAgent(conn,logger) 
	namespaces = monitor_agent.get_namespaces()
	
	#for ns in namespaces:
        #	monitor_agent.check_namespace(ns)

	while True:
		print(1)
		logger.info(1)
		#timer = threading.Timer(5,monitor_agent.monitoring)
		#timer.start()
		time.sleep(5)

except Exception as e:
	logger.error(e)	
finally:
	conn.close()


