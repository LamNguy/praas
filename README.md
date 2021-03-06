# Proxy as a Service - Thesis graduation project
## _Proxy service PAT for OpenStack_
The project separated into two part, including Proxy CLI and Proxy as a Service (PRaaS) and the part here is for PraaS. 
PRaaS is a service which is integrated in OpenStack. It use Port Address Translation (PAT) technique, also as port forwarding. For details, it enables the connection from external to virtual machines in a tenant network through only the gateway and specified port of router which is associated betwwen the provider and tenant networks.  

## Features
- Manage PAT information on project routers in OpenStack
- Receive request from Proxy CLI and handles PAT operations such as creating, removing and modifying.
- Monitor the status of virtual machines which were establised connection by PraaS every 30s and update the PAT connection of deleted or ip-changed virtual machines in OpenStack.

#### 1. Prerequisite
- Python virtual environment such as __*virtualenv*__ or __*anaconda*__. (optional)
- Python >= 2.7
#### 2. Installation
PRaaS use python interpreter in the current environment. Use virtual environment is a safe and low-risk aprroach for not conflicting and the virtual python interpreter will be choosen. The guide using tool python __*virtualenv*__ for creating environment.

__Install virtualenv__
```
$ pip install virtualenv
```
__Create virtual python env__
```
$ virtualenv myenv
```
__Activate env__
```
$ source myenv/bin/activate
```
__Deactivate env__
```
$ deactivate
```
__Clone the project__
```
$ git clone https://github.com/LamNguy/praas 
```
__Install packages__
```
$ cd praas
$ pip install -e .
```
__If the install fail due to missing package "pbr", install it and re-run install packages__
```
$ pip install pbr
```
__Install service (required in the folder project)__
```
$ praas-install
```
__Uninstall service (required in the folder project)__
```
$ praas-uninstall
```
#### 3. Configuration
PRaaS is installed on system including:
- Log file: _/var/log/praas_
- Library: _/usr/local/lib/praas_
- Config file: _/usr/local/etc/praas_
- Service file: _/etc/systemd/system_

__Edit config file__
_Config PRaaS if needs customizing_
```
# praas.conf
[praas]
port_app = 3000 #RESTful API default run on port 3000
router_port_range = 4000:4100 #Specific router port range using for pat agent
second_monitoring = 30 #Specific period working of monitor agent.
```
_Config to auto login OpenStack for PRaaS_
```
# clouds.yaml
clouds:
  openstack:
    auth:
      auth_url: http://controller:5000/v3/  #specific ip or hostname of controller
      username: "admin"
      password: "xxx"
      project_name: "admin"
      project_domain_name: 'Default'
      user_domain_name: "Default"
    region_name: "RegionOne"
    interface: "public"
    identity_api_version: 3
```
#### 4. Start PRaaS services
PRaaS include __*PAT agent service*__ and __*Monitor agent service*__
```
$ systemctl start praas-pat-agent.service
$ systemctl status praas-pat-agent.service
```
```
$ systemctl start praas-monitor-agent.service
$ systemctl status praas-monitor-agent.service
```
#### 5. Notes
```
# create user define-chain which referenced to postrouting and prerouting to avoid conflicting
sudo iptables -t nat -N custom-PREROUTING
sudo iptables -t nat -N custom-POSTROUTING
sudo iptables -t nat -I PREROUTING -j custom-PREROUTING
sudo iptables -t nat -I POSTROUTING -j custom-POSTROUTING

# commandline to create rules in examples
iptables -t nat -A custom-PREROUTING -p tcp -m tcp --dport 4022 -j DNAT --to 192.168.21.227:22
iptables -t nat -A custom-POSTROUTING -p tcp -m tcp --dport 22 -d 192.168.21.227 -j MASQUERADE
```
