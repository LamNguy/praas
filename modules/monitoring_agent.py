import netns
from pyroute2 import NSPopen
import iptc
from ctypes import cdll
import pyroute2
libc = cdll.LoadLibrary('libc.so.6')
setns = libc.setns
CLONE_NEWNET = 0x40000000
class MonitorAgent:

	__agent__ = None
	
	def __init__ (self,conn):
		if MonitorAgent.__agent__ is None:
			MonitorAgent.__agent__ = self
		else:
			raise Exception('You are allowed to create only one Agent')

		self.conn = conn

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
				print(dst)
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
	def start_monitoring (ns):
		MonitorAgent.__agent__.check_namespace(ns)
		MonitorAgent.__agent__.check_server_exist(ns)

	@staticmethod
	def check_server_exist( ns ):
		vm_ports, mapping_ports, router_ports = MonitorAgent.__agent__.router_ports_querry( ns )
		if not bool (vm_ports):
			return 
		for key,value in vm_ports.items():
			server_check = MonitorAgent.__agent__.check_vm_life_cycle(key)	
			if server_check is False:
				for port in vm_ports[key]:
					mapping = key + ':' + port
					MonitorAgent.__agent__.remove_rule(key,ns,port,mapping_ports[mapping])
			else:
				print('VM existed')
		

	@staticmethod
	def check_vm_life_cycle(server_ip_address):
                ports = MonitorAgent.__agent__.conn.network.ports()
                port = next((i for i in ports if i['fixed_ips'][0]['ip_address'] == server_ip_address),None)
		
		check = False if port is None else True
                return check 

	@staticmethod
	def get_namespaces():
		return [ 'qrouter-' + i.id for i in MonitorAgent.__agent__.conn.network.routers() ]

	
	@staticmethod
        def remove_rule(server, namespace, vmport, router_port):
                with netns.NetNS(nsname= namespace):
			nat = iptc.Table(iptc.Table.NAT)
                        prerouting_chain = iptc.Chain( nat ,"custom-PREROUTING")
                        postrouting_chain = iptc.Chain(iptc.Table(iptc.Table.NAT),"custom-POSTROUTING")
                        prerouting_rule, postrouting_rule = MonitorAgent.__agent__.create_rules(server, vmport, router_port)
                        prerouting_chain.delete_rule(prerouting_rule)
                        postrouting_chain.delete_rule(postrouting_rule)
			nat.close()
                        nat._cache.clear()

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

	@staticmethod
	def check_namespace( _ns_ ):
		try:
			pyroute2.netns.setns(_ns_)
			print( _ns_)
			with NSPopen( _ns_ ,['true']) as proc:

                                nat = iptc.Table(iptc.Table.NAT)
                                check_custom_prerouting = next((i for i in nat.chains if i.name == 'custom-PREROUTING'),None)
                                check_custom_postrouting = next((i for i in nat.chains if i.name == 'custom-POSTROUTING'),None)

                                if check_custom_prerouting is None:
                                        print('custom-prerouting false')
                                       	nat.create_chain('custom-PREROUTING')
				else:
					print('custom-pre true')
                                if check_custom_postrouting is None:
                                        print('custom-post-routing false')
                                       	nat.create_chain('custom-POSTROUTING')
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

