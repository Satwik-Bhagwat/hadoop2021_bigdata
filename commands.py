import os
import json
from utilities import *
#from termcolor import colored

config_file = open('dfs_setup_config.json','r')
config = json.load(config_file)

no_of_nodes = config['num_datanodes']
replication = config['replication_factor']
block_size = config['block_size']

datanode = os.path.expandvars(config['path_to_datanodes'])
namenode = os.path.expandvars(config['path_to_namenodes'])
fs_path = os.path.expandvars(config['fs_path'])

datanode_path = os.path.join(datanode, 'DataNodes')


def put_command(source, destination):
	user_file = source.split('/')[-1]
	dest_path = os.path.join(destination, user_file)

	#mapping of virtual path and file name
	mapping_file = open(namenode + "mapping_file.json",'r+')
	mapping_data = json.load(mapping_file)

	if not destination in mapping_data:       					#check if destinataion path exists
		mapping_file.close()
		raise Exception(destination,"No such directory")

	mapping_data[destination].append(user_file)
	updateJSON(mapping_data ,mapping_file)

	#file to keep track of where file blocks are stored
	location_file = open(namenode + "location_file.json","r+")
	location_data = json.load(location_file)
	location_data[dest_path] = []

	datanode_tracker = open(namenode + 'datanode_tracker.json', 'r+')
	datanode_details = json.load(datanode_tracker)

	#splitting files to datanodes
	next_datanode = datanode_details['Next_datanode']
	for split in fileSplit(source,block_size):
		replica = []
		for _ in range(replication):
			DN_str = 'DN' + str(next_datanode)
			empty_blk_no = datanode_details[DN_str].index(0)
			block = 'block' + str(empty_blk_no)
			
			datanode_details[DN_str][empty_blk_no] = 1
			next_datanode = (next_datanode % no_of_nodes) + 1

			store_path = DN_str + '/' + block
			replica.append(store_path)

			file_path = os.path.join(datanode_path, store_path)
			file = open(file_path,'w')
			file.write(split)
			file.close()

		location_data[dest_path].append(replica)


	datanode_details['Next_datanode'] = next_datanode

	updateJSON(datanode_details, datanode_tracker)
	updateJSON(location_data, location_file)


def cat_command(path):
	location_file = open(namenode + "location_file.json",'r+')
	location_data = json.load(location_file)

	if not path in location_data:
		location_file.close()
		raise Exception(path, "File does not exist")

	for replica in location_data[path]:
		for file_blk in replica:
			block_path = os.path.join(datanode, 'DataNodes', file_blk)
			if os.path.isfile(block_path):
				content = open(block_path, 'r').read()
				print(content, end='')
				break
	

def ls_command(path):
	mapping_file = open(namenode + "mapping_file.json",'r')
	mapping_data = json.load(mapping_file)
	
	#directory doesn't exist
	if not path in mapping_data:
		mapping_file.close()
		raise Exception(path,"No such directory")

	for entry in mapping_data[path]:
		if (path + entry) in mapping_data:
			print(entry, "\tDirectory")
			#print(colored(entry,'blue'))
		else:
			print(entry, "\tfile")

	mapping_file.close()


def rmdir_command(path):
	split = os.path.split(path)
	par_path, user_dir = split[0], split[1]

	mapping_file = open(namenode + "mapping_file.json",'r+')
	mapping_data = json.load(mapping_file)
	
	#directory doesn't exist
	if not path in mapping_data:
		mapping_file.close()
		raise Exception(path,"No such directory")

	if len(mapping_data[path]) != 0:								#check for any file/dir in path
		mapping_file.close()
		raise Exception(path,"Directory is not empty")

	del mapping_data[path]
	
	#deleting entry in parent directory
	if par_path in mapping_data:
		mapping_data[par_path].remove(user_dir)


	updateJSON(mapping_data, mapping_file)


def mkdir_command(path):
	split = os.path.split(path)
	par_path, user_dir = split[0], split[1]

	mapping_file = open(namenode + "mapping_file.json",'r+')
	mapping_data = json.load(mapping_file)
	
	#have to create parent directory before creating subdirectory
	if not par_path in mapping_data:
		mapping_file.close()
		raise Exception(par_path,"No such directory")

	#appends subdirectory to parent directory
	mapping_data[par_path].append(user_dir)
	mapping_data[path] = []

	updateJSON(mapping_data, mapping_file)
	

def rm_command(path):
	split = os.path.split(path)
	par_path, file = split[0], split[1]

	location_file = open(namenode + "location_file.json",'r+')
	location_data = json.load(location_file)

	if not path in location_data:
		location_file.close()
		raise Exception(path, "File does not exist")


	datanode_tracker = open(namenode + 'datanode_tracker.json', 'r+')
	datanode_details = json.load(datanode_tracker)

	for replica in location_data[path]:
		for file_blk in replica:
			DN_str, block = file_blk.split('/')
			block = int(block[5:])									#getting the block number

			datanode_details[DN_str][block] = 0

			block_path = os.path.join(datanode, 'DataNodes', file_blk)
			os.remove(block_path)

	del location_data[path]

	mapping_file = open(namenode + "mapping_file.json",'r+')
	mapping_data = json.load(mapping_file)
	mapping_data[par_path].remove(file)

	updateJSON(mapping_data, mapping_file)
	updateJSON(location_data, location_file)
	updateJSON(datanode_details, datanode_tracker)
