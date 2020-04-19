import os, sys, toml, inspect


def load(path=None, upper=True, docker_env='DJANGO_ENV',
    production_env=('DJANGO_ENV', 'production'), module=None):
    """Use this method to load django settings from the pyproject.toml file.

    ### Params:

    - path - filepath of your toml file. If you don't specify it, django-pyproject will look in the folder that contains your project folder (with settings.py).
    - upper - whether to convert lowercase variable names to uppercase.
    - docker_env - django-pyproject will look for this env variable. If it finds the variable, django-pyproject will include settings from [tool.djange.docker].
    - production_env - django-pyproject will look for the env variable from production_env[0]. If it finds the variable and its contents match with production_env[1], django-pyproject will include settings from [tool.djange.production].
    - module - you can set custom module to which all settings will be uploaded.

    > Note: docker settings override normal and apps settings, production settings override all settings.
    """
    if not module:
        module = os.getenv('DJANGO_SETTINGS_MODULE')
    data, path = check(path)
    django_data = data['tool']['django']
    settings = { 'DEBUG': True }
    for key in django_data:
        if key not in ('production', 'docker', 'apps'):
            settings.update(convert(key, django_data[key], path, data, upper))
    apps = data.get('tool').get('django').get('apps')
    for app in apps:
        for key in apps[app]:
            settings.update(convert(key, apps[app][key], path, data, upper))
    if os.getenv(docker_env):
        django_data = data.get('tool').get('django').get('docker')
        if django_data:
            for key in django_data:
                settings.update(convert(key, django_data[key], path, data, upper))
    if os.getenv(production_env[0]) == production_env[1]:
        settings['DEBUG'] = False
        django_data = data.get('tool').get('django').get('production')
        if django_data:
            for key in django_data:
                settings.update(convert(key, django_data[key], path, data, upper))
    for key in settings:
        setattr(sys.modules[module], key, settings[key])
    
def check(path=None):
    if not path:
        filename = inspect.getouterframes(inspect.currentframe(), 2)[2].filename
        path = os.path.join(os.path.dirname(os.path.dirname(filename)), 'pyproject.toml')
    try:
        data = toml.load(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Path to pyproject.toml is not \
set or is incorrect, and default path didn't work. Broken filepath: {path}")
    except toml.TomlDecodeError:
        raise toml.TomlDecodeError('Your pyproject.toml is configured improperly.')
    try:
        django_data = data['tool']['django']
    except KeyError:
        raise KeyError("Your pyproject.toml doesn't have a [tool.django] section.")
    return data, path
    
def convert(key, value, path, data, upper=True):
    if upper:
        key = key.upper()
    if isinstance(value, dict):
        if 'env' in value:
            value = os.environ.get(value['env'], value.get('default'))
        elif 'path' in value:
            value = edit_path(value['path'], path)
        elif 'insert' in value:
            value = edit_var(key, value['insert'], data, value.get('pos'))
        else:
            for k in value: value[k] = convert(k, value[k], path, data, upper)
    return {key: value}
    
def edit_path(s, path):
    names = s.split('/')
    path = os.path.dirname(path)
    for i in range(1, len(names)):
        if names[i] == '..':
            path = os.path.dirname(path)
        else:
            path = os.path.join(path, names[i])
    return path
    
def edit_var(key, value, data, pos=None):
    result = data['tool']['django'].get(key, [])
    if pos: result.insert(pos, value)
    else: result.append(value)
    return result
    
def load_all(path=None):
    """Loads all data from the pyproject file as a dict.
    You can set custom path with the path parameter."""
    data, _ = check(path)
    return data
