import json
import sys
import dynatrace_rest_api_helper
import copy

# # UWM LOWER
# tenant_name = 'UWM LOWER'
# env = 'https://sdx86737.live.dynatrace.com'
# token = '$entity_token2$'
#
# UWM SANDBOX
# tenant_name = 'UWM SANDBOX'
# env = 'https://fqz97080.live.dynatrace.com'
# token = '$entity_token3$'
#
# UWM UPPER
tenant_name = 'UWM UPPER'
env = '  https://bmk57446.live.dynatrace.com'
token = '$entity_token1$'


def process(env, token):
    k8s_clusters = {}
    environments = []
    cloud_types = []

    # Load all k8s clusters from k8s integration list
    endpoint = '/api/config/v1/kubernetes/credentials'
    params = ''
    kubernetes_credentials_json_list = dynatrace_rest_api_helper.get_rest_api_json(env, token, endpoint, params)

    for kubernetes_credentials_json in kubernetes_credentials_json_list:
        inner_kubernetes_credentials_json_list = kubernetes_credentials_json.get('values')
        for inner_kubernetes_credentials_json in inner_kubernetes_credentials_json_list:
            id = inner_kubernetes_credentials_json.get('id')
            name = inner_kubernetes_credentials_json.get('name')
            k8s_clusters[name] = {'id': id, 'cloudType': [], 'environment': [], 'data_center': []}

    # print('k8s clusters from integrations')
    # print(k8s_clusters)

    # Fill in details for k8s clusters from host list
    endpoint = '/api/v2/entities'
    params = 'pageSize=4000&entitySelector=type%28%22HOST%22%29&to=-5m&fields=properties%2Ctags'
    entities_json_list = dynatrace_rest_api_helper.get_rest_api_json(env, token, endpoint, params)
    for entities_json in entities_json_list:
        inner_entities_json_list = entities_json.get('entities')
        for inner_entities_json in inner_entities_json_list:
            display_name = inner_entities_json.get('displayName')
            properties = inner_entities_json.get('properties')
            cloud_type = properties.get('cloudType', 'TANZU')
            tags = inner_entities_json.get('tags', [])
            k8s_cluster = 'NONE'
            environment = 'NONE'
            data_center = 'NONE'
            for tag in tags:
                if "Kubernetes Cluster" in str(tag):
                    k8s_cluster = tag.get('value')
                if "Environment" in str(tag):
                    environment = tag.get('value', 'NONE')
                    if environment == '2':
                        environment = 'NONE'
                    environment = environment.upper()
                    if environment not in environments:
                        environments.append(environment)
                if "Data Center" in str(tag):
                    data_center = tag.get('value')

            if k8s_cluster != 'NONE':
                if k8s_cluster not in k8s_clusters:
                    k8s_clusters[k8s_cluster] = {'cloudType': [cloud_type], 'environment': [environment], 'data_center': [data_center]}
                else:
                    dict = k8s_clusters[k8s_cluster]
                    if cloud_type not in dict['cloudType']:
                        dict['cloudType'].append(cloud_type)
                    if environment not in dict['environment']:
                        dict['environment'].append(environment)
                    if data_center not in dict['data_center']:
                        dict['data_center'].append(data_center)
                    if cloud_type not in cloud_types:
                        cloud_types.append(cloud_type)

    # print('k8s clusters augmented with details from hosts')
    # print(k8s_clusters)

    print('Environments: ' + str(environments))
    print('Cloud Types: ' + str(cloud_types))

    generate_json(k8s_clusters, tenant_name)

def get_management_zone_template():
    with open('management_zone_template.json', 'r', encoding='utf-8') as file:
        management_zone_template_string = file.read()
        management_zone_template = json.loads(management_zone_template_string)
        return management_zone_template


def write_management_zone(filename, management_zone):
    with open(filename, 'w') as file:
        file.write(json.dumps(management_zone, indent=4, sort_keys=False))


