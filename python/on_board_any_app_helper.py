import monaco_meta_generator
# from Monaco import monaco_meta_generator

# copy collides with function named "copy" in this module
import copy as copy_module
import json
import os
import os.path
import re
import shutil
import subprocess
import time
import yaml

# Supported: high|none
verbosity = 'none'
confirmation_required = False


def get_meta():
    print_high('Executing: get_meta()')

    with open('meta.yaml', 'r') as file:
        document = file.read()
        return yaml.load(document, Loader=yaml.FullLoader)


def generate_monaco_configuration_file():
    print_high('Executing: generate_monaco_configuration_file()')

    monaco_meta_generator.generate_monaco_configuration_file()

    confirm('Confirm monaco.yaml contents are correct', confirmation_required)


def generate_delete_yaml_file():
    print_high('Executing: generate_delete_yaml_file()')

    monaco_meta_generator.generate_delete_yaml_file()

    confirm('Confirm meta-output/delete.yaml contents are correct', confirmation_required)


def initialize_temporary_directories():
    print_high('Executing: initialize_temporary_directories()')

    remove_dir('meta-output')
    remove_dir('meta-work')

    makedir('meta-output')
    makedir('meta-output/entities')
    makedir('meta-output/entities/app-detection-rule')
    makedir('meta-output/entities/application-web')
    makedir('meta-output/entities/auto-tag')
    makedir('meta-output/entities/management-zone')
    makedir('meta-work')
    makedir('meta-work/entities')
    makedir('meta-work/entities/application-web')

    confirm('Confirm that meta-output/entities \
        (with 4 subdirectories: app-detection-rule, application-web, auto-tag and management-zone) \
        and work/entities (1 subdirectory: application-web) sub directories exist.', confirmation_required)


def add_web_applications():
    print_high('Executing: add_web_applications()')

    copy('meta-input/entities/application-web/application-web.json', 'meta-output/entities/application-web')
    if monaco_meta_generator.generate_application_web_yaml():
        copy('meta-input/entities/application-web/application-web.json', 'meta-work/entities/application-web')
        copy('meta-output/entities/application-web/application-web.yaml', 'meta-work/entities/application-web')

    messages = ['']
    pass
    messages.append(
        'Confirm that the meta-work/entities/application-web subdirectory contains correct json and yaml files')
    messages.append('Confirm that the meta-output/entities/application-web subdirectory \
        contains correct json and yaml files')
    confirm(messages, confirmation_required)

    monaco_deploy('meta-work')

    messages = []
    pass
    messages.append('')
    messages.append(
        'Confirm that the web applications were successfully added using the Dynatrace UI and/or monaco logs \
        (work/.logs)')
    confirm(messages, confirmation_required)

    # To avoid possible race conditions in monaco when referencing a recently added web application
    time.sleep(5)


def mock_add_web_applications():
    print_high('Executing: mock_add_web_applications()')

    copy('meta-input/entities/application-web/application-web.json', 'meta-output/entities/application-web')
    copy('meta-input/entities/application-web/application-web.json', 'meta-work/entities/application-web')
    monaco_meta_generator.generate_application_web_yaml()
    copy('meta-output/entities/application-web/application-web.yaml', 'meta-work/entities/application-web')

    messages = []
    pass
    messages.append('')
    messages.append(
        'Confirm that the meta-work/entities/application-web subdirectory contains correct json and yaml files')
    messages.append(
        'Confirm that the meta-output/entities/application-web subdirectory contains correct json and yaml files')
    confirm(messages, confirmation_required)

    messages = []
    pass
    messages.append('')
    messages.append(
        'Confirm that the web application yaml and json files were added to meta-output/entities/application-web '
        'subdirectory)')
    confirm(messages, confirmation_required)


def download_app_entities():
    print_high('Executing: download_app_entities()')

    monaco_download_specific_api('meta-work', 'application-web')

    confirm(
        'Confirm that the meta-work\\entities\\application-web subdirectory is populated with multiple '
        'json/yaml files downloaded',
        confirmation_required)


