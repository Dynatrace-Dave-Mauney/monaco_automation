"""
Create Monaco YAML and JSON based on a "Meta YAML" file.
"""

import yaml

k8s_cluster_id_lookup = {}


def get_meta():
	with open('meta.yaml', 'r') as file:
		document = file.read()
		return yaml.load(document, Loader=yaml.FullLoader)


def generate_monaco_configuration_file():
	meta = get_meta()
	name = 'entities'
	tenant = meta.get('tenant')
	env_url = ''
	env_token_name = ''

	if tenant == '$tenant3$':
		env_url = 'https://$tenant3$.live.dynatrace.com'
		env_token_name = '$tenant3$-token'
	else:
		if tenant == '$tenant2$':
			env_url = 'https://$tenant2$.live.dynatrace.com'
			env_token_name = '$tenant2$-token'
		else:
			if tenant == '$tenant1$':
				env_url = 'https://$tenant1$.live.dynatrace.com'
				env_token_name = '$tenant1$-token'
			else:
				print('Unsupported tenant specified in meta.yaml')
				exit()

	monaco_list = []
	name_dict = {'name': name}
	monaco_list.append(name_dict)

	env_url_dict = {'env-url': env_url}
	monaco_list.append(env_url_dict)

	env_token_dict = {'env-token-name': env_token_name}
	monaco_list.append(env_token_dict)

	# Generate monaco.yaml
	monaco_dict = {'entities': monaco_list}

	with open('monaco.yaml', 'w') as file:
		yaml.dump(monaco_dict, file, sort_keys=False)


def generate_delete_yaml_file():
	meta = get_meta()
	configs = meta.get('configs')

	delete_list = []

	for config in configs:
		name = list(config.keys())[0]
		name_dict = config.get(name)
		apps = name_dict.get('apps', [''])
		app = name_dict.get('app', apps[0])
		env = name_dict.get('env')

		short_env_name = get_short_env_name(env)

		app_name = name + ' (' + app + '_' + env + ')'
		mz_name = 'App: ' + name + ' - ' + short_env_name

		app_detection_rule = 'app-detection-rule/' + app_name
		application_web = 'application-web/' + app_name
		management_zone = 'management-zone/' + mz_name

		delete_list.append(app_detection_rule)
		delete_list.append(application_web)
		delete_list.append(management_zone)

	# Generate delete.yaml
	delete_dict = {'delete': delete_list}

	with open('meta-output/delete.yaml', 'w') as file:
		yaml.dump(delete_dict, file, sort_keys=True)


def generate_management_zone_yaml():
	management_zone_dict = {}
	management_zone_config_list = []
	management_zone_config_name_list = []

	meta = get_meta()
	output_path = 'meta-output/entities'

	management_zone_path = output_path + '/' + 'management-zone'

	management_zone_file_name = management_zone_path + '/' + 'management-zone.yaml'

	configs = meta.get('configs')
	for config in configs:
		name = list(config.keys())[0]
		name_dict = config.get(name)
		app = name_dict.get('app', '')
		apps = name_dict.get('apps', [app])
		env = name_dict.get('env')
		k8s_clusters = name_dict.get('clusters', [])
		short_env_name = get_short_env_name(env)
		mz_name = 'App: ' + name + ' - ' + short_env_name
		config_key = name + '-' + short_env_name

		# Gather management-zone.yaml data
		mz_dict = {config_key: name + env + '.json'}
		management_zone_config_list.append(mz_dict)

		mz_dict = {
			'config': config_key,
			'name': mz_name,
			'apps': apps,
			'env': env,
			'clusters': k8s_clusters
		}
		management_zone_config_name_list.append(mz_dict)

	management_zone_dict['config'] = management_zone_config_list
	for management_zone_config_name in management_zone_config_name_list:
		config_list = []
		config_name = management_zone_config_name.get('config')
		name = management_zone_config_name.get('name')
		apps = management_zone_config_name.get('apps')
		env = management_zone_config_name.get('env')
		k8s_clusters = management_zone_config_name.get('clusters')
		name_dict = {'name': name}
		config_list.append(name_dict)
		env_dict = {'env': env}
		config_list.append(env_dict)
		suffix = 1
		for app in apps:
			app_name = 'app' + str(suffix)
			app_dict = {app_name: app}
			config_list.append(app_dict)
			management_zone_dict[config_name] = config_list
			suffix += 1
		suffix = 1
		for k8s_cluster in k8s_clusters:
			cluster_name = 'cluster_name' + str(suffix)
			cluster_dict = {cluster_name: k8s_cluster}
			config_list.append(cluster_dict)
			cluster_id_name = 'cluster_id' + str(suffix)
			cluster_id_dict = {cluster_id_name: get_k8s_cluster_id(k8s_cluster)}
			config_list.append(cluster_id_dict)
			management_zone_dict[config_name] = config_list
			suffix += 1

	with open(management_zone_file_name, 'w') as file:
		yaml.dump(management_zone_dict, file, sort_keys=False)


