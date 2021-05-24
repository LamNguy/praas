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
	def router_ports_querry( _nsname_ ):
		with netns.NetNS(nsname= _nsname_):
                        prerouting = iptc.easy.dump_chain('nat','custom-PREROUTING',ipv6=False)
                        postrouting = iptc.easy.dump_chain('nat','custom-POSTROUTING',ipv6=False)
                        vm_ports = {}
                        mapping_ports = {}
                        router_ports = []
                        # list vm_port which vm opened (vms)
                        for rule in postrouting:
                                dst = rule['dst']
                                dst = dst[:-3]
                                if dst in vm_ports:
                                        vm_ports[dst].append(rule['tcp']['dport'])
                                else:
                                        vm_ports[dst] = []
                                        vm_ports[dst].append(rule['tcp']['dport'])

                        for rule in prerouting:
                                src = rule['target']['DNAT']['to-destination']
                                dport = rule['tcp']['dport']
                                # the port which router opened (vmy)
                                router_ports.append(dport)
                                # mapping the vm_port_opened with router_port_opened
                                mapping_ports[src] = dport
                        return vm_ports, mapping_ports, router_ports

	@staticmethod
        def show_router_port(router):
                server_ports , mapping_ports, router_ports = NatAgent.__agent__.router_ports_querry(router)
                return mapping_ports

	@staticmethod
	def show_server_router_port_mapping( router , server):
		server_ports, mapping_ports , router_ports = NatAgent.__agent__.router_ports_querry(router)
		response = {}
		if server in server_ports:
			for vmport in server_ports[server]:
				mapping = server + ':' + vmport
				response[vmport] = mapping_ports[mapping]	
		return response
		

	@staticmethod
        def create_rules(server, vmport, router_port):
                dst = server + ':' +  vmport
                prerouting_rule = iptc.Rule()
                prerouting_rule.protocol ="tcp"
                match = iptc.Match(prerouting_rule, "tcp")
                match.dport = router_port 
                target = prerouting_rule.create_target("DNAT")
                target.to_destination = dst
                prerouting_rule.add_match(match)
                prerouting_rule.target = target

                postrouting_rule = iptc.Rule()
                postrouting_rule.protocol ="tcp"
                postrouting_rule.dst = server 
                match = iptc.Match(postrouting_rule, "tcp")
                match.dport = vmport
                postrouting_rule.add_match(match)
                postrouting_rule.target = iptc.Target(postrouting_rule,"MASQUERADE")
		return prerouting_rule, postrouting_rule

	# add port address translation processing
	@staticmethod
        def add_pat(server, router, vmport, router_port, gateway):
                with netns.NetNS(nsname= router):
			nat = iptc.Table(iptc.Table.NAT)
                        prerouting_chain = iptc.Chain( nat ,"custom-PREROUTING")
                        postrouting_chain = iptc.Chain( nat ,"custom-POSTROUTING")
			prerouting_rule, postrouting_rule = NatAgent.__agent__.create_rules(server, vmport, router_port)
			prerouting_chain.insert_rule(prerouting_rule)
                        postrouting_chain.insert_rule(postrouting_rule)
			nat.close()
			nat._cache.clear()

	# port address translation processing
	@staticmethod
	def remove_pat(server, router, vmport, router_port, gateway):
		with netns.NetNS(nsname= router):
			nat = iptc.Table(iptc.Table.NAT)
                        prerouting_chain = iptc.Chain( nat ,"custom-PREROUTING")
                        postrouting_chain = iptc.Chain( nat ,"custom-POSTROUTING")
                        prerouting_rule, postrouting_rule = NatAgent.__agent__.create_rules(server, vmport, router_port)
                        prerouting_chain.delete_rule(prerouting_rule)
                        postrouting_chain.delete_rule(postrouting_rule)
			nat.close()
                        nat._cache.clear()

	# add port nat fucntion
	@staticmethod
	def add_nat (server, router, vmport, gateway):

		try:
			assert isinstance(int(vmport), int), 'Argument of wrong type!'
			# get vm_ports , mapping_ports , router_ports 
			vm_ports , mapping_ports, router_ports = NatAgent.__agent__.router_ports_querry(router)
		
			# add 
			if (server in vm_ports) and (vmport in vm_ports[server]):
        			mapping = server + ':' + vmport
				response = {
					'status': 'CREATED',
					'created_server_port': vmport,
					'created_router_port': mapping_ports[mapping],
					'server_ip': server,
					'gateway': gateway,
					'message': 'Server port has been PAT already'
				}
			
    			else:
        			router_port = str(randint(4000,4100))
        			# check len router_ports if full will make error
        			while router_port in router_ports:
                			router_port = str(randint(4000,4100))
			
				NatAgent.__agent__.add_pat(server, router, vmport, router_port, gateway)
				
				response = {
					'status' : 'SUCCESS',
					'create_router_port': router_port,	
					'server_ip': server,
					'create_server_port' : vmport,
					'gateway': gateway,
					'message': 'Create PAT successfully'
				}

		except Exception as e:
			print(e)
			response = { 'status': 'ERROR', 'message': 'Wrong type input' }
		finally:
			return response	

	# remove port nat funtion
	@staticmethod
        def remove_nat (server, router, vmport, gateway):

		try:
			assert isinstance(int(vmport), int), 'Argument of wrong type!'
			# get vm_ports , mapping_ports , router_ports 
                	vm_ports , mapping_ports, router_ports = NatAgent.__agent__.router_ports_querry(router)
			if ( server in vm_ports) and ( vmport in vm_ports[server]):
				mapping = server + ':' + vmport
				NatAgent.__agent__.remove_pat(server, router, vmport, mapping_ports[mapping], gateway)
				response = {
                                        'status' : 'REMOVED',
                                        'remove_router_port': mapping_ports[mapping],
                                        'server_ip': server,
                                        'remove_server_port' : vmport,
                                        'gateway': gateway,
					'message': 'Remove PAT successfully'
                                }
			else:
				response = {
                                        'status' : 'NO CREATED',
                                        'remove_server_port': vmport,
                                        'server_ip': server,
                                        'gateway': gateway,
					'message': 'The remove port has not been PAT yet'
                                }
		except Exception as e:
			print(e)
			response = { 'status': 'ERROR', 'message': 'Wrong type input' }
		finally: 
			return response
	# modify port nat function
	@staticmethod
	def modify_nat(server, router, vmport, new_router_port, gateway):

		try:
			# get vm_ports , mapping_ports , router_ports 
                	vm_ports , mapping_ports, router_ports = NatAgent.__agent__.router_ports_querry(router)
			if (server not in vm_ports) or (vmport not in vm_ports[server]) :
				response = {
                                        'status' : 'NO CREATED',
                                        'server_ip': server,
                                        'modify_server_port' : vmport,
                                        'gateway': gateway,
					'message': 'Server port has not PAT yet'
                                }
			elif new_router_port in router_ports:
				mapping = server + ':' + vmport
				response = {
                                        'status' : 'USED',
					'modified_router_port': mapping_ports[mapping],
                                        'server_ip': server,
                                        'modify_server_port' : vmport,
					'modify_router_port': new_router_port,
                                        'gateway': gateway,
					'message': "New router port has been used already"
                                }
			else:
				mapping = server + ':' + vmport
				NatAgent.__agent__.remove_pat(server, router, vmport, mapping_ports[mapping], gateway)
				NatAgent.__agent__.add_pat(server, router, vmport, new_router_port, gateway)
				response = {
                                        'status' : 'SUCCESS',
                                        'modified_router_port': mapping_ports[mapping],
					'modify_router_port': new_router_port,
                                        'server_ip': server,
                                        'modify_server_port' : vmport,
                                        'gateway': gateway,
					'message': "Modify PAT successfully"
                                }
		except Exception as e:
			print(e)
			response = { 'status': 'ERROR',  'message': 'Wrong type input' }
		finally:
			return response
