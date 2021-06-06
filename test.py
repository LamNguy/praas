from  configparser import ConfigParser
config = ConfigParser()
config.read('config')
print(config['openstack']['auth_url'])
