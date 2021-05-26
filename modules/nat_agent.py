import netns
import iptc
from random import randint
class NatAgent:

	__agent__ = None
	
	def __init__ (self):
		if NatAgent.__agent__ is None:
			NatAgent.__agent__ = self
		else:
			raise Exception('You are allowed to create only one Agent')
	@staticmethod
	def get_agent():
		if not NatAgent.__agent__ :
			NatAgent()
		return NatAgent.__agent__ 

		
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
                                # the port which router opened (vmy)
                                router_nat_ports.append(dport)
                                # mapping the vm_port_opened with router_port_opened
                                mapping_ports[src] = dport
                        return server_nat_ports, mapping_ports, router_nat_ports

	@staticmethod
        def router_pat_info( router_id ):
                server_nat_ports , mapping_ports, router_nat_ports = NatAgent.__agent__.router_pat_query( router_id )
                return mapping_ports

	@staticmethod
	def router_server_pat_info( router_id , server_ip):
		server_nat_ports, mapping_ports , router_ports = NatAgent.__agent__.router_pat_query(router_id)
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
			prerouting_rule, postrouting_rule = NatAgent.__agent__.create_rules(server_ip, server_port, router_port, gateway)
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
                        prerouting_rule, postrouting_rule = NatAgent.__agent__.create_rules(server_ip, server_port, router_port, gateway)
                        prerouting_chain.delete_rule(prerouting_rule)
                        postrouting_chain.delete_rule(postrouting_rule)
			nat.close()
                        nat._cache.clear()

	# add port nat fucntion
	@staticmethod
	def add_nat (server_ip, router_id, create_server_port, gateway):

		try:
			assert isinstance(int(create_server_port), int), 'Argument of wrong type!'
			# get server_nat_ports , mapping_ports , router_nat_ports 
			server_nat_ports , mapping_ports, router_nat_ports = NatAgent.__agent__.router_pat_query(router_id)
		
			# add 
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
			
    			else:
        			router_port = str(randint(4000,4100))
        			# check len router_nat_ports if full will make error
        			while router_port in router_nat_ports:
                			router_port = str(randint(4000,4100))
			
				NatAgent.__agent__.add_pat(server_ip, router_id, create_server_port, router_port,gateway)
				
				response = {
					'status' : 'SUCCESS',
					'create_router_port': router_port,	
					'server_ip': server_ip,
					'create_server_port' : create_server_port,
					'gateway': gateway,
					'message': 'Create PAT successfully'
				}

		except Exception as e:
			print(e)
			response = { 'status': 'ERROR', 'message': e }
		finally:
			return response	

	# remove port nat funtion
	@staticmethod
        def remove_nat (server_ip, router_id, remove_server_port, gateway):

		try:
			assert isinstance(int(remove_server_port), int), 'Argument of wrong type!'
			# get server_nat_ports , mapping_ports , router_nat_ports 
                	server_nat_ports , mapping_ports, router_nat_ports = NatAgent.__agent__.router_pat_query(router_id)
			if ( server_ip in server_nat_ports) and ( remove_server_port in server_nat_ports[server_ip]):
				mapping = server_ip + ':' + remove_server_port
				NatAgent.__agent__.remove_pat(server_ip, router_id, remove_server_port, mapping_ports[mapping],gateway)
				response = {
                                        'status' : 'REMOVED',
                                        'remove_router_port': mapping_ports[mapping],
                                        'server_ip': server_ip,
                                        'remove_server_port' : remove_server_port,
                                        'gateway': gateway,
					'message': 'Remove PAT successfully'
                                }
			else:
				response = {
                                        'status' : 'NO CREATED',
                                        'remove_server_port': remove_server_port,
                                        'server_ip': server_ip,
                                        'gateway': gateway,
					'message': 'The remove port has not been PAT yet'
                                }
		except Exception as e:
			#print(e)
			response = { 'status': 'ERROR', 'message': e }
		finally: 
			return response
	# modify port nat function
	@staticmethod
	def modify_nat(server_ip, router_id, modify_server_port, modify_router_port, gateway):

		try:
			# get server_nat_ports , mapping_ports , router_nat_ports 
                	server_nat_ports , mapping_ports, router_nat_ports = NatAgent.__agent__.router_pat_query(router_id)
			if (server_ip not in server_nat_ports) or (modify_server_port not in server_nat_ports[server_ip]) :
				response = {
                                        'status' : 'NO CREATED',
                                        'server_ip': server_ip,
                                        'modify_server_port' : modify_server_port,
                                        'gateway': gateway,
					'message': 'Server port has not PAT yet'
                                }
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
			else:
				mapping = server_ip + ':' + modify_server_port
				NatAgent.__agent__.remove_pat(server_ip, router_id, modify_server_port, mapping_ports[mapping], gateway)
				NatAgent.__agent__.add_pat(server_ip, router_id, modify_server_port, modify_router_port, gateway)
				response = {
                                        'status' : 'SUCCESS',
                                        'modified_router_port': mapping_ports[mapping],
					'modify_router_port': modify_router_port,
                                        'server_ip': server_ip,
                                        'modify_server_port' : modify_server_port,
                                        'gateway': gateway,
					'message': "Modify PAT successfully"
                                }
		except Exception as e:
			#print(e)
			response = { 'status': 'ERROR',  'message': e  }
		finally:
			return response
