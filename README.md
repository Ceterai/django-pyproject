# django-pyproject

## Description

This package allows you to store some/all of your settings in your pyproject.toml file (or any toml file in general).

## Installation

You can add django-pyproject to your poetry project with:

    poetry add django-pyproject

Or through pip:

    pip install django-pyproject

Neither Django nor Poetry are **not** required to use this package.

## Usage

You can use django-pyproject to import any settings specified in your pyproject file under [tool.django].

### Settings file

To import django settings from your pyproject file, use this in your settings file:

    from djpp import pyproject
    pyproject.load()

This will work only if you have a standard django project structure.  
If your pyproject file is located somewhere else or has a different name, you can specify it:

    pyproject.load('path-to-your-pyproject-file')

### PyProject file

All django settings in pyproject.toml file should be stored under [tool.django] key, like this:

    [tool.django]
    ALLOWED_HOSTS = []

You don't have to use uppercase letters for the variable names, django-pyproject will automatically convert them all. This does **not** work for dict key names:

    [tool.django]
    allowed_hosts = []

    [tool.django.databases.default]
    engine = 'django.db.backends.sqlite3'
    HOST = '127.0.0.1'
    PORT = '5432'

Will convert into:

    ALLOWED_HOSTS = []
    DATABASES = {
        'default': {
            'engine': 'django.db.backends.sqlite3',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

But what to do about relative filepaths, that you had to construct with os.path?  
You can specify filepaths separating them with '/' in inline dict under key 'path'.  
Using '..' will make django-pyproject go up a level.
Starting with '.' will make a path relative:

    base_dir = { path = "." }
    project_dir = { path = "./your_project_folder" }
    repo_dir = { path = "./.." }

This will have the same effect as the following code in settings.py:

    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

> This is assuming you have a standard django project structure.

If a value needs to be taken from an environment, use inline dict with key 'path' and optional key 'default':

    email_host_password = { env = 'SECRET_PASSWORD' }
    secret_key = { env = 'SECRET_KEY', default = 'hello' }

### Docker & Production

If some of you settings have an alternative value for when DEBUG is off, specify them in [tool.django.production]. They will override regular settings if DEBUG is off.

By default, django-pyproject applies production settings and sets DEBUG to False, if current evironment has a DJANGO_ENV variable, set to 'production'.  
You can override it with your own key and value like this:

    pyproject.load(production_env=('YOUR_KEY', 'your_value'))

If some of you settings have an alternative value for when the app is in container, specify them in [tool.django.docker]. They will override regular settings and will be overriden by production settings.

By default, django-pyproject applies docker settings, if current evironment has a DJANGO_ENV variable.  
You can override it with your own key like this:

    pyproject.load(docker_env='YOUR_KEY')

### Apps

You can group settings that belong to an external app together for easier access.  
To do that, you can list them under [tool.django.apps.your_app].  
You can also modify variables like INSTALLED_APPS from here with 'insert' key.

Here's an example for corsheaders:

    [tool.django.apps.cors]
    CORS_ORIGIN_WHITELIST = ['http://localhost:3000',]
    CORS_ALLOW_CREDENTIALS = true
    CSRF_COOKIE_NAME = "XCSRF-Token"
    INSTALLED_APPS = { insert = 'corsheaders' }
    MIDDLEWARE = { insert = 'corsheaders.middleware.CorsMiddleware', pos = 3 }

This is similar to the following python code:

    CORS_ORIGIN_WHITELIST = ('http://localhost:3000',)
    CORS_ALLOW_CREDENTIALS = True
    CSRF_COOKIE_NAME = "XCSRF-Token"
    INSTALLED_APPS.append('corsheaders')
    MIDDLEWARE.insert(3, 'corsheaders.middleware.CorsMiddleware')

### Full import

You also can simply import pyproject file (or any toml file) contents as a dict with load_all().
