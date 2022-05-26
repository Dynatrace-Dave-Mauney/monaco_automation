import on_board_any_app_helper as helper
# from Monaco import on_board_any_app_helper as helper

# Supported: high|none
verbosity = 'none'
confirmation_required = False


def print_high(string):
	if verbosity == 'high':
		print(string)


def deploying_web_apps():
	configs = meta.get('configs')
	for config in configs:
		name = list(config.keys())[0]
		name_dict = config.get(name)
		domain = name_dict.get('domain', '')
		if domain != '':
			return True
	return False


def deploy_flow():
	# Step 1: Generate monaco.yaml
	helper.generate_monaco_configuration_file()

	# Step 2: Initialize the meta-output and meta-work folders
	helper.initialize_temporary_directories()

	if deploying_web_apps():
		# Step 3: Add Application(s) via monaco
		helper.add_web_applications()

		# Step 4: Download all application-web entities to meta-work folder for later use
		helper.download_app_entities()

		# Step 5: Generate app-detection-rule.yaml and copy app-detection-rule.json from meta-input folder
		helper.generate_app_detection_yaml()

		# Step 6: Copy application-web files downloaded earlier to meta-output folder
		helper.copy_application_web_files_to_meta_output()

	# Step 7: Download all auto-tag entities to meta-work folder for later use
	helper.download_tag_entities()

	# Step 8: Copy Application Auto Tag to meta-input folder
	helper.copy_auto_tag_to_meta_input()

	# Step 9: Add entity selector rule to Application auto-tag and generate auto-tag YAML
	helper.add_apps_to_application_tag()

	# Step 10: Generate management-zone.yaml and copy management-zone.json from meta-input folder
	helper.generate_management_zone_files()

	# Step 11: Add/Update entities via monaco (excluding any Web Applications as they were already added)
	helper.add_entities_via_monaco()

	# Step 12: Backup the current directory
	helper.backup_current_directory()


def delete_flow():
	# Step 1: Generate monaco.yaml
	helper.generate_monaco_configuration_file()

	# Step 2: Initialize the meta-output and meta-work folders
	helper.initialize_temporary_directories()

	if deploying_web_apps():
		# Step 3: Download all application-web entities to meta-work folder for later use
		helper.download_app_entities()

		# Step 4: Copy application-web files to meta-output folder
		helper.copy_application_web_files_to_meta_output()

	# Step 5 Download all auto-tag entities to meta-work folder for later use
	helper.download_tag_entities()

	# Step 6: Copy Application Auto Tag to meta-input folder
	helper.copy_auto_tag_to_meta_input_for_delete()

	# Step 7: Remove entity selector rules from Application auto-tag and generate auto-tag YAML
	helper.remove_apps_from_application_tag()

	# Step 8: Generate management-zone.yaml and copy management-zone.json from meta-input folder
	helper.generate_management_zone_files()

	# Step 9: Generate app-detection-rule.yaml and copy app-detection-rule.json from meta-input folder
	helper.generate_app_detection_yaml()

	# Step 10: Generate delete.yaml
	helper.generate_delete_yaml_file()

	# Step 11: Delete/Update entities via monaco
	helper.delete_entities_via_monaco()

	# Step 12: Backup the current directory
	helper.backup_current_directory()


def download_flow():
	# Step 1: Generate monaco.yaml
	helper.generate_monaco_configuration_file()

	# Step 2: Initialize the meta-output and meta-work folders
	helper.initialize_temporary_directories()

	# Step 3: Download all application on-boarding entities to meta-work folder
	helper.download_all_application_on_boarding_entities()

	# Step 4: Copy application on-boarding entities to meta-output folder
	helper.copy_application_on_boarding_entities_to_meta_output()


def dry_run_flow():
	# Step 1: Generate monaco.yaml
	helper.generate_monaco_configuration_file()

	# Step 2: Initialize the meta-output and meta-work folders
	helper.initialize_temporary_directories()

	# Step 3: Add Application(s) via monaco
	helper.mock_add_web_applications()

	# Step 4: Download all application-web and auto-tag entities to meta-work folder for later use
	helper.download_app_and_tag_entities()

	# Step 5: Copy Application Auto Tag to meta-input folder
	helper.copy_auto_tag_to_meta_input()

	# Step 6: Add entity selector rule to Application auto-tag and generate auto-tag YAML
	helper.add_apps_to_application_tag()

	# Step 7: Generate management-zone.yaml and copy management-zone.json from meta-input
	helper.generate_management_zone_files()

	# Step 8: Validate entities via monaco (excluding app-detection-rules)
	helper.validate_entities_via_monaco()


if __name__ == '__main__':
	meta = helper.get_meta()
	action = meta.get('action')

	if action in ['deploy', 'delete', 'download', 'dry-run']:
		helper.confirm_meta(meta)
	else:
		print('Invalid action specified in meta.yaml.  Aborting...')
		exit()

	if action == 'deploy':
		deploy_flow()
	else:
		if action == 'delete':
			delete_flow()
		else:
			if action == 'download':
				download_flow()
			else:
				if action == 'dry-run':
					dry_run_flow()

	print_high('Done!')
