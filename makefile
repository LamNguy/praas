.PHONY: all install uninstall
lib_dir=/usr/local/lib/praas
conf_dir=/usr/local/etc/praas
log_dir=/var/log/praas
service_dir=/etc/systemd/system

install: 

	@echo Installing the service files...
	-cp services/praas-pat-agent.service $(service_dir)
	-chown root:root $(service_dir)/praas-pat-agent.service
	-chmod 644 $(service_dir)/praas-pat-agent.service
	-cp services/praas-monitor-agent.service $(service_dir)
	-chown root:root $(service_dir)/praas-monitor-agent.service
	-chmod 644 $(service_dir)/praas-monitor-agent.service

	@echo Installing library files...
	-mkdir -p $(lib_dir)
	-cp lib/pat_service.py $(lib_dir)
	-cp lib/monitor_service.py $(lib_dir)
	-cp -R modules $(lib_dir)
	-chown root:root $(lib_dir)/pat_service.py
	-chmod 644 $(lib_dir)/pat_service.py
	-chown root:root $(lib_dir)/monitor_service.py
	-chmod 644 $(lib_dir)/monitor_service.py

	@echo Create log files...
	-mkdir -p $(log_dir)

	@echo Create config files...
	-mkdir -p $(conf_dir)
	-cp config/clouds.yaml $(conf_dir)	
	-cp config/praas.conf $(conf_dir)
	-systemctl daemon-reload
	
uninstall:

	-systemctl stop praas-monitor-agent.service
	-systemctl disable praas-monitor-agent.service
	-systemctl stop praas-pat-agent.service
	-systemctl disable praas-pat-agent.service
	-rm  $(service_dir)/praas-monitor-agent.service
	-rm  $(service_dir)/praas-pat-agent.service
	-systemctl daemon-reload
	-rm -r $(lib_dir)
	-rm -r $(conf_dir)
	-rm -r $(log_dir)
	-echo Uninstall service susccesfully
