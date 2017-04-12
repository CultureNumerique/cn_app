Installation
============

Cette section est destinée aux usagers techniciens ou aux contributeurs du code qui souhaitent installer l'application localement ou sur un serveur.

## Prérequis et installation minimale

Tout d'abord, il est nécessaire de disposer d'un environnement Python 2. Nous préconisons fortement l'adoption d'un environnement virtuel comme proposé par l'outils [`virtualenv`](https://virtualenv.pypa.io/en/stable/installation/) qui permet d'isoler des environnements python. Une fois virtualenv installé, créez un environnement:

    $ virtualenv cnappenv

Ceci créera un dossier `cnappenv`. Placez-vous dans ce dossier, et clonez l'application:

    $ cd cnappenv
    $ git clone https://github.com/CultureNumerique/cn_app
    $ cd cn_app
    $ source ../bin/activate

Ensuite, les librairies nécessaires sont installées via `pip` en utilisant le fichier de dépendences fourni `requirements.txt` de cette manière:

```
$ pip install -r requirements.txt
```

L'installation de toutes ces librairies reposent parfois sur des packets "systèmes". Pour une distribution linux basé sur Debian, assurez-vous que les paquets suivants sont installés:

- libxml2-dev
- libxslt-dev
- python-libxml2
- python-libxslt1
- python-dev
- zlib1g-dev


## Exécution du script en local

En supposant que vous disposez d'un dossier local `mon_dossier_de_cours` contenant votre contenu de cours structuré en respectant [le guide d'utilisation](usage.html) et la [syntaxe Esc@pad](syntaxe.html),  le script `src/cnExport.py` vous permet d'obtenir un export Web contenant les archives importable dans Moodle ou EDX. L'usage de base est le suivant:

```
$ cd cnappenv
$ source bin/activate
$ cd cn_app
$ python src/cnExport.py -r chemin/vers/mon_dossier_de_cours -d /chemin/vers/dossier/cible [OPTIONS]
```

Cette commande génère uniquement le mini site web reprenant tous les modules présent dans le dossier `mon_dossier_de_cours`. Les options suivantes sont disponibles (et doivent être placées à la suite de la commande ci-dessus à la place de `[OPTIONS]`):

- `-m moduleX moduleY ` : exporte uniquement les modules contenus dans les dossiers de module `moduleX`, `moduleY`
- `-i` : génère en plus l'archive IMSCC (IMS Common Cartridge) de chaque module de cours et la place dans le dossier d'export de chaque module avec le nom `moduleX.imscc.zip`
- `-e` : génère en plus l'archive EDX de chaque module de cours et la place dans le dossier d'export de chaque module avec le nom `moduleX_edx.tar.gz`
- `-f` : inclue les feedbacks dans l'export HTML, i.e dans le minisite.


## Running the Web application locally

For the Django web app cn_app to work, you need to copy `cn_app/site_settings.template.py` as `cn_app/site_settings.py`:

```
 $ cp cn_app/site_settings.template.py cn_app/site_settings.py

```
and change the settings depending on your running environment (dev, production, domain name, database, etc) as explained in comments in the file.

Then do the database migrations in order to bootstrap the database with the schemas needed by the application:
```
$ python manage.py migrate
```

Then start the web application locally with:

```
$ python manage.py runserver
```

and go to web adress at `http://localhost:8000`

## Déploiement sur un serveur