# TODO: Clean up this self-contained hack!!
def get_k8s_cluster_id(k8s_cluster):
	global k8s_cluster_id_lookup
	env_url = ''
	env_token = ''

	if k8s_cluster_id_lookup == {}:
		import dynatrace_rest_api_helper

		meta = get_meta()
		tenant = meta.get('tenant')

		if tenant == '$tenant3$':
			env_url = 'https://$tenant3$.live.dynatrace.com'
			env_token = '$entity_token3$'
		else:
			if tenant == '$tenant2$':
				env_url = 'https://$tenant2$.live.dynatrace.com'
				env_token = '$entity_token2$'
			else:
				if tenant == '$tenant1$':
					env_url = 'https://$tenant1$.live.dynatrace.com'
					# env_token = '$entity_token1$'
					env_token = '$entity_token1$'
				else:
					print('Unsupported tenant specified in meta.yaml')
					exit()

		# Load all k8s clusters from k8s integration list
		endpoint = '/api/config/v1/kubernetes/credentials'
		params = ''
		kubernetes_credentials_json_list = dynatrace_rest_api_helper.get_rest_api_json(env_url, env_token, endpoint, params)
	
		for kubernetes_credentials_json in kubernetes_credentials_json_list:
			inner_kubernetes_credentials_json_list = kubernetes_credentials_json.get('values')
			for inner_kubernetes_credentials_json in inner_kubernetes_credentials_json_list:
				k8s_cluster_id = inner_kubernetes_credentials_json.get('id')
				name = inner_kubernetes_credentials_json.get('name')
				k8s_cluster_id_lookup[name] = k8s_cluster_id

	k8s_cluster_id = k8s_cluster_id_lookup.get(k8s_cluster, '')
	
	return k8s_cluster_id


def generate_application_web_yaml():
	application_web_dict = {}
	application_web_config_list = []
	application_web_config_name_list = []

	meta = get_meta()
	output_path = 'meta-output/entities'

	application_web_path = output_path + '/' + 'application-web'

	application_web_file_name = application_web_path + '/' + 'application-web.yaml'

	configs = meta.get('configs')
	for config in configs:
		name = list(config.keys())[0]
		name_dict = config.get(name)
		apps = name_dict.get('apps', [''])
		app = name_dict.get('app', apps[0])
		env = name_dict.get('env')
		domain = name_dict.get('domain', '')

		if domain != '':
			web_app_name = name + ' (' + app + '_' + env + ')'

			config_key = name + app + env

			# Gather application-web.yaml data
			app_web_dict = {config_key: 'application-web.json'}
			application_web_config_list.append(app_web_dict)

			app_web_dict = {
				'config': config_key,
				'name': web_app_name,
				'app': app,
				'env': env}
			application_web_config_name_list.append(app_web_dict)

		application_web_dict['config'] = application_web_config_list
		for application_web_config_name in application_web_config_name_list:
			config_list = []
			config_name = application_web_config_name.get('config')
			name = application_web_config_name.get('name')
			app = application_web_config_name.get('app')
			env = application_web_config_name.get('env')
			name_dict = {'name': name}
			config_list.append(name_dict)
			app_dict = {'app': app}
			config_list.append(app_dict)
			env_dict = {'env': env}
			config_list.append(env_dict)
			application_web_dict[config_name] = config_list

	if len(application_web_config_list) > 0:
		with open(application_web_file_name, 'w') as file:
			yaml.dump(application_web_dict, file, sort_keys=False)
		return True
	else:
		return False