def download_app_and_tag_entities():
    print_high('Executing: download_app_and_tag_entities()')

    monaco_download_specific_api('meta-work', 'application-web,auto-tag')

    confirm(
        'Confirm that the meta-work\\entities\\application-web and meta-work\\entities\\auto-tag subdirectories '
        'are populated with multiple json/yaml files downloaded',
        confirmation_required)


def download_all_application_on_boarding_entities():
    print_high('Executing: download_all_application_on_boarding_entities()')

    monaco_download_specific_api('meta-work', 'app-detection-rule,application-web,auto-tag,management-zone')

    missing_files = get_missing_application_on_boarding_files()
    if not missing_files:
        print('Download complete!.')
    else:
        print('Download FAILED!.')
        print('The following files were not downloaded:')
        print_list(missing_files)
        exit(1)

    confirm(
        'Confirm that the app-detection-rule, application-web, auto-tag and management-zone subdirectories '
        'under meta-work\\entities are populated with multiple json/yaml files downloaded',
        confirmation_required)


def download_mz_entities():
    print_high('Executing: download_mz_entities()')

    monaco_download_specific_api('meta-work', 'management-zone')

    confirm(
        'Confirm that the meta-work\\entities\\management-zone subdirectory is populated with '
        'multiple json/yaml files downloaded',
        confirmation_required)


def download_tag_entities():
    print_high('Executing: download_tag_entities()')

    monaco_download_specific_api('meta-work', 'auto-tag')

    confirm('Confirm that the meta-work\\entities\\auto-tag subdirectory is populated'
            ' with multiple json/yaml files downloaded',
            confirmation_required)


def copy_auto_tag_to_meta_input():
    print_high('Executing: copy_auto_tag_to_meta_input()')

    copy('meta-work/entities/auto-tag/Application.json', 'meta-input/entities/auto-tag')

    confirm(
        'Confirm that the meta-input\\entities\\auto-tag\\Application.json file looks good '
        '(this is BEFORE additions of new applications)',
        confirmation_required)


def copy_auto_tag_to_meta_input_for_delete():
    print_high('Executing: copy_auto_tag_to_meta_input_for_delete()')

    copy('meta-work/entities/auto-tag/Application.json', 'meta-input/entities/auto-tag')

    confirm(
        'Confirm that the meta-input\\entities\\auto-tag\\Application.json file looks good \
        (this is BEFORE removal of application(s))',
        confirmation_required)


def copy_tag_entities_to_meta_output():
    print_high('Executing: copy_tag_entities_to_meta_output()')

    meta = get_meta()
    configs = meta.get('configs')
    streamline_yaml(configs, 'meta-work/entities/auto-tag/auto-tag.yaml')
    copy('meta-work/entities/auto-tag/auto-tag.yaml', 'meta-output/entities//auto-tag')

    tag_file_name = 'meta-work/entities/auto-tag/Application.json'
    copy(tag_file_name, 'meta-output/entities/auto-tag')

    confirm('Confirm that meta-output\\entities\\management-zone yaml and json files look good', confirmation_required)


def copy_mz_entities_to_meta_output():
    print_high('Executing: copy_mz_entities_to_meta_output()')

    short_env_names = {'DEVELOPMENT': 'DEV'}
    meta = get_meta()
    configs = meta.get('configs')

    streamline_yaml(configs, 'meta-work/entities/management-zone/management-zone.yaml')
    copy('meta-work/entities/management-zone/management-zone.yaml', 'meta-output/entities/management-zone')

    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        env = name_dict.get('env')
        short_env_name = short_env_names.get(env)
        mz_file_name = 'meta-work/entities/management-zone/' + 'App' + name + '-' + short_env_name + '.json'
        copy(mz_file_name, 'meta-output/entities/management-zone')

    confirm('Confirm that meta-output\\entities\\management-zone yaml and json files look good', confirmation_required)


