import os
import json

def init_DFS(config_file_path = 'default_config.json'):
	config_file = open(config_file_path)
	config = json.load(config_file)

	datanode = os.path.expandvars(config['path_to_datanodes'])
	namenode = os.path.expandvars(config['path_to_namenodes'])
	
	os.mkdir(datanode)
	os.mkdir(namenode)
	
	directory = 'DataNodes'
	cur_path = os.path.join(datanode, directory)
	os.mkdir(cur_path)
	
	no_of_nodes = config['num_datanodes']
	for i in range(no_of_nodes):
		dirname = 'DN' + str(i+1)
		path = os.path.join(cur_path, dirname)
		os.mkdir(path)

init_DFS('config_sample.json')
