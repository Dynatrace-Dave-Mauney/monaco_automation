import os
import yaml


def get_deobfuscate_data():
    with open('deobfuscate.yaml', 'r') as file:
        document = file.read()
        return yaml.load(document, Loader=yaml.FullLoader)


def deobfuscate_directory(directory):
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(subdir, file)
            new_file = deobfuscate_string(file)
            if new_file != file:
                os.rename(path, os.path.join(subdir, new_file))

    for subdir, dirs, files in os.walk(directory):
        for dir_name in dirs:
            new_dir_name = deobfuscate_string(dir_name)
            if new_dir_name != dir_name:
                os.rename(os.path.join(subdir, dir_name), os.path.join(subdir, new_dir_name))

    for subdir, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(subdir, file)
            # dump_file(path)
            if '.exe' not in path:
                fin = open(path, "rt")
                data = fin.read()
                data = deobfuscate_string(data)
                fin.close()
                fin = open(path, "wt")
                fin.write(data)
                fin.close()


def deobfuscate_string(string):
    deobfuscate_data = get_deobfuscate_data()
    account = deobfuscate_data.get('account', '')
    tenants = deobfuscate_data.get('tenants', [])
    tokens = deobfuscate_data.get('tokens', [])

    if account == '' or len(tenants) != 3 or len(tokens) != 3:
        print("deobfuscate.yaml file must contain an account string, "
              "a list of three tenants and a list of three tokens. Aborting!")
        exit()

    tenant1 = tenants[0]
    tenant2 = tenants[1]
    tenant3 = tenants[2]

    token1 = tokens[0]
    token2 = tokens[1]
    token3 = tokens[2]

    new_string = string

    if '$tenant' in string.lower() or '$account' in string.lower():
        new_string = new_string.replace('$tenant1$', tenant1.lower())
        new_string = new_string.replace('$tenant2$', tenant2.lower())
        new_string = new_string.replace('$tenant3$', tenant3.lower())

        new_string = new_string.replace('$TENANT1$', tenant1.upper())
        new_string = new_string.replace('$TENANT2$', tenant2.upper())
        new_string = new_string.replace('$TENANT3$', tenant3.upper())

        new_string = new_string.replace('$account$', account.lower())
        new_string = new_string.replace('$ACCOUNT$', account.upper())

    if '$token' in new_string:
        new_string = new_string.replace('$token1$', token1)
        new_string = new_string.replace('$token2$', token2)
        new_string = new_string.replace('$token3$', token3)

    return new_string


if __name__ == '__main__':
    deobfuscate_directory('uwm-transition')