def add_apps_to_application_tag():
    print_high('Executing: add_apps_to_application_tag()')

    add_application_tag_entity_selector_rule()
    monaco_meta_generator.generate_auto_tag_yaml()

    messages = []
    pass
    messages.append(
        'Confirm that the meta-output\\entities\\auto-tag\\Application.json and \
        meta-output\\entities\\auto-tag\\auto-tag.yaml files look good')
    messages.append(
        'meta-output/entities/auto-tag/Application.json should now contain entity selector rules \
        for the new (name in six) applications')
    messages.append('meta-output/entities/auto-tag/auto-tag.yaml should now also exist')
    confirm(messages, confirmation_required)


def remove_apps_from_application_tag():
    print_high('Executing: remove_apps_from_application_tag()')

    remove_application_tag_entity_selector_rule()
    monaco_meta_generator.generate_auto_tag_yaml()

    messages = []
    pass
    messages.append(
        'Confirm that the meta-work\\entities\\auto-tag\\Application.json file no longer references \
        the application(s) being deleted')
    messages.append('meta-output/entities/auto-tag/auto-tag.yaml should now also exist')
    confirm(messages, confirmation_required)


def generate_management_zone_files():
    print_high('Executing: generate_management_zone_files()')

    meta = get_meta()

    configs = meta.get('configs')
    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        app = name_dict.get('app', '')
        apps = name_dict.get('apps', [app])
        env = name_dict.get('env', '')
        domain = name_dict.get('domain', '')
        calls_database = name_dict.get('calls_database', True)
        k8s_clusters = name_dict.get('clusters', [])

        with open('meta-input/entities/management-zone/management-zone-template.json', 'r', encoding='utf-8') as file:
            mz_json = json.loads(file.read())
            rules = mz_json.get('rules')
            process_group_rule = rules[0]
            web_app_rule = rules[1]
            browser_rule = rules[2]
            db_rule = rules[3]

            if len(k8s_clusters) > 0:
                dimensional_rules = mz_json.get('dimensionalRules')
                dimensional_rule = dimensional_rules[0]

            # Delete rules that do not apply
            if not k8s_clusters:
                rules = mz_json.get('rules')
                del rules[9]
                del rules[8]
                del rules[7]
                del rules[6]
                del rules[5]
                del rules[4]
                mz_json['rules'] = rules
                mz_json['dimensionalRules'] = []

            if not calls_database:
                rules = mz_json.get('rules')
                del rules[3]
                mz_json['rules'] = rules

            if domain == '':
                rules = mz_json.get('rules')
                del rules[2]
                del rules[1]
                mz_json['rules'] = rules

            new_mz_json = copy_module.deepcopy(mz_json)

            # Multi-app logic
            if len(apps) > 0:
                new_rules = []
                new_dimensional_rules = []

                suffix = 1
                for _ in apps:
                    new_rule = copy_module.deepcopy(process_group_rule)
                    conditions = process_group_rule.get('conditions')[0]
                    comparison_info = conditions.get('comparisonInfo')
                    value = comparison_info.get('value').get('value')
                    new_value = value.replace('app', 'app' + str(suffix))
                    new_rule['conditions'][0]['comparisonInfo']['value']['value'] = new_value
                    new_rules.append(new_rule)
                    # For web apps, only the first "app" ever matters
                    if domain != '' and suffix == 1:
                        new_rule = copy_module.deepcopy(web_app_rule)
                        conditions = web_app_rule.get('conditions')[0]
                        comparison_info = conditions.get('comparisonInfo')
                        value = comparison_info.get('value').get('value')
                        new_value = value.replace('app', 'app' + str(suffix))
                        new_rule['conditions'][0]['comparisonInfo']['value']['value'] = new_value
                        new_rules.append(new_rule)
                        new_rule = copy_module.deepcopy(browser_rule)
                        conditions = browser_rule.get('conditions')[0]
                        comparison_info = conditions.get('comparisonInfo')
                        value = comparison_info.get('value').get('value')
                        new_value = value.replace('app', 'app' + str(suffix))
                        new_rule['conditions'][0]['comparisonInfo']['value']['value'] = new_value
                        new_rules.append(new_rule)
                    suffix += 1

                if calls_database:
                    suffix = 1
                    for _ in apps:
                        new_rule = copy_module.deepcopy(db_rule)
                        conditions = db_rule.get('conditions')[1]
                        comparison_info = conditions.get('comparisonInfo')
                        value = comparison_info.get('value').get('value')
                        new_value = value.replace('app', 'app' + str(suffix))
                        new_rule['conditions'][1]['comparisonInfo']['value']['value'] = new_value
                        new_rules.append(new_rule)
                        suffix += 1

                suffix = 1
                for _ in k8s_clusters:
                    for rule in rules:
                        new_rule = copy_module.deepcopy(rule)
                        conditions = rule.get('conditions')[0]
                        comparison_info = conditions.get('comparisonInfo')
                        value = comparison_info.get('value')
                        if value == '{{.cluster_name}}':
                            new_value = value.replace('cluster_name', 'cluster_name' + str(suffix))
                            new_rule['conditions'][0]['comparisonInfo']['value'] = new_value
                            new_rules.append(new_rule)

                    new_dimensional_rule = copy_module.deepcopy(dimensional_rule)
                    conditions = dimensional_rule.get('conditions')[0]
                    value = conditions.get('value')
                    new_value = value.replace('cluster_id', 'cluster_id' + str(suffix))
                    new_dimensional_rule['conditions'][0]['value'] = new_value
                    new_dimensional_rules.append(new_dimensional_rule)

                    suffix += 1

                new_mz_json['rules'] = new_rules
                new_mz_json['dimensionalRules'] = new_dimensional_rules

        with open('meta-output/entities/management-zone/' + name + env + '.json', 'w') as file:
            file.write(json.dumps(new_mz_json, indent=4, sort_keys=False))

    monaco_meta_generator.generate_management_zone_yaml()

    confirm('Confirm that meta-output\\entities\\management-zone\\management-zone.yaml and \
    meta-output\\entities\\management-zone\\management-zone.json look good', confirmation_required)


