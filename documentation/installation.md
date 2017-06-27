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
$ pip install -e git://github.com/CelestineSauvage/pygiftparser#egg=pygiftparser
```

L'installation de toutes ces librairies reposent parfois sur des paquets "systèmes". Pour une distribution linux basée sur Debian, assurez-vous que les paquets suivants sont installés:

- libxml2-dev
- libxslt-dev
- python-libxml2
- python-libxslt1
- python-dev
- zlib1g-dev

## Installation de l'instance etherpad

Dans le dossier source contenant l’application django, cloner tout d’abord l’instance suivante d’etherpad. On a modifié l’etherpad d’origine pour qu’il puisse envoyer des appels aux fenêtres parents quand une instance est contenue dans une iframe.

### Étapes d’installation

1. Cloner l’etherpad depuis l'adresse suivante: https://github.com/lmagniez/etherpad-lite.git
    ```
    $ git clone https://github.com/lmagniez/etherpad-lite.git
    ```

2. Installer nodes.js
    Télécharger `node-install.sh` sur [ce lien](https://github.com/taaem/nodejs-linux-installer/releases) est l’exécuter :
    Plus d’informations sur l’installation: [Installation nodeJS](https://github.com/nodejs/node/wiki/Installation)

3. Installer abiword pour pouvoir faire fonctionner etherpad
(Si abiword a un dossier d'installation différent : changer dans settings.json ("abiword" : "/usr/bin/abiword",))
    ```
    $ sudo apt-get install abiword
    $ sudo apt-get install curl
    ```
    
4. Executer etherpad pour la première fois, puis quitter celui-ci une fois initialisé.
    ```
    $ cd etherpad-lite
    $ bin/run.sh
    ```
    Puis quitter l'instance après le chargement de l'instance.
    ```
    $ CTRL + C
    ```
    
5. Ajout des différents modules dans l’instance etherpad :
    Dans le dossier node_module, cloner l’ensemble des dépôts suivants, ils représentent les différents plugins de l’application.
    ```
    $ cd node_modules
    $ git clone https://github.com/lmagniez/ep_disable_format_buttons
    $ git clone https://github.com/lmagniez/ep_markdownify
    $ git clone https://github.com/lmagniez/ep_giftify.git
    $ git clone https://github.com/lmagniez/ep_post_data
    $ git clone https://github.com/lmagniez/ep_defaultPadText
    $ git clone https://github.com/lmagniez/strftime
    ```
    Redémarrer l'instance pour appliquer les changements de plugins.
    ```
    $ cd ..
    $ bin/run.sh
    ```
    
7. Configuration de mysql-server:
    Si mysql-server n'est pas installé, effectuer la commande suivante :
    ```
    $ sudo apt-get install mysql-server
    ```
    Suivre les instructions, et configurer mysql-server avec un mdp super-utilisateur.
    Dans etherpad-lite/settings.json, passer en commentaire le code suivant comme ceci :
    ```
    //"dbType" : "dirty",
      //the database specific settings
    //  "dbSettings" : {
    //                   "filename" : "var/dirty.db"
    //                 },
    ```
    Et décommenter le code suivant comme ceci :
    ```
      /* An Example of MySQL Configuration */
      "dbType" : "mysql",
      "dbSettings" : {
          "user"    : "root",
    	"host"    : "localhost",
    	"password": "MonPassword",
    	"database": "store",
    	"charset" : "utf8mb4"
      },
    ```
    Veuillez rentrer le mot de passe précédemment du super utilisateur pour pouvoir faire fonctionner la base de données etherpad.
    
    Ensuite, il va falloir créer la base de donnée qui va stocker les différents pads. Pour cela :
    ```
    $ mysql -u root -p
    <Entrer votre mot de passe root>
    > Create database store
    > quit
    ```
    On va ensuite mettre à jour les différentes relations dans etherpad en effectuant :
    ```
    $ ./bin/installDeps.sh
    ```
    Puis on redémarre l’application et on la laisse tourner
    ```
    $ ./bin/run.sh 
    ```

### Description des plugins installés

- **ep_post_data** : Utilise curl pour modifier le contenu du pad (utilisé pour l’import).
	curl -X POST --data '<DATA>' -H 'X-PAD-ID:<ID-PAD>' <URL-ETHERPAD>
	Modifie le contenu de ID-PAD en DATA
	Attention! Ne fonctionne que si le pad existe déjà, sinon ne fait que le créer.
- **strftime** : Nécessaire pour faire fonctionner ep_post_data.

- **ep_disable_format_buttons** : Supprime les boutons inutiles, pas d'édition html. (Modification d’un plugin existant).

- **ep_markdownify** : colorise et met en forme la syntaxe markdown.
	Modification des expressions régulières dans index.js
	Modification du css dans mardownify.css
- **ep_giftify** : colorise et met en forme la syntaxe gift.
	Modification des expressions régulières dans index.js
	Modification du css dans giftify.css

- **ep_default-pad-text** : création de pad avec pattern.
	Si on a un url répondant à une expression régulière donnée, on va adapter le contenu en 	fonction de ce qui a été indiqué dans le fichier de configuration.
	**Modification des pads par défaut** : Modifier dans **settings.json** dans "**ep_defaultPadText**"

    
    
    
    
    
        

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
LOGDIR='/tmp/'
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

L'idée ici est d'ajouter un site à la config Apache. Pour ceci créer un fichier `escapad.conf` dans le dossier `/etc/apache2/sites-enabled`. Le fichier doit ressembler à ceci:


```
        # URL et chemin des repo-data
        Alias /data /path/to/cnapp_install/data/repo-data

        <Directory /path/to/cnapp_install/data/repo-data>
        Require all granted

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