def generate_json(k8s_clusters, tenant_name):
    environment_mz_name = {'development': 'Dev', 'integration': 'Int', 'stage': 'Stage', 'production': 'Prod', 'prod': 'Prod'}
    platform_mz_name = {'azure': 'AKS', 'google_cloud_platform': 'GKE', 'tanzu': 'Tanzu',
                        'unknown_cloud_type': 'Unknown_Cloud_Platform'}
    datacenter_mz_name = {'pontiac': 'Pon', 'grand rapids': 'GR', 'tanzu': 'Tanzu'}

    filename_prefix = 'k8s_mz_' + tenant_name + '_'
    filename_prefix_environment = filename_prefix + 'environment_'
    filename_prefix_platform = filename_prefix + 'platform_'
    filename_prefix_platform_environment = filename_prefix + 'platform_environment_'
    filename_prefix_datacenter = filename_prefix + 'datacenter_'
    filename_prefix_datacenter_environment = filename_prefix + 'datacenter_environment_'

    filename_all = filename_prefix + 'all.json'

    management_zone_template = get_management_zone_template()

    dimensional_rules_template = management_zone_template.get('dimensionalRules')
    rules_template = management_zone_template.get('rules')

    output_dict = {}

    for cluster_name in sorted(k8s_clusters.keys()):
        k8s_cluster_id = k8s_clusters[cluster_name]['id']
        k8s_cluster_environment_list = k8s_clusters[cluster_name]['environment']
        k8s_cluster_cloud_type_list = k8s_clusters[cluster_name]['cloudType']
        k8s_cluster_datacenter_list = k8s_clusters[cluster_name]['data_center']

        if len(k8s_cluster_environment_list) > 0:
            k8s_cluster_environment = k8s_cluster_environment_list[0]
        else:
            if 'PROD' in cluster_name.upper() or 'PRD' in cluster_name.upper() or 'K8P' in cluster_name.upper():
                k8s_cluster_environment = 'PRODUCTION'
            else:
                if 'STAGE' in cluster_name.upper() or 'STG' in cluster_name.upper() or 'K8S' in cluster_name.upper():
                    k8s_cluster_environment = 'STAGE'
                else:
                    if 'INT' in cluster_name.upper():
                        k8s_cluster_environment = 'INTEGRATION'
                    else:
                        if 'DEV' in cluster_name.upper():
                            k8s_cluster_environment = 'DEVELOPMENT'
                        else:
                            k8s_cluster_environment = 'NONE'

        if len(k8s_cluster_cloud_type_list) == 0:
            k8s_cluster_cloud_type = 'UNKNOWN_CLOUD_TYPE'
        else:
            k8s_cluster_cloud_type = k8s_cluster_cloud_type_list[0]

        if len(k8s_cluster_datacenter_list) == 0:
            k8s_cluster_datacenter = 'UNKNOWN_DATA_CENTER'
        else:
            k8s_cluster_datacenter = k8s_cluster_datacenter_list[0]
            # if k8s_cluster_datacenter.lower != 'pontiac' and k8s_cluster_datacenter.lower != 'grand rapids':
            #     k8s_cluster_datacenter = 'NONE'

        normalized_environment = environment_mz_name.get(k8s_cluster_environment.lower(), 'NONE')
        normalized_platform = platform_mz_name.get(k8s_cluster_cloud_type.lower(), 'NONE')
        normalized_datacenter = datacenter_mz_name.get(k8s_cluster_datacenter.lower(), 'NONE')

        print(cluster_name + ': ' + k8s_cluster_id + ': ' + k8s_cluster_environment.lower() + ': ' + k8s_cluster_cloud_type.lower()  + ': ' + k8s_cluster_datacenter.lower())
        print(cluster_name + ': ' + k8s_cluster_id + ': ' + normalized_environment + ': ' + normalized_platform  + ': ' + normalized_datacenter)

        filename_environment = filename_prefix_environment + normalized_environment + '.json'
        filename_platform = filename_prefix_platform + normalized_platform + '.json'
        filename_platform_environment = filename_prefix_platform_environment + normalized_platform + '_' + normalized_environment + '.json'
        filename_datacenter = filename_prefix_datacenter + normalized_datacenter + '.json'
        filename_datacenter_environment = filename_prefix_datacenter_environment + normalized_datacenter + '_' + normalized_environment + '.json'

        filename_all = filename_all.replace(' ', '_').lower()
        filename_environment = filename_environment.replace(' ', '_').lower()
        filename_platform = filename_platform.replace(' ', '_').lower()
        filename_platform_environment = filename_platform_environment.replace(' ', '_').lower()
        filename_datacenter = filename_datacenter.replace(' ', '_').lower()
        filename_datacenter_environment = filename_datacenter_environment.replace(' ', '_').lower()

        mz_name_all = 'K8s: All'
        mz_name_environment = 'K8s: ' + normalized_environment
        mz_name_platform = 'K8s: ' + normalized_platform
        mz_name_platform_environment = 'K8s: ' + normalized_platform + ' ' + normalized_environment
        mz_name_datacenter = 'K8s: ' + normalized_datacenter
        mz_name_datacenter_environment = 'K8s: ' + normalized_datacenter + ' ' + normalized_environment

        all_output = {'mzName': mz_name_all, 'dimensionalRules': [], 'rules': []}
        environment_output = {'mzName': mz_name_environment, 'dimensionalRules': [], 'rules': []}
        platform_output = {'mzName': mz_name_platform, 'dimensionalRules': [], 'rules': []}
        platform_environment_output = {'mzName': mz_name_platform_environment, 'dimensionalRules': [], 'rules': []}
        datacenter_output = {'mzName': mz_name_datacenter, 'dimensionalRules': [], 'rules': []}
        datacenter_environment_output = {'mzName': mz_name_datacenter_environment, 'dimensionalRules': [], 'rules': []}

        for dimensional_rule_template in dimensional_rules_template:
            new_dimensional_rule = eval(str(dimensional_rule_template).replace('{{.KUBERNETES_CLUSTER-ID}}', k8s_cluster_id))
            all_output['dimensionalRules'].append(new_dimensional_rule)
            environment_output['dimensionalRules'].append(new_dimensional_rule)
            platform_output['dimensionalRules'].append(new_dimensional_rule)
            platform_environment_output['dimensionalRules'].append(new_dimensional_rule)
            datacenter_output['dimensionalRules'].append(new_dimensional_rule)
            datacenter_environment_output['dimensionalRules'].append(new_dimensional_rule)
        for rule_template in rules_template:
            new_rule = eval(str(rule_template).replace('{{.KUBERNETES_CLUSTER-NAME}}', cluster_name))
            all_output['rules'].append(copy.deepcopy(new_rule))
            environment_output['rules'].append(copy.deepcopy(new_rule))
            platform_output['rules'].append(copy.deepcopy(new_rule))
            platform_environment_output['rules'].append(copy.deepcopy(new_rule))
            datacenter_output['rules'].append(copy.deepcopy(new_rule))
            datacenter_environment_output['rules'].append(copy.deepcopy(new_rule))

        if output_dict.get(filename_all, 'NOTFOUND') == 'NOTFOUND':
            output_dict[filename_all] = [all_output]
        else:
            output_dict[filename_all].append(all_output)

        if output_dict.get(filename_environment, 'NOTFOUND') == 'NOTFOUND':
            output_dict[filename_environment] = [environment_output]
        else:
            output_dict[filename_environment].append(environment_output)

        if output_dict.get(filename_platform, 'NOTFOUND') == 'NOTFOUND':
            output_dict[filename_platform] = [platform_output]
        else:
            output_dict[filename_platform].append(platform_output)

        if output_dict.get(filename_platform_environment, 'NOTFOUND') == 'NOTFOUND':
            output_dict[filename_platform_environment] = [platform_environment_output]
        else:
            output_dict[filename_platform_environment].append(platform_environment_output)

        if output_dict.get(filename_datacenter, 'NOTFOUND') == 'NOTFOUND':
            output_dict[filename_datacenter] = [datacenter_output]
        else:
            output_dict[filename_datacenter].append(datacenter_output)

        if output_dict.get(filename_datacenter_environment, 'NOTFOUND') == 'NOTFOUND':
            output_dict[filename_datacenter_environment] = [datacenter_environment_output]
        else:
            output_dict[filename_datacenter_environment].append(datacenter_environment_output)

    write_yaml_file(output_dict)
    write_json_files(output_dict)


