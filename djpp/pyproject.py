import os
import sys
import toml
import inspect as ins
states = ('development', 'docker', 'production')


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
    if os.getenv(production_env[0]) == production_env[1]:
        settings['DEBUG'] = False
    for app in new_data['apps'].copy():
        for key in app:
            if key not in states:
                settings.update(convert(key, app[key], path, new_data))
            elif (key == states[0] and settings['DEBUG']) or \
                 (key == states[1] and os.getenv(docker_env)) or \
                 (key == states[2] and not settings['DEBUG']):
                for k in app[key]:
                    settings.update(convert(k, app[key][k], path, new_data))
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
    trimmed = {'poetry': {}, 'apps': [{}]}
    django = data['tool']['django']
    for key in django:
        if key not in ('apps'):
            trimmed['apps'][0].update({up(key, upper): django[key]})
    apps = django.get('apps')
    if apps:
        for app in apps:
            trimmed['apps'].append({})
            for key in apps[app]:
                trimmed['apps'][-1].update({up(key, upper): apps[app][key]})
    for app in trimmed['apps']:
        for state in states:
            if app.get(state):
                part = app.get(state).copy()
                for key in part:
                    app[state].update({up(key, upper): part[key]})
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
            for i in value:
                value[i] = conv_value(value[i], path, data)
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
    result = data['apps'][0].get(key, [])
    if pos:
        result.insert(pos, value)
    else:
        result.append(value)
    return result


def up(key, upper):
    return key.upper() if upper and key not in states else key


def load_all(path=None):
    """Loads all data from the pyproject file as a dict.
    You can set custom path with the path parameter."""
    data, _ = check(path)
    return data