def generate_app_detection_yaml():
    print_high('Executing: generate_app_detection_yaml()')

    copy('meta-input/entities/app-detection-rule/app-detection-rule.json',
         'meta-output/entities/app-detection-rule')
    monaco_meta_generator.generate_app_detection_yaml()

    confirm('Confirm that meta-output\\entities\\app-detection-rule\\app-detection-rule.yaml and \
    meta-output\\entities\\app-detection-rule\\app-detection-rule.json look good', confirmation_required)


def copy_application_web_files_to_meta_output():
    print_high('Executing: copy_application_web_files_to_meta_output()')

    meta = get_meta()
    configs = meta.get('configs')
    streamline_yaml(configs, 'meta-work/entities/application-web/application-web.yaml')

    with open('meta-work/entities/application-web/application-web.yaml', 'r') as file:
        document = file.read()
        doc = yaml.load(document, Loader=yaml.FullLoader)
        configs = doc['config']
        for config in configs:
            name = list(config.keys())[0]
            src = 'meta-work/entities/application-web/' + name + '.json'
            dst = 'meta-output/entities/application-web'
            copy(src, dst)
    copy('meta-work/entities/application-web/application-web.yaml', 'meta-output/entities/application-web')
    monaco_meta_generator.generate_app_detection_yaml()

    confirm('Confirm that meta-output\\entities\\application-web json and yaml files look good \
    (new apps should be included here for reference by \
    meta-output/entities/app-detection-rule/app-detection-rule.yaml)', confirmation_required)


