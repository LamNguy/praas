import netns
import requests
import iptc

class MonitorAgent:

	__agent__ = None
	logger = None
	def __init__ (self,conn,logger):
		if MonitorAgent.__agent__ is None:
			MonitorAgent.__agent__ = self
			MonitorAgent.logger = logger
		else:
			raise Exception('You are allowed to create only one Agent')

		self.conn = conn

	@staticmethod
        def router_ports_querry( router_id ):
                with netns.NetNS( nsname = router_id):
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
	def monitoring ():
		namespaces = MonitorAgent.__agent__.get_routers() 
		for namespace in namespaces:
			# get gateway
			gateway = MonitorAgent.__agent__.conn.network.get_router(namespace).external_gateway_info['external_fixed_ips'][0]['ip_address']
			server_nat_ports, mapping_ports, router_nat_ports = MonitorAgent.__agent__.router_ports_querry(  'qrouter-' +  namespace )

                	if not bool (server_nat_ports): continue 

                	for server_ip,server_ports in server_nat_ports.items():
                        	check = MonitorAgent.__agent__.check_server_life_cycle(server_ip)
                        	if check is False:
					MonitorAgent.logger.info('Detect server with ip {} is deleted, so remove all its pat connection'.format(server_ip))
                                	for port in server_nat_ports[server_ip]:
                                        	mapping = server_ip + ':' + port
                                        	MonitorAgent.__agent__.remove_pat_request(server_ip,namespace,port,gateway)
                        	else:
                                	MonitorAgent.logger.info('VM existed')

	@staticmethod
	def check_server_life_cycle(server_ip):
                ports = MonitorAgent.__agent__.conn.network.ports()
                port = next((i for i in ports if i['fixed_ips'][0]['ip_address'] == server_ip),None)
		check = False if port is None else True
                return check 

	@staticmethod
	def get_namespaces():
		return [ 'qrouter-' + i.id for i in MonitorAgent.__agent__.conn.network.routers() ]

	@staticmethod
        def get_routers():
                return [  i.id for i in MonitorAgent.__agent__.conn.network.routers() ]


	@staticmethod
	def remove_pat_request (server_ip, router_id, remove_server_port, gateway):
		payload = {
                	'server_ip': server_ip,
                        'router_id': 'qrouter-' + router_id,
                        'remove_server_port': remove_server_port,
                        'gateway': gateway 
                }
               
		url = 'http://192.168.0.105:3000/pat/remove'

                response = requests.post(url = url, params = payload).json()	
		print(response)

	@staticmethod
	def check_namespace( _ns_ ):
		try:
			with netns.NetNS( nsname = _ns_): 

                                nat = iptc.Table(iptc.Table.NAT)
                                check_custom_prerouting = next((i for i in nat.chains if i.name == 'custom-PREROUTING'),None)
                                check_custom_postrouting = next((i for i in nat.chains if i.name == 'custom-POSTROUTING'),None)

                                if check_custom_prerouting is None:
                                        print('custom-prerouting false')
                                       	#nat.create_chain('custom-PREROUTING')
				else:
					print('custom-pre true')
                                if check_custom_postrouting is None:
                                        print('custom-post-routing false')
                                       	#nat.create_chain('custom-POSTROUTING')
				else:
					print('custom-pos true')

                                pre_chain = iptc.Chain(iptc.Table(iptc.Table.NAT), "PREROUTING")
                                post_chain = iptc.Chain(iptc.Table(iptc.Table.NAT), "POSTROUTING")
                                check_prerouting = next(( i for i in pre_chain.rules if i.target.name == 'custom-PREROUTING'),None)
                                check_postrouting = next(( i for i in post_chain.rules if i.target.name == 'custom-POSTROUTING'),None)

                                if check_prerouting is None:
                                       print('check prerouting jump false')
                                       #rule_goto = { 'target': {'goto': 'custom-PREROUTING'}}
                                       #iptc.easy.insert_rule('nat','PREROUTING',rule_goto)
				else:
					print('check prerouting jump true')
                                if check_postrouting is None:
                                        print('check postrouting jump false')
                                        #rule_goto = { 'target': {'goto': 'custom-POSTROUTING'}}
                                        #iptc.easy.insert_rule('nat','POSTROUTING',rule_goto)
				else:
					print('check postrouting jump true')
				nat.close()
                                nat._cache.clear()

                except Exception as e:
                        print(e) 

