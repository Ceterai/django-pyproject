import os
import sys
import toml
import inspect as ins


def load(path=None, upper=True, docker_env='DJANGO_ENV',
         production_env=('DJANGO_ENV', 'production'), module=None):
    """Use this method to load django settings from the pyproject.toml file.

    ### Params:

    - path - filepath of your toml file. If you don't specify it, django-
      pyproject will look in the folder that contains
      your project folder (with settings.py).
    - upper - whether to convert lowercase variable names to uppercase.
    - docker_env - django-pyproject will look for this env variable. If it
      finds the variable, django-pyproject will include
      settings from [tool.djange.docker].
    - production_env - django-pyproject will look for the env variable from
      production_env[0]. If it finds the variable and its contents match with
      production_env[1], django-pyproject will include
      settings from [tool.djange.production].
    - module - you can set custom module to which all
      settings will be uploaded.

    > Note: docker settings override normal and apps settings, production
     settings override all settings.
    """
    if not module:
        module = os.getenv('DJANGO_SETTINGS_MODULE')
    data, path = check(path)
    new_data = trim(data, upper)
    settings = {'DEBUG': True}
    for key in new_data:
        if key not in ('production', 'docker', 'apps', 'poetry'):
            settings.update(convert(key, new_data[key], path, new_data))
    apps = data.get('tool').get('django').get('apps')
    for app in apps:
        for key in apps[app]:
            settings.update(convert(key, apps[app][key], path, new_data))
    if os.getenv(docker_env):
        new_data = data.get('tool').get('django').get('docker')
        if new_data:
            for key in new_data:
                settings.update(convert(key, new_data[key], path, new_data))
    if os.getenv(production_env[0]) == production_env[1]:
        settings['DEBUG'] = False
        new_data = data.get('tool').get('django').get('production')
        if new_data:
            for key in new_data:
                settings.update(convert(key, new_data[key], path, new_data))
    for key in settings:
        setattr(sys.modules[module], key, settings[key])


def check(path=None, ppt='pyproject.toml'):
    if not path:
        f = ins.getouterframes(ins.currentframe(), 2)[2].filename
        path = os.path.join(os.path.dirname(os.path.dirname(f)), ppt)
    try:
        data = toml.load(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Path to {ppt} is not \
set or is incorrect, and default path didn't work. Broken filepath: {path}")
    except toml.TomlDecodeError:
        raise toml.TomlDecodeError(f'Your {ppt} is configured improperly.')
    try:
        data['tool']['django']
    except KeyError:
        raise KeyError(f"Your {ppt} doesn't have a [tool.django] section.")
    return data, path


def trim(data, upper):
    trimmed = {'poetry': {}, 'docker': {}, 'production': {}, 'apps': {}}
    django = data['tool']['django']
    for key in django:
        if key not in ('production', 'docker', 'apps', 'poetry'):
            trimmed.update({up(key, upper): django[key]})
    apps = data['tool']['django'].get('apps')
    if apps:
        for app in apps:
            trimmed['apps'].update({app: {}})
            for key in apps[app]:
                trimmed['apps'][app].update({up(key, upper): apps[app][key]})
    docker = data['tool']['django'].get('docker')
    if docker:
        for key in docker:
            trimmed['docker'].update({up(key, upper): docker[key]})
    production = data['tool']['django'].get('production')
    if production:
        for key in production:
            trimmed['production'].update({up(key, upper): production[key]})
    poetry = data['tool'].get('poetry')
    if poetry:
        for key in poetry:
            trimmed['poetry'].update({key: poetry[key]})
    return trimmed


def convert(key, value, path, data):
    if isinstance(value, dict):
        if conv_check(value, ('env',), opt=('default',)):
            if isinstance(value['env'], dict):
                value['env'] = conv_value(value['env'], path, data)
            if isinstance(value.get('default'), dict):
                value['default'] = conv_value(value['default'], path, data)
            value = os.environ.get(value['env'], value.get('default'))
        elif conv_check(value, ('path',)):
            if isinstance(value['path'], dict):
                value['path'] = conv_value(value['path'], path, data)
            value = edit_path(value['path'], path)
        elif conv_check(value, ('insert',), opt=('pos',)):
            if isinstance(value['insert'], dict):
                value['insert'] = conv_value(value['insert'], path, data)
            value = edit_var(key, value['insert'], data, value.get('pos'))
        elif conv_check(value, ('con', 'poetry', 'cat',)):
            concat = []
            for i in ('con', 'poetry', 'cat'):
                if value.get(i) is not None:
                    if i != 'poetry' and isinstance(value[i], dict):
                        concat.append(conv_value(value[i], path, data))
                    elif i != 'poetry':
                        concat.append(str(value[i]))
                    else:
                        concat.append(data['poetry'].get(value['poetry']))
            value = ''.join(concat)
        else:
            for k in value:
                value[k] = convert(k, value[k], path, data)
    return {key: value}


def conv_check(d, main, amount=1, opt=tuple(), n=0):
    for key in main:
        if key in d:
            n += 1
    if n < amount:
        return False
    for key in d:
        if key not in main and key not in opt:
            return False
    return True


def conv_value(value, path, data):
    return convert('a', value, path, data)['a']


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
    result = data.get(key, [])
    if pos:
        result.insert(pos, value)
    else:
        result.append(value)
    return result


def up(key, upper):
    return key.upper() if upper else key


def load_all(path=None):
    """Loads all data from the pyproject file as a dict.
    You can set custom path with the path parameter."""
    data, _ = check(path)
    return data