def copy_application_on_boarding_entities_to_meta_output():
    print_high('Executing: copy_application_on_boarding_entities_to_meta_output()')

    short_env_names = {'DEVELOPMENT': 'DEV'}
    meta = get_meta()
    configs = meta.get('configs')

    streamline_yaml(configs, 'meta-work/entities/app-detection-rule/app-detection-rule.yaml')
    streamline_yaml(configs, 'meta-work/entities/application-web/application-web.yaml')
    streamline_yaml(configs, 'meta-work/entities/auto-tag/auto-tag.yaml')
    streamline_yaml(configs, 'meta-work/entities/management-zone/management-zone.yaml')

    copy('meta-work/entities/app-detection-rule/app-detection-rule.yaml', 'meta-output/entities/app-detection-rule')
    copy('meta-work/entities/application-web/application-web.yaml', 'meta-output/entities/application-web')
    copy('meta-work/entities/auto-tag/auto-tag.yaml', 'meta-output/entities/auto-tag')
    copy('meta-work/entities/management-zone/management-zone.yaml', 'meta-output/entities/management-zone')
    copy('meta-work/entities/auto-tag/Application.json', 'meta-output/entities/auto-tag')

    app_detection_rule_names = []
    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        apps = name_dict.get('apps', [''])
        app = name_dict.get('app', apps[0])
        env = name_dict.get('env')
        domain = name_dict.get('domain', '')
        short_env_name = short_env_names.get(env)
        mz_file_name = 'meta-work/entities/management-zone/' + 'App' + name + '-' + short_env_name + '.json'
        copy(mz_file_name, 'meta-output/entities/management-zone')
        if domain != '':
            app_detection_rule_name = name + app + env
            app_detection_rule_names.append(app_detection_rule_name)
            app_detection_rule_file_name = 'meta-work/entities/app-detection-rule/' + app_detection_rule_name + '.json'
            copy(app_detection_rule_file_name, 'meta-output/entities/app-detection-rule')
            application_web_file_name = 'meta-work/entities/application-web/' + name + app + env + '.json'
            copy(application_web_file_name, 'meta-output/entities/application-web')

    confirm('Confirm that meta-output\\entities yaml and json files look good', confirmation_required)


def get_missing_application_on_boarding_files():
    print_high('Executing: application_on_boarding_files_exist()')

    root_directory = 'meta-work/entities'

    missing_files = []

    filename = root_directory + '/app-detection-rule/app-detection-rule.yaml'
    if not os.path.exists(filename):
        missing_files.append(filename)
    filename = root_directory + '/application-web/application-web.yaml'
    if not os.path.exists(filename):
        missing_files.append(filename)
    filename = root_directory + '/auto-tag/auto-tag.yaml'
    if not os.path.exists(filename):
        missing_files.append(filename)
    filename = root_directory + '/management-zone/management-zone.yaml'
    if not os.path.exists(filename):
        missing_files.append(filename)
    filename = root_directory + '/auto-tag/Application.json'
    if not os.path.exists(filename):
        missing_files.append(filename)

    short_env_names = {'DEVELOPMENT': 'DEV'}
    meta = get_meta()
    configs = meta.get('configs')
    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        apps = name_dict.get('apps', [''])
        app = name_dict.get('app', apps[0])
        env = name_dict.get('env')
        domain = name_dict.get('domain', '')
        short_env_name = short_env_names.get(env)
        mz_file_name = 'meta-work/entities/management-zone/' + 'App' + name + '-' + short_env_name + '.json'
        if not os.path.exists(mz_file_name):
            missing_files.append(mz_file_name)

        if domain != '':
            app_detection_rule_file_name = 'meta-work/entities/app-detection-rule/' + name + app + env + '.json'
            application_web_file_name = 'meta-work/entities/application-web/' + name + app + env + '.json'
            if not os.path.exists(app_detection_rule_file_name):
                missing_files.append(app_detection_rule_file_name)
            if not os.path.exists(application_web_file_name):
                missing_files.append(mz_file_name)

    return missing_files