def write_yaml_file(output_dict):
    configs = ['config:']
    names = []
    for filename in output_dict.keys():
        # print(filename)
        if 'none' not in filename.lower():
            output = output_dict.get(filename)[0]
            config = '- ' + filename.replace('.json', '') + ': ' + filename
            configs.append(config)
            name = filename.replace('.json', '') + ':'
            names.append(name)
            name = "- name: '" + output['mzName'] + "'"
            names.append(name)
    with open('management-zone.yaml', 'w') as file:
        for config in configs:
            file.write(config)
            file.write('\n')
        for name in names:
            file.write(name)
            file.write('\n')


def write_json_files(output_dict):
    management_zone_template = get_management_zone_template()

    for filename in output_dict.keys():
        if 'none' not in filename.lower():
            new_management_zone = management_zone_template
            new_management_zone['dimensionalRules'] = []
            new_management_zone['rules'] = []

            for output in output_dict.get(filename):
                new_management_zone['dimensionalRules'].extend(output['dimensionalRules'])
                new_management_zone['rules'].extend(output['rules'])

            write_management_zone(filename, new_management_zone)


def main(arguments):
    # For convenience, the default values are global and can be used easily
    # in the IDE or by passing no arguments from the command line.
    # Override them via command line by supplying the arguments.
    global env
    global token
    global tenant_name

    usage = '''
    generate_kubernetes_management_zones.py: Generate kubernetes management zones.

    Usage:    generate_kubernetes_management_zones.py <tenant/environment URL> <token> <friendly_tenant_name>
    Examples: generate_kubernetes_management_zones.py https://<TENANT>.live.dynatrace.com ABCD123ABCD123 SaaSDemo
              generate_kubernetes_management_zones.py https://<TENANT>.dynatrace-managed.com/e/<ENV>> ABCD123ABCD123 ManagedDemo
    '''

    # When no arguments are supplied, use the default global values
    if len(arguments) == 1:
        process(env, token)
        exit()

    if len(arguments) < 2:
        print(usage)
        raise ValueError('Too few arguments!')
    if len(arguments) > 4:
        print(help)
        raise ValueError('Too many arguments!')
    if arguments[1] in ['-h', '--help']:
        print(help)
    elif arguments[1] in ['-v', '--version']:
        print('1.0')
    else:
        if len(arguments) == 4:
            # Override the default global values when arguments are supplied
            env = arguments[1]
            token = arguments[2]
            tenant_name = arguments[3]
            process(env, token)
        else:
            print(usage)
            raise ValueError('Incorrect arguments!')


if __name__ == '__main__':
    main(sys.argv)
