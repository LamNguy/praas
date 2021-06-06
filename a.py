import iptc
rule_goto = { 'target':  'custom-PREROUTING'}
iptc.easy.insert_rule('nat','PREROUTING',rule_goto)