### Configuration Nginx

Voici un exemple de configuration avec `Nginx+gunicorn`. Il est nécessaire dans un premier temps d'installer `gunicorn` dans l'environnement virtuel par un `pip install gunicorn`. Puis ajouter le fichier suivant  dans `/etc/nginx/sites-available/` (nommer ce fichier par exemple `escapad`).

```
server{
	listen 80 default_server;
	listen [::]:80 default_server;

	# SSL configuration
	#
	# listen 443 ssl default_server;
	# listen [::]:443 ssl default_server;
	#
	# Note: You should disable gzip for SSL traffic.
	# See: https://bugs.debian.org/773332
	#
	# Read up on ssl_ciphers to ensure a secure configuration.
	# See: https://bugs.debian.org/765782
	#
	# Self signed certs generated by the ssl-cert package
	# Don't use them in a production server!
	#
	# include snippets/snakeoil.conf;

	root /var/www/html;

	# Add index.php to the list if you are using PHP
	index index.html index.htm index.nginx-debian.html;

	server_name _;

	location / {
		# First attempt to serve request as file, then
		# as directory, then fall back to displaying a 404.
		try_files $uri $uri/ =404;
	}
    # etherpad
    location /pad {        
        rewrite                /pad/(.*) /$1 break;
        rewrite                ^/pad$ /pad/ permanent; 
        proxy_pass             http://localhost:9001/;
        proxy_pass_header Server;
        proxy_redirect         / /pad/;
        proxy_set_header       Host $host;
        proxy_buffering off;
    }
    
    location /pad/socket.io {
        rewrite /pad/socket.io/(.*) /socket.io/$1 break;
        proxy_pass http://localhost:9001/;
        proxy_redirect         / /pad/;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_set_header X-Real-IP $remote_addr;  # http://wiki.nginx.org/HttpProxyModule
        proxy_set_header X-Forwarded-For $remote_addr; # EP logs to show the actual remote IP
        proxy_set_header X-Forwarded-Proto $scheme; # for EP to set secure cookie flag when https is used
        proxy_set_header Host $host;  # pass the host header                                                   
        proxy_http_version 1.1;  # recommended with keepalive connections                                                    
        # WebSocket proxying - from http://nginx.org/en/docs/http/websocket.html
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
    # static de etherpad
    location /static {
        rewrite /static/(.*) /static/$1 break;
        proxy_pass http://localhost:9001/;
        proxy_set_header Host $host;
        proxy_buffering off;
    }

    # cn_app
    location /escapad {
        proxy_pass_header Server;
    	proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_set_header X-Forwarded-For  $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header SCRIPT_NAME /escapad
        proxy_connect_timeout 10;
        proxy_read_timeout 10;

        # This line is important as it tells nginx to channel all requests to port 8000.
        # We will later run our wsgi application on this port using gunicorn.
        proxy_pass http://127.0.0.1:8000;
    }

    # static de cn_app (adapter en fonction de site-settings)
    location /escapad/static {
        autoindex on;
        alias /path/to/cn_app/collectedstatics/;
    }
	# documentation
    location /escapad-formulaire/static/documentation/ {
        # First attempt to serve request as file, then
        # as directory, then fall back to displaying a 404.
        autoindex on;
        alias /path/to/cn_app/collectedstatics/documentation/html/;
    }


}
# we're in the http context here
map $http_upgrade $connection_upgrade {
  default upgrade;
  ''      close;
}
```

