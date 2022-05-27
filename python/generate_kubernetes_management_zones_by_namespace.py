import json
import sys
import dynatrace_rest_api_helper
import copy

# # $ACCOUNT$ LOWER
# tenant_name = '$ACCOUNT$ LOWER'
# env = 'https://$tenant2$.live.dynatrace.com'
# token = '$entity_token2$'
#
# # $ACCOUNT$ SANDBOX
# tenant_name = '$ACCOUNT$ SANDBOX'
# env = 'https://$tenant3$.live.dynatrace.com'
# token = '$entity_token3$'
#
# $ACCOUNT$ UPPER
tenant_name = '$ACCOUNT$ UPPER'
env = '  https://$tenant1$.live.dynatrace.com'
token = '$entity_token1$'


def process(env, token):
    # Write template with name including the tenant
    tenant = tenant_name.lower().replace(' ', '_')
    management_zone_template_file_name = 'k8s_namespace_management_zone_' + tenant + '.json'
    write_management_zone(management_zone_template_file_name, get_management_zone_template())

    # Get all namespaces
    endpoint = '/api/v2/entities'
    params = 'entitySelector=type%28CLOUD_APPLICATION_NAMESPACE%29'
    kubernetes_namespaces_json_list = dynatrace_rest_api_helper.get_rest_api_json(env, token, endpoint, params)

    # Get all hosts with "Kubernetes Namespace" tag(s)
    endpoint = '/api/v2/entities'
    params = 'entitySelector=type%28host%29%2Ctag%28%22Kubernetes%20Namespace%22%29&fields=%2Btags'
    hosts_json_list = dynatrace_rest_api_helper.get_rest_api_json(env, token, endpoint, params)
    # print(str(hosts_json_list))

    namespaces = []
    for kubernetes_namespaces_json in kubernetes_namespaces_json_list:
        inner_kubernetes_namespaces_json_list = kubernetes_namespaces_json.get('entities')
        for inner_kubernetes_namespaces_json in inner_kubernetes_namespaces_json_list:
            entity_id = inner_kubernetes_namespaces_json.get('entityId')
            display_name = inner_kubernetes_namespaces_json.get('displayName')
            # print(entity_id + ': ' + display_name)
            # Only generate management zones for namespaces tagging one or more hosts
            search_namespace = "'Kubernetes Namespace', 'value': '" + display_name + "'"
            # 'Kubernetes Namespace', 'value': '$account$-trisotech'
            # print(search_namespace)
            if search_namespace in str(hosts_json_list):
                if display_name not in namespaces:
                    namespaces.append(display_name)

    write_yaml_file(sorted(namespaces), management_zone_template_file_name)


def get_management_zone_template():
    with open('management_zone_by_namespace_template.json', 'r', encoding='utf-8') as file:
        management_zone_template_string = file.read()
        # management_zone_template = json.loads(management_zone_template_string)
        return management_zone_template_string


def write_management_zone(filename, management_zone):
    with open(filename, 'w') as file:
        # file.write(json.dumps(management_zone, indent=4, sort_keys=False))
        file.write(management_zone)


def write_yaml_file(namespaces, management_zone_template_file_name):
    configs = ['config:']
    names = []
    for namespace in namespaces:
        config = '- ' + namespace + ': ' + management_zone_template_file_name
        configs.append(config)
        name = namespace + ':'
        names.append(name)
        name = "- name: '" + 'K8s NS: ' + namespace + "'"
        names.append(name)
        name = "- namespace: '" + namespace + "'"
        names.append(name)
    with open('management-zone.yaml', 'w') as file:
        for config in configs:
            file.write(config)
            file.write('\n')
        for name in names:
            file.write(name)
            file.write('\n')


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