def generate_app_detection_yaml():
	app_detection_dict = {}
	app_detection_config_list = []
	app_detection_config_name_list = []

	meta = get_meta()
	output_path = 'meta-output/entities'

	app_detection_path = output_path + '/' + 'app-detection-rule'

	app_detection_file_name = app_detection_path + '/' + 'app-detection-rule.yaml'

	configs = meta.get('configs')
	for config in configs:
		name = list(config.keys())[0]
		name_dict = config.get(name)
		domain = name_dict.get('domain', '')
		apps = name_dict.get('apps', [''])
		app = name_dict.get('app', apps[0])
		env = name_dict.get('env')

		if domain != '':
			web_app_name = name + ' (' + app + '_' + env + ')'

			short_env_name = get_short_env_name(env)
			config_key = name + '-' + short_env_name

			# Gather app-detection-rule.yaml data
			app_detect_dict = {config_key: 'app-detection-rule.json'}
			app_detection_config_list.append(app_detect_dict)

			monaco_reference = '/entities/application-web/' + name + app + env + '.id'

			app_detect_dict = {
				'config': config_key,
				'name': web_app_name,
				'id': monaco_reference,
				'pattern': domain
			}
			app_detection_config_name_list.append(app_detect_dict)

	app_detection_dict['config'] = app_detection_config_list
	for app_detection_config_name in app_detection_config_name_list:
		config_list = []
		config_name = app_detection_config_name.get('config')
		name = app_detection_config_name.get('name')
		app_id = app_detection_config_name.get('id')
		pattern = app_detection_config_name.get('pattern')
		name_dict = {'name': name}
		config_list.append(name_dict)
		id_dict = {'id': app_id}
		config_list.append(id_dict)
		pattern_dict = {'pattern': pattern}
		config_list.append(pattern_dict)
		app_detection_dict[config_name] = config_list

	with open(app_detection_file_name, 'w') as file:
		yaml.dump(app_detection_dict, file, sort_keys=False)


def generate_auto_tag_yaml():
	auto_tag_dict = {}
	auto_tag_config_list = []
	auto_tag_config_name_list = []

	output_path = 'meta-output/entities'
	auto_tag_path = output_path + '/' + 'auto-tag'
	auto_tag_file_name = auto_tag_path + '/' + 'auto-tag.yaml'

	# Generate auto-tag.yaml (from thin air!)
	auto_tag_temp_dict = {'Application': 'Application.json'}
	auto_tag_config_list.append(auto_tag_temp_dict)

	auto_tag_temp_dict = {
		'config': 'Application',
		'name': 'Application'}
	auto_tag_config_name_list.append(auto_tag_temp_dict)

	auto_tag_dict['config'] = auto_tag_config_list
	for auto_tag_config_name in auto_tag_config_name_list:
		config_list = []
		config_name = auto_tag_config_name.get('config')
		name = auto_tag_config_name.get('name')
		name_dict = {'name': name}
		config_list.append(name_dict)
		auto_tag_dict[config_name] = config_list

	with open(auto_tag_file_name, 'w') as file:
		yaml.dump(auto_tag_dict, file, sort_keys=False)


def get_short_env_name(long_env_name):
	short_env_names = {'DEVELOPMENT': 'DEV', 'INTEGRATION': 'INT', 'STAGE': 'STAGE', 'PRODUCTION': 'PROD'}
	short_env_name = short_env_names.get(long_env_name)
	return short_env_name


def main():
	# For testing only.
	# Use perform_app_on_boarding_meta_monaco.py to run these steps in the proper sequence for each workflow.
	generate_management_zone_yaml()
	exit()

	generate_app_detection_yaml()
	generate_application_web_yaml()
	generate_auto_tag_yaml()
	generate_delete_yaml_file()
	generate_management_zone_yaml()
	generate_monaco_configuration_file()


if __name__ == '__main__':
	main()