Mettre à jour les liens et relancer le service
```
cd /etc/nginx/sites-enabled
rm default
ln -s ../sites-available/escapad .
service nginx restart
```

Le serveur `gunicorn` doit être lancé, la section suivante donne un exemple de script de démarrage.

### Script de déploiement

Ces deux scripts permettent de lancer `gunicorn` et `etherpad` au démarrage du serveur.

```
#! /bin/sh
### BEGIN INIT INFO
# Provides:          escapad
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Should-Start:      $nginx
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: gunicorn + nginx ubuntu init script
# Description:       gunicorn + nginx ubuntu init script
### END INIT INFO

# Author: Jeremy Chalmer
# Original Author: Nicolas Kuttler <hidden>
#
# This init script was written for Ubuntu 17.04 using start-stop-daemon.
# 
# Enable with update-rc.d escapad


# Source init-functions:
#source /lib/lsb/init-functions
. /lib/lsb/init-functions

# PATH should only include /usr/* if it runs after the mountnfs.sh script
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 

# ----- gunicorn_django configuration -----
#export PYTHONPATH=/opt/graphite/webapp
PROJECT=/path/to/cn_app
APP=cn_app.wsgi:application
PORT=8000
LOGDIR=/var/log/gunicorn		# Make sure this directory is writeable by USER!
IP=localhost
WORKERS=1
USER=www-data
GROUP=www-data
# ----- end gunicorn_django configuration -----

# Name of executable daemon
NAME=escapad
DESC=$NAME
LOGFILE="$LOGDIR/$NAME.log"

# Path to Executable
# DAEMON=$(which $NAME)
DAEMON=/path/to/virtualenv/instance/of/gunicorn

PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME

# Lay out the arguments for gunicorn using the configuration from above.
# GUNICORN_ARGS="	--user=$USER \
# 		--group=$GROUP \
# 		--daemon \
# 		--workers=$WORKERS \
# 		--bind=$IP:$PORT \
# 		--pid=$PIDFILE \
# 		--name=$NAME \
# 		--log-file=$LOGFILE \
# 		--log-level=info \
# 		-D settings.py"

GUNICORN_ARGS="	--user=$USER \
		--group=$GROUP \
		--daemon \
		--workers=$WORKERS \
		--bind=$IP:$PORT \
		--pid=$PIDFILE \
		--name=$NAME \
		--log-file=$LOGFILE \
		--log-level=info \
		$APP"

# Exit if the package is not installed
if [ ! -x "$DAEMON" ]; then {
    echo "Couldn't find $DAEMON or not executable"
    exit 99
}
fi

# Load the VERBOSE setting and other rcS variables
[ -f /etc/default/rcS ] && . /etc/default/rcS

#
# Function that starts the daemon/service
#
do_start()
{
    # Return
    #   0 if daemon has been started
    #   1 if daemon was already running
    #   2 if daemon could not be started
    
		# Test to see if the daemon is already running - return 1 if it is. 
    start-stop-daemon --start --pidfile $PIDFILE --make-pidfile --chdir $PROJECT \
        --exec $DAEMON --background --test -- $GUNICORN_ARGS  || return 1
		
		# Start the daemon for real, return 2 if failed
    start-stop-daemon --start --pidfile $PIDFILE --make-pidfile --chdir $PROJECT \
        --exec $DAEMON -- $GUNICORN_ARGS || return 2
}

#
# Function that relaods the daemon's settings by sending SIGHUP
#
do_reload()
{
    start-stop-daemon --stop --quiet --pidfile $PIDDILE --exec $DAEMON --signal 1
}

#
# Function that stops the daemon/service
#
do_stop()
{
    # Return
    #   0 if daemon has been stopped
    #   1 if daemon was already stopped
    #   2 if daemon could not be stopped
    #   other if a failure occurred
    start-stop-daemon --stop --quiet --retry=TERM/10/KILL/5 --pidfile $PIDFILE --exec $DAEMON
    RETVAL="$?"
    [ "$RETVAL" = 2 ] && return 2

    # Wait for children to finish too if this is a daemon that forks
    # and if the daemon is only ever run from this initscript.
    # If the above conditions are not satisfied then add some other code
    # that waits for the process to drop all resources that could be
    # needed by services started subsequently.  A last resort is to
    # sleep for some time.

    start-stop-daemon --stop --quiet --oknodo --retry=0/30/KILL/5 --exec $DAEMON
    [ "$?" = 2 ] && return 2

    # Many daemons don't delete their pidfiles when they exit.
		if [ -e "$PIDFILE" ]; then {
    	rm -f $PIDFILE
    }
		fi
		
    return "$RETVAL"
}


# Display / Parse Init Options
case "$1" in
  start)
 	 [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME"
	  do_start
	  case "$?" in
	    0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
	    2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	  esac
  ;;
  stop)
 	 [ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
	  do_stop
	  case "$?" in
	    0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
	    2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	  esac
  ;;
  restart)
  	log_daemon_msg "Restarting $DESC" "$NAME"
		do_stop
		  case "$?" in
		    0|1)
		    do_start
		    case "$?" in
		      0) log_end_msg 0 ;;
		      1) log_end_msg 1 ;; # Old process is still running
		      *) log_end_msg 1 ;; # Failed to start
		    esac
	   ;;
    *)
      # Failed to stop
    log_end_msg 1
    ;;
  esac
  ;;
  reload)
  	log_daemon_msg "Reloading $DESC" "$NAME"
	  do_reload
	  case "$?" in
	    0) log_end_msg 0 ;;
	    *) log_end_msg 1 ;;
	  esac
  ;;
  status)
      if [ -s $PIDFILE ]; then
          pid=`cat $PIDFILE`
          kill -0 $pid >/dev/null 2>&1
          if [ "$?" = "0" ]; then
              echo "$NAME is running: pid $pid."
              RETVAL=0
          else
              echo "Couldn't find pid $pid for $NAME."
              RETVAL=1
          fi
      else
          echo "$NAME is stopped (no pid file)."
          RETVAL=1
      fi
  ;;
  *)
  echo "Usage: $SCRIPTNAME {start|stop|status|restart|reload}" >&2
  exit 3
  ;;
esac
:

```

