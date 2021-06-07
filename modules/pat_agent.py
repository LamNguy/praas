import netns
import iptc
from random import randint
from  configparser import ConfigParser
class PatAgent:

	__agent__ = None
	logger = None
	
	def __init__ (self,logger):

		config = ConfigParser()
		config.read('/usr/local/etc/praas/praas.conf')
		#config.read('praas.conf')
		router_port_range  = config['praas']['router_port_range']



		if PatAgent.__agent__ is None:
			PatAgent.__agent__ = self
			PatAgent.router_port_range = router_port_range
			PatAgent.logger = logger

		else:
			raise Exception('You are allowed to create only one Agent')
	@staticmethod
	def get_agent():
		if not PatAgent.__agent__ :
			PatAgent()
		return PatAgent.__agent__ 

	# get pat information on a specific router		
	@staticmethod
	def router_pat_query( router_id ):
		with netns.NetNS(nsname= router_id):
                        prerouting = iptc.easy.dump_chain('nat','custom-PREROUTING',ipv6=False)
                        postrouting = iptc.easy.dump_chain('nat','custom-POSTROUTING',ipv6=False)
                        server_nat_ports = {}
                        mapping_ports = {}
                        router_nat_ports = []
                        # list vm_port which vm opened (vms)
                        for rule in postrouting:
                                dst = rule['dst'][:-3]
                                if dst in server_nat_ports:
                                        server_nat_ports[dst].append(rule['tcp']['dport'])
                                else:
                                        server_nat_ports[dst] = []
                                        server_nat_ports[dst].append(rule['tcp']['dport'])

                        for rule in prerouting:
                                src = rule['target']['DNAT']['to-destination']
                                dport = rule['tcp']['dport']
                                router_nat_ports.append(dport)
                                mapping_ports[src] = dport
                        return server_nat_ports, mapping_ports, router_nat_ports

	@staticmethod
        def router_pat_info( router_id ):
                server_nat_ports , mapping_ports, router_nat_ports = PatAgent.__agent__.router_pat_query( router_id )
		PatAgent.logger.info('Return pat information on router {}'.format(router_id))
                return mapping_ports

	@staticmethod
	def router_server_pat_info( router_id , server_ip):
		server_nat_ports, mapping_ports , router_ports = PatAgent.__agent__.router_pat_query(router_id)
		response = {}
		if server_ip in server_nat_ports:
			for server_port in server_nat_ports[server_ip]:
				mapping = server_ip + ':' + server_port
				response[server_port] = mapping_ports[mapping]	
		return response
		

	@staticmethod
        def create_rules(server_ip, server_port, router_port, gateway):
                destination = server_ip + ':' +  server_port
                prerouting_rule = iptc.Rule()
                prerouting_rule.protocol ="tcp"
		prerouting_rule.dst = gateway
                match = iptc.Match(prerouting_rule, "tcp")
                match.dport = router_port 
                target = prerouting_rule.create_target("DNAT")
                target.to_destination = destination 
                prerouting_rule.add_match(match)
                prerouting_rule.target = target

                postrouting_rule = iptc.Rule()
                postrouting_rule.protocol ="tcp"
                postrouting_rule.dst = server_ip 
                match = iptc.Match(postrouting_rule, "tcp")
                match.dport = server_port
                postrouting_rule.add_match(match)
                postrouting_rule.target = iptc.Target(postrouting_rule,"MASQUERADE")
		return prerouting_rule, postrouting_rule

	# add port address translation processing
	@staticmethod
        def add_pat(server_ip, router_id, server_port, router_port, gateway):
                with netns.NetNS(nsname= router_id):
			nat = iptc.Table(iptc.Table.NAT)
                        prerouting_chain = iptc.Chain( nat ,"custom-PREROUTING")
                        postrouting_chain = iptc.Chain( nat ,"custom-POSTROUTING")
			prerouting_rule, postrouting_rule = PatAgent.__agent__.create_rules(server_ip, server_port, router_port, gateway)
			prerouting_chain.insert_rule(prerouting_rule)
                        postrouting_chain.insert_rule(postrouting_rule)
			nat.close()
			nat._cache.clear()

	# port address translation processing
	@staticmethod
	def remove_pat(server_ip, router_id, server_port, router_port, gateway):
		with netns.NetNS(nsname= router_id):
			nat = iptc.Table(iptc.Table.NAT)
                        prerouting_chain = iptc.Chain( nat ,"custom-PREROUTING")
                        postrouting_chain = iptc.Chain( nat ,"custom-POSTROUTING")
                        prerouting_rule, postrouting_rule = PatAgent.__agent__.create_rules(server_ip, server_port, router_port, gateway)
                        prerouting_chain.delete_rule(prerouting_rule)
                        postrouting_chain.delete_rule(postrouting_rule)
			nat.close()
                        nat._cache.clear()

	# add port nat fucntion
	@staticmethod
	def add_nat (server_ip, router_id, create_server_port, gateway):

		try:
			assert isinstance(int(create_server_port), int), 'Argument is not integer!'
			# get server_nat_ports , mapping_ports , router_nat_ports 
			server_nat_ports , mapping_ports, router_nat_ports = PatAgent.__agent__.router_pat_query(router_id)
		
			# check if server port has nat on router? 
			if (server_ip in server_nat_ports) and (create_server_port in server_nat_ports[server_ip]):
        			mapping = server_ip + ':' + create_server_port
				response = {
					'status': 'CREATED',
					'created_server_port': create_server_port,
					'created_router_port': mapping_ports[mapping],
					'server_ip': server_ip,
					'gateway': gateway,
					'message': 'Server port has been PAT already'
				}
				PatAgent.logger.debug('Find existing port {} of server {} which has translated to port {} on router {}'.format(create_server_port, server_ip, mapping_ports[mapping], gateway))
			
    			else:
				start, end = PatAgent.router_port_range.split(':')
        			router_port = str(randint(int(start),int(end)))
        			# check len router_nat_ports if full will make error
        			while router_port in router_nat_ports:
                			router_port = str(randint(int(start),int(end)))
			
				PatAgent.__agent__.add_pat(server_ip, router_id, create_server_port, router_port,gateway)
				
				response = {
					'status' : 'SUCCESS',
					'create_router_port': router_port,	
					'server_ip': server_ip,
					'create_server_port' : create_server_port,
					'gateway': gateway,
					'message': 'Create PAT successfully'
				}
				PatAgent.logger.info('Create port {} of server {} which has translated to port {} on router {}'.format(create_server_port, server_ip, router_port, gateway))

		except Exception as e:
			PatAgent.logger.error(e)	
			response = { 'status': 'ERROR', 'message': e }
		finally:
			return response	

	# remove port nat funtion
	@staticmethod
        def remove_nat (server_ip, router_id, remove_server_port, gateway):

		try:
			assert isinstance(int(remove_server_port), int), 'Argument of wrong type!'
			# get server_nat_ports , mapping_ports , router_nat_ports 
                	server_nat_ports , mapping_ports, router_nat_ports = PatAgent.__agent__.router_pat_query(router_id)
			if ( server_ip in server_nat_ports) and ( remove_server_port in server_nat_ports[server_ip]):
				mapping = server_ip + ':' + remove_server_port
				PatAgent.__agent__.remove_pat(server_ip, router_id, remove_server_port, mapping_ports[mapping],gateway)
				response = {
                                        'status' : 'REMOVED',
                                        'remove_router_port': mapping_ports[mapping],
                                        'server_ip': server_ip,
                                        'remove_server_port' : remove_server_port,
                                        'gateway': gateway,
					'message': 'Remove PAT successfully'
                                }
				PatAgent.logger.info('Remove port {} of server {} which has translated to port {} on router {}'.format(remove_server_port, server_ip, mapping_ports[mapping], gateway))
			else:
				response = {
                                        'status' : 'NO CREATED',
                                        'remove_server_port': remove_server_port,
                                        'server_ip': server_ip,
                                        'gateway': gateway,
					'message': 'The remove port has not been PAT yet'
                                }
				PatAgent.logger.debug('The remove port {} of server {} which has not been translated on router {}'.format(remove_server_port, server_ip,gateway))
		except Exception as e:
			PatAgent.logger.error(e)
			response = { 'status': 'ERROR', 'message': e }
		finally: 
			return response
	# modify port nat function
	@staticmethod
	def modify_nat(server_ip, router_id, modify_server_port, modify_router_port, gateway):

		try:
			# get server_nat_ports , mapping_ports , router_nat_ports 
                	server_nat_ports , mapping_ports, router_nat_ports = PatAgent.__agent__.router_pat_query(router_id)
			if (server_ip not in server_nat_ports) or (modify_server_port not in server_nat_ports[server_ip]) :
				response = {
                                        'status' : 'NO CREATED',
                                        'server_ip': server_ip,
                                        'modify_server_port' : modify_server_port,
                                        'gateway': gateway,
					'message': 'Server port has not PAT yet'
                                }
				PatAgent.logger.debug('Can not modify because port {} of server {} which has not been translated on router {}'.format(modify_server_port, server_ip, gateway))
			elif modify_router_port in router_nat_ports:
				mapping = server_ip + ':' + modify_server_port
				response = {
                                        'status' : 'USED',
					'modified_router_port': mapping_ports[mapping],
                                        'server_ip': server_ip,
                                        'modify_server_port' : modify_server_port,
					'modify_router_port': modify_router_port,
                                        'gateway': gateway,
					'message': "New router_id port has been used already"
                                }
				PatAgent.logger.debug('Can not modify because port {} of router {} which has translated already'.format(modify_router_port, gateway))
			else:
				mapping = server_ip + ':' + modify_server_port
				PatAgent.__agent__.remove_pat(server_ip, router_id, modify_server_port, mapping_ports[mapping], gateway)
				PatAgent.__agent__.add_pat(server_ip, router_id, modify_server_port, modify_router_port, gateway)
				response = {
                                        'status' : 'SUCCESS',
                                        'modified_router_port': mapping_ports[mapping],
					'modify_router_port': modify_router_port,
                                        'server_ip': server_ip,
                                        'modify_server_port' : modify_server_port,
                                        'gateway': gateway,
					'message': "Modify PAT successfully"
                                }
				PatAgent.logger.info('Modify old router port {} to new router port {} on router {} which has translate to port {} of server {}'.format(mapping_ports[mapping],modify_router_port, gateway, modify_server_port,server_ip))
		except Exception as e:
			PatAgent.logger.error(e)
			response = { 'status': 'ERROR',  'message': e  }
		finally:
			return response