def add_entities_via_monaco():
    print_high('Executing: add_entities_via_monaco()')

    monaco_deploy('meta-output')

    messages = []
    pass
    messages.append('Confirm via the Dynatrace UI and/or monaco logs (meta-output/.logs) that the \
    following entities were added/changed:')
    messages.append('Application Detection Rules (ADDED)')
    messages.append('Management Zones (ADDED)')
    messages.append('Auto Tag "Application" (CHANGED: entity selector rules for each "name in six" \
    application added)')
    messages.append('Web Applications that were added earlier should have already been verified...')
    confirm(messages, confirmation_required)


def validate_entities_via_monaco():
    print_high('Executing: validate_entities_via_monaco()')

    monaco_dry_run('meta-output', True)

    message = 'Confirm via the monaco logs (meta-output/.logs) that the dry run looks good.'
    confirm(message, confirmation_required)


def delete_entities_via_monaco():
    print_high('Executing: delete_entities_via_monaco()')

    monaco_delete('meta-output')

    messages = []
    pass
    messages.append('Confirm via the Dynatrace UI and/or monaco logs (meta-output/.logs) \
    that the following entities were deleted/changed:')
    messages.append('Web Applications (DELETED')
    messages.append('Application Detection Rules (DELETED)')
    messages.append('Management Zones (DELETED)')
    messages.append('Auto Tag "Application" (CHANGED: entity selector rules for each "name in six" \
    application removed)')
    confirm(messages, confirmation_required)


def get_application_tag():
    with open('meta-input/entities/auto-tag/Application.json', 'r', encoding='utf-8') as file:
        application_tag_string = file.read()
        application_tag = json.loads(application_tag_string)
        return application_tag


def write_application_tag(application_tag):
    with open('meta-output/entities/auto-tag/Application.json', 'w') as file:
        file.write(json.dumps(application_tag, indent=4, sort_keys=False))


def add_application_tag_entity_selector_rule():
    entity_selector_template = {'enabled': True, 'entitySelector': 'type(SERVICE), databaseName.exists(), \
    toRelationships.calls(type(SERVICE), tag(Application:{{.app}}))', 'valueFormat': '{{.app}}'
    }

    application_tag = get_application_tag()
    entity_selector_based_rules = application_tag.get('entitySelectorBasedRules')

    meta = get_meta()
    configs = meta.get('configs')
    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        app = name_dict.get('app', '')
        apps = name_dict.get('apps', [app])
        calls_database = name_dict.get('calls_database', 'True')
        for app in apps:
            if not calls_database:
                print_high('Application ' + app + 'does not call database, skipping...')
            else:
                if app in str(entity_selector_based_rules):
                    print_high(
                        'Application ' + app + ' already occurs in the Application entity selector list, skipping...')
                else:
                    new_entity_selector = copy_module.deepcopy(entity_selector_template)
                    new_entity_selector['entitySelector'] = new_entity_selector['entitySelector'].replace('{{.app}}', app)
                    new_entity_selector['valueFormat'] = new_entity_selector['valueFormat'].replace('{{.app}}', app)
                    entity_selector_based_rules.append(new_entity_selector)
    application_tag['entitySelectorBasedRules'] = entity_selector_based_rules
    write_application_tag(application_tag)


def remove_application_tag_entity_selector_rule():
    application_tag = get_application_tag()
    entity_selector_based_rules = application_tag.get('entitySelectorBasedRules')

    meta = get_meta()
    configs = meta.get('configs')
    apps_to_delete = []
    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        app = name_dict.get('app', '')
        apps = name_dict.get('apps', [])
        if app != '':
            apps.append(app)
        for app in apps:
            apps_to_delete.append(app)

    new_entity_selector_based_rules = []

    for entity_selector_based_rule in entity_selector_based_rules:
        if entity_selector_based_rule['valueFormat'] not in apps_to_delete:
            new_entity_selector_based_rules.append(entity_selector_based_rule)

    application_tag['entitySelectorBasedRules'] = new_entity_selector_based_rules
    write_application_tag(application_tag)