```
#!/bin/sh
### BEGIN INIT INFO
# Provides: etherpad-lite
# Required-Start: $local_fs $remote_fs $network $syslog
# Required-Stop: $local_fs $remote_fs $network $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: starts etherpad lite
# Description: starts etherpad lite using start-stop-daemon
### END INIT INFO
PATH="/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin"
LOGFILE="/var/log/etherpad-lite/etherpad-lite.log"
EPLITE_DIR="/path/to/etherpad-lite"
EPLITE_BIN="bin/run.sh"
USER="root"
GROUP="root"
DESC="Etherpad Lite"
NAME="etherpad-lite"
set -e
. /lib/lsb/init-functions

start() {
	echo "Starting $DESC... "
	start-stop-daemon --start --chuid "$USER:$GROUP" --background --make-pidfile --pidfile /var/run/$NAME.pid --exec "$EPLITE_DIR/$EPLITE_BIN" -- $LOGFILE || true
	echo "done"
}

# Nous avons besoin de cette fonction pour assurer la totalité du processus lorsqu'il sera tué
killtree() {
	local _pid=$1
	local _sig=${2-TERM}
	for _child in $(ps -o pid --no-headers --ppid ${_pid}); do
		killtree ${_child} ${_sig}
	done
	kill -${_sig} ${_pid}
}

stop() {
	echo "Stopping $DESC... "
	while test -d /proc/$(cat /var/run/$NAME.pid); do
		killtree $(cat /var/run/$NAME.pid) 15
		sleep 0.5
	done
	rm /var/run/$NAME.pid
	echo "done"
}

status() {
	status_of_proc -p /var/run/$NAME.pid "" "etherpad-lite" && exit 0 || exit $?
}

case "$1" in
	start)
		start
		;;
	stop)
		stop
		;;
	restart)
		stop
		start
		;;
	status)
		status
		;;
	*)
		echo "Usage: $NAME {start|stop|restart|status}" >&2
		exit 1
		;;
esac
exit 0
```
