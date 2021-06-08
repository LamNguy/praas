from setuptools import setup, find_packages
with open ("README.md", "r") as f:
	readme = f.read()

setup(
    name='praas',
    version='0.0.1',
    author='Nguyen Duc Lam',
    author_email='lamchipabc@gmail.com',
    description='Proxy Service integrated with OpenStack',
    long_description_content_type="text/markdown",
    url = 'https://github.com/LamNguy/proxy_pat_agents',
    python_requires='>=2.7, <=3.*',
    packages=find_packages(),
    scripts=['praas-install','praas-uninstall'],
    include_package_data=True,
    install_requires= [
	'configparser',
	'pbr',
	'python-iptables',
	'Flask==1.1.2',
	'netns',
	'openstacksdk==0.36.5'], 
)