Il s'agit ici de voir un peu plus en détail la stratégie de déploiement.
Pour le déploiement sur un serveur, nous préconisons de suivre les conseils [donnés par la documentation Django](https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/modwsgi/) ou bien ceux disponible sur [ce support de cours](https://openclassrooms.com/courses/developpez-votre-site-web-avec-le-framework-django/deployer-votre-application-en-production). Nous revoyons les étapes principipales de l'installation, mais les prérequis vu [ci-avant](#prerequis-et-installation-minimale) sont toujours les mêmes.

### Arborescence des fichiers et dossiers

Par rapport à un déploiement standard, la difficulté ici réside dans le fait que plusieurs fichiers et dossiers sont manipulés à chaque exécution de l'application, ce qui peut poser problème si les droits d'accès ne sont pas gérés de manière cohérente. Nous recommandons d'utiliser l'arborescence suivants pour l'installation d'Esc@pad sur un serveur (considérons pour la suite que `cnuser` est le compte de l'usager, `www-data` le compte lié au serveur --dans notre cas Apache+mod_wsgi--):

```
    - cnapp (dossier d'installation)
        - cnappenv/ (owner = cnuser)
              (dossier de l'environement virtuel contenant les binaires et librairies)
        - cn_app/ (owner = cnuser)
              (le dossier de code source cloné depuis le dépôt git)
        - data/ (owner = www-data)
              - db.sqlite3 (fichier de base de donnée, uniquement si vous choisissez SQLite)
              - debug.log (fichier de debug du script cnExport.py)
              - repo-data/
                    - repositories (dossier contenant les dépôts de code source)
                    - sites (dossier où sont copiés les mini-sites web générés)
```

### Configuration Django

Après avoir créé le dossier `cnappenv` avec l'applicatif `virtualenv`, et cloné le code source dans `cn_app`, vous pouvez installer les dépendances avec `pip` depuis le dossier `cn_app` (après avoir activé votre environment):
```
$ pip install -r requirements.txt
```
 Ensuite, créez le dossier `data` et à l'interieur de celui-ci `repo-data`. Les autres fichiers (`db.sqlite3` et `debug.log`) et dossiers (`repositories` et `sites`) seront créés automatiquement plus tard).

 Passons à présent à la configuration du fichier `site_settings.py` qu'il faut créer à partir du patron `site_settings.template.py`. Modifiez le de cette manière:

 - Ajoutez l'url du serveur dans le champ `ALLOWED_HOSTS`
 - base SQLite: indiquez le chemin absolu vers le fichier de base de donnée:
```
     # SQLite conf
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.sqlite3',
             'NAME': '/path/to/cnapp_install/data/db.sqlite3',
```
- chemin vers le dossier data:
```
    DATA_DIR = '/path/to/cnapp_install/data/'
```
- pour le logging, indiquez aussi le chemin absol vers le fichier de log:
```
    LOGGING = {
            (...)
            'apps_handler': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': 'path/to/cnapp_install/data/debug.log',
```
A ce stade vous pouvez lancer la migration et la collecte de fichiers statiques:
```
    $ ./manage.py migrate
    $ ./manage.py collectstatic
```
Ce qui aura pour effet de créer le fichier et peupler la base de données, ainsi que copier les fichiers statiques (CSS, images, JS) dans le dossier `cn_app/collectedstatics`.

Pour tester que l'installation a bien fonctionné, lancer le serveur local:
```
$ ./manage.py runserver
```

### Configuration Apache

L'idée ici est d'ajouter un site à la config Apache. Pour ceci créer un fichier escapad.conf dans le dossier `/etc/apache2/sites-enabled`. Le fichier doit ressembler à ceci:


```
        # URL et chemin des repo-data
        Alias /data /path/to/cnapp_install/data/repo-data

        <Directory /path/to/cnapp_install/data/repo-data>
        Require all granted
        </Directory>

        # URL et chemin pour les fichiers static de Django
        Alias /static /path/to/cnapp_install/cn_app/collectedstatics

        <Directory /path/to/cnapp_install/cn_app/collectedstatics>
        Require all granted
        </Directory>

        # CHemin et PythonPath pour l'appli web escapad
        WSGIScriptAlias / /path/to/cnapp_install/cn_app/cn_app/wsgi.py
        WSGIPythonPath /path/to/cnapp_install/cn_app:/path/to/cnapp_install/cnapp_env/lib/python2.7/site-packages

        <Directory /path/to/cnapp_install/cn_app/cn_app>
          <Files wsgi.py>
          Require all granted
          </Files>
        </Directory>

```