def streamline_yaml(configs, yaml_file):
    configs = transform_configs(configs, yaml_file)

    with open(yaml_file, 'r') as file:
        document = file.read()
        yaml_document = yaml.load(document, Loader=yaml.FullLoader)
        yaml_configs = yaml_document.get('config')

        new_configs = []
        new_details = []
        for yaml_config in yaml_configs:
            key = list(yaml_config.keys())[0]
            if key in configs:
                new_configs.append(yaml_config)
                yaml_details = yaml_document.get(key)
                new_details_dict = {
                    key: yaml_details
                }
                new_details.append(new_details_dict)

        new_yaml_dict = {'config': new_configs}
        for new_details_dict in new_details:
            key = list(new_details_dict.keys())[0]
            new_yaml_dict[key] = new_details_dict[key]

    with open(yaml_file, 'w') as file:
        yaml.dump(new_yaml_dict, file, sort_keys=False)


def transform_configs(configs, yaml_file):
    short_env_names = {'DEVELOPMENT': 'DEV'}
    new_configs = []
    for config in configs:
        name = list(config.keys())[0]
        name_dict = config.get(name)
        apps = name_dict.get('apps', [''])
        app = name_dict.get('app', apps[0])
        env = name_dict.get('env')
        short_env_name = short_env_names.get(env)

        if 'management-zone' in yaml_file:
            config_name = 'App' + name + '-' + short_env_name
            new_configs.append(config_name)
        else:
            if 'application-web' in yaml_file or 'app-detection-rule' in yaml_file:
                config_name = name + app + env
                new_configs.append(config_name)
            else:
                if 'auto-tag' in yaml_file:
                    config_name = 'Application'
                    new_configs.append(config_name)
                else:
                    print('Invalid file name for transformation: ' + yaml_file)
                    exit(1)

    return new_configs


def backup_current_directory():
    print_high('Executing: backup_current_directory()')

    meta = get_meta()
    tenant = meta.get('tenant')
    action = meta.get('action')

    time_string = time.strftime('%Y%m%d-%H%M%S')
    zip_name = '..\\Monaco-Backups\\Automation_Monaco_' + tenant + '_' + action + '_' + time_string
    shutil.make_archive(zip_name, 'zip', '.')
    print_high(f'successfully created archive: {zip_name + ".zip"}')


def monaco_deploy(work_directory):
    print_high('Executing: monaco_deploy(work_directory)')

    command_line = 'cd ' + work_directory + '&@echo off&monaco deploy --environments=..\\monaco.yaml -p=entities'
    command_line += ' > monaco.out 2>&1'
    print_high(command_line)

    subprocess.run(command_line, shell=True)

    with open(work_directory + '/monaco.out', 'r') as file:
        monaco_output = file.read()

    print_high(monaco_output)

    if 'Deployment finished without errors' in monaco_output:
        if work_directory == 'meta-output':
            print('Deploy complete!')
    else:
        print('Deploy FAILED')
        print(monaco_output)


def monaco_delete(work_directory):
    print_high('Executing: monaco_delete(work_directory)')

    command_line = 'cd ' + work_directory + '&@echo off&monaco deploy --environments=..\\monaco.yaml -p=entities'
    command_line += ' > monaco.out 2>&1'
    print_high(command_line)

    subprocess.run(command_line, shell=True)

    with open(work_directory + '/monaco.out', 'r') as file:
        monaco_output = file.read()

    print_high(monaco_output)

    if 'Deployment finished without errors' in monaco_output:
        print('Delete complete!')
    else:
        print('Delete FAILED')
        print(monaco_output)


