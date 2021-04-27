import iptc
import netns
with netns.NetNS(nsname= 'qrouter-03b72092-e8bb-473e-b671-e1dce6c4b73d'):
	prerouting_chain = iptc.Chain(iptc.Table(iptc.Table.NAT),"custom-PREROUTING")
	prerouting_chain.close()
        prerouting_chain.clear()