def monaco_dry_run(work_directory, is_webapp):
    print_high('Executing: monaco_dry_run(work_directory)')

    meta = get_meta()
    calls_database = meta.get('calls_database', True)

    command_line = 'cd ' + work_directory + \
                   '&@echo off&monaco_old_cli -dry-run --environments=..\\monaco.yaml -p=entities'
    command_line += ' > monaco.out 2>&1'
    print_high(command_line)

    subprocess.run(command_line, shell=True)

    with open(work_directory + '/monaco.out', 'r') as file:
        monaco_output = file.read()

    print_high(monaco_output)

    if 'Validation finished without errors' in monaco_output:
        if is_webapp:
            print('Validation PASSED for application-web, auto-tag, and management-zone.  ' +
                  'NOTE: app-detection-rule cannot be validated.')
        else:
            if calls_database:
                print('Validation PASSED for auto-tag, and management-zone.')
            else:
                print('Validation PASSED for management-zone.')
    else:
        print('Validation FAILED')
        print(monaco_output)


def monaco_download_specific_api(work_directory, specific_api):
    print_high('Executing: monaco_download(work_directory)')

    command_line = 'cd ' + work_directory + '&@echo off&monaco download --downloadSpecificAPI ' + \
                   specific_api + ' --environments=..\\monaco.yaml'
    command_line += ' > monaco.out 2>&1'
    print_high(command_line)

    subprocess.run(command_line, shell=True)

    with open(work_directory + '/monaco.out', 'r') as file:
        monaco_output = file.read()

    print_high(monaco_output)


def print_high(string):
    if verbosity == 'high':
        print(string)


def print_list(lines):
    for line in lines:
        print(line)


def confirm(message, confirmation_is_required):
    if confirmation_is_required:
        if isinstance(message, list):
            print_list(message)
        else:
            print(message)

        msg = 'PROCEED?'
        proceed = input('%s (Y/n) ' % msg).upper() == 'Y'
        if not proceed:
            exit()


def makedir(path):
    print_high('Executing: makedir(path)')

    try:
        os.mkdir(path)
    except OSError:
        print('Creation of the directory %s failed' % path)
        exit()
    else:
        print_high('Successfully created the directory %s ' % path)


def remove_dir(path):
    print_high('Executing: remove_dir(path)')

    try:
        shutil.rmtree(path, ignore_errors=False)

    except OSError:
        print_high('Directory %s does not exist' % path)
    else:
        print_high('Removed the directory %s ' % path)


def copy(src, dst):
    print_high('Executing: copy(src, dst)')

    try:
        shutil.copy(src, dst)

    except OSError:
        print('File %s not copied to %s! Aborting...' % (src, dst))
        exit(1)
    else:
        print_high('File %s was copied' % src)


def confirm_meta(meta):
    action = meta.get('action')
    tenant = meta.get('tenant')
    configs = meta.get('configs')
    if action == 'dry-run':
        print('You are about to perform a dry run against ' + tenant + ' for the following:')
    else:
        to_from = ' from '
        if action == 'deploy':
            to_from = ' to '
        print('You are about to ' + action + to_from + tenant + ':')
    for config in configs:
        config_string = re.sub(r'[{}"]', '', str(config))
        print(config_string)
    msg = 'PROCEED?'
    proceed = input('%s (Y/n) ' % msg).upper() == 'Y'
    if not proceed:
        exit()


if __name__ == '__main__':
    add_apps_to_application_tag()
    exit()
    remove_apps_from_application_tag()
    exit()
    backup_current_directory()
    exit()
    generate_management_zone_files()
    exit()
    download_all_application_on_boarding_entities()
    exit()
    copy_application_on_boarding_entities_to_meta_output()
    exit()
    print('Not to be run standalone.  \
    Use one of the "on_board_*.py" modules designed to on_board a specific type of application.  \
    They call this module.')
    exit(1)
