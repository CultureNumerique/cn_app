Contribuer au code d'Esc@pad
============================

Cette section est dédiée aux contributeurs du code d'Escapad et décrit comment contribuer au projet Esc@pad dans les meilleurs conditions.


Architecture
------------

Le code d'Escapad est décomposé comme suit:

- le parser dont le point d'entrée est ``src/cnExport.py``
- l'application Web qui exécute le script du parser via une application Django
- le fichier "requirements.txt" contient les dépendances pour ces 2 parties du code.

**Le parser**

Cette partie du code réside dans les dossiers:

- pygiftparser (module installé dans le virtualenv depuis Git):

	responsable du découpage et du parsing des questions rédigées en GIFT dans les sous-section de type Activité; gère également l'export web des questions. Source du package : https://github.com/mtommasi/pygiftparser

- src:

    - cnExport.py : c'est le script de départ; il amorce le parsing et contrôle les différents exports directemenr (Web) ou via  toEDX.py ou toIMS.py.
    - model.py : contient le modèle; le parsing est amorcé par la création d'un objet Module défini dans ce modèle
    - fromGIFT.py : module qui surchage les classes de :mod:`pygiftparser` en ajoutant la transformation des objets GIFT en XML pour EDX et IMS-CC.
    - utils.py : contient quelques méthodes utilitaires pour l'écriture de fichiers et certains filtres
- templates: La génération du mini-site et de l'archive EDX utilise des templates écrit en Jinja2 et situé dans ce dossier.
- static : dossier regroupant les fichiers js, css, etc. utilisés par la version mini-site web de l'export. Ce dossier est donc copié tel quel dans chaque export web.
- logs : contient les logs uniquement pour cnExport

**l'application web**

Cette application web est écrite au sein du framework Django (version 10). Tout le code écrit suit la documentation au plus près. Il est conseillé de faire au moins le premier tutoriel Django pour prendre en main ce framework.

Son code est situé dans les dossiers:

- cn_app : paramètres globaux
- escapad : la "sous-application" qui gère les dépôts:

    - admin.py : paramétrage de l'interface d'admin utilisée et localisée à l'url `/admin`. C'est la seule interface web permettant d'interagir avec l'application Escapad.
    - apps.py : paramétrage de l'application
    - forms.py : utilisé par l'interface d'admin pour effectuer certaines opérations avant la soumission d'un nouvel objet Repository
    - models.py : défini le modèle de Repository
    - signals.py : exploite le mécanisme de signals de Django et relié donc au évènements de création, édition, ou suppression d'objets Repository
    - urls.py : définition des patterns d'urls spécifique à l'application escapad
    - views.py : définition du code permettant de faire exécuter le script pour un dépôt donné. L'emplacement des fichiers sources et les fichiers générés est défini dans le fichier site_settings.py et expliqué dans la documentation d'installation
    - utils.py : qqs méthodes utilitaires, notamment celle à qui est délégué l'exécuption du script cnExport.py
- les logs de l'application Django sont situés dans le fichier debug.log dont l'emplacement est défini dans le fichier cn_app/site_settings.py
- le fichier manage.py n'est pas à modifier à priori (sauf cas avancé)

Contribuer au code
------------------

*Requirement*
- Avoir un compte GitHub.

Pour nous aider sur le projet Culture Numérique, forker ce repository : 
https://github.com/CultureNumerique/cn_app

Toutes les modifications doivent s'effectuer sur votre instance forkée et doivent être testée avant d'envoyer une pull-request. Pour plus de sûreté, travailler sur une nouvelle branche ( pour plus d'aide : https://help.github.com/categories/collaborating-with-issues-and-pull-requests/)


Couverture de tests
--------------------

La stratégie de tests présente différents aspects:
Chaque module de src est testé dans un fichier de tests qui lui est propre.

1. model_test.py : le test du parsing des fichiers de code source de cours qui aboutit à la construction d'un modèle de cours (cf :class:`model.Module`); On teste également les fonctions des classes de model.
2. edx_test & ims_test: le test de la génération des exports IMS et EDX. On vérifie que l'archive est correctement générée et comme pour model_test.py, on vérifie la bonne structure de chaque format de question suite à sa modification en XML.
3. utils_test.py & cnexport_test.py, une stratégie de test plus granulaire qui consiste à tester chaque méthode séparemment en vérifiant la cohérence des entrées et sorties (WIP).


Pour lancer les tests:

- ``$ cd tests``
- ``$ pytest`` 
ou

- ``$ pytest --cov=src --cov=pygiftparser``
pour avoir le taux de couverture des fichiers src.

On peut également lancer les tests avec ``python``:

- ``python all_test.py`` pour lancer tous les tests.
- ``python [nom_du_fichier_test].py``

Paquages de test
~~~~~~~~~~~~~~~~

- `Unittest <https://docs.python.org/2/library/unittest.html>`_
- `Mock <https://docs.python.org/3/library/unittest.mock.html>`_
- `Pytest <https://pypi.python.org/pypi/pytest>`_
- `Coverage <https://coverage.readthedocs.io/en/coverage-4.4.1/#quick-start>`_  permet de voir le taux de couverture des tests :

	- ``$ coverage run [nom_du_module_test].py``
Pour avoir un aperçu graphique :

	- ``$ coverage html``
qui crée les fichiers html pour visualiser quelles lignes sont couvertes.
- `Coveralls <https://pypi.python.org/pypi/python-coveralls/>`_  


Utilisation des web-services d'intégration continue
---------------------------------------------------

Travis.ci
~~~~~~~~~
Travis CI est un logiciel libre et un service en ligne utilisé pour compiler et tester le code source des logiciels développés, notamment en lien avec le service d'hébergement du code source GitHub.

**Comment fonctionne Travis ?**

Travis capture les push et pull-request sur un projet GitHub et créer un environnement temporaire grâce aux lignes de commande cachées dans un fichier .travis.yml. On peut ainsi tester si il n'y a pas soucis de compilation, ou également automatiser les tests.

**Architecture fichier .travis.yml**

Plus d'infos `ici
<https://docs.travis-ci.com/user/customizing-the-build>`_.

- *language* : le langage du projet (ici python)

- *before_script* : 
	- lance toutes les commandes nécessaires à la mise en place de l'instance.
	- chaque commande est listée comme ceci.

- *script* : c'est ici que nous lançons les tests.

- *after_success* : action à réaliser si tout s'est bien passé. (Dans notre cas, on fait appel à l'autre web-service, ``coveralls`` (voir partie coveralls)
	
Pour utiliser Travis :
 - rendez vous sur https://travis-ci.org/
 - connecter vous via votre compte GitHub.
 - attendez quelques secondes le temps que Travis se synchronise avec votre compte GitHub.
 - dans le menu à gauche, appuyer sur le '+' à droite de 'My Repositories'
 - activer la synchronisation de votre fork du projet (normalement : [votre_pseudo]/cn_app), le petit rouage permet d'ouvrir les options de build.
 - le fichier .travis.yml n'est normalement pas à ajouter car il est déjà présent dans le projet.
 - si tout s'est bien passé, lors de votre prochain push, travis lancera automatiquement les tests pour vous !

Si vous avez un soucis, une `documentation <https://docs.travis-ci.com/user/getting-started>`_ très détaillée est disponible sur Travis.

Si vous n'êtes pas seul à travailler sur votre fork, les autres développeurs n'auront qu'à suivre les 3 premières instructions pour avoir accès aux informations des différents builds.

*Warning*


Par défault, Travis envoie un e-mail à chaque modification pour notifier le chef de projet des résultats des builds. Pour désactiver cette option, insérer :

   ::

       notifications: 
		email: false

dans le fichier .travis.yml.


Coveralls.io
~~~~~~~~~~~~
.. _coveralls:

Coveralls, comme Travis, est un web-service permettant de voir rapidement le nombre de lignes de code couvertes par les tests. Coveralls s'appuie sur les builds de Travis pour s'exécuter.

*Warning* Il faut obligatoire configurer Travis pour pouvoir utiliser Coveralls

**Comment utiliser Coveralls ? :**

- se rendre sur https://coveralls.io/
- comme pour Travis, connecter vous via votre compte GitHub.
- dans le menu à gauche, cliquez sur 'Add Repos'
- synchoniser votre repository forké en l'activant
- si vous avez configurer correctement Travis, Coveralls se lancera au prochain push.



Ajouter des tests
~~~~~~~~~~~~~~~~~

*TODO*


- Test des web services développés en Django: dans ce cas il s'agit de contrôler la manipulation des fichiers et l'exécution des appels web.
- Test pour les méthodes utililées par escapad_formulaire ( `cnExportLight.py`, méthodes avec `Light` dans le nom des différents modules,
à vérifier avec coverage)
- Certains tests ont la mention `#TODO` car ils ont besoin d'être complété.

*Warning*


Si vous voulez ajouter un fichier de tests, veiller à bien lancer son exécution dans le fichier all_test.py en ajoutant cette ligne:
   ::

       os.system('python [nom_du_nouveau_fichier_de_test].py')

En effet, coverage utilise ce fichier pour vérifier le taux de couverture des lignes exécutées. 


Pistes d'améliorations de l'application
---------------------------------------

Tests
~~~~~
Voir plus haut.

Résoudre le problème des accents dans les gifts 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pour Compréhension, Activité et Activitée Avancée, les accents ne passent plus dans.
Problème dans l'ouverture du fichier qu'il faudra ouvrir en `UTF-8` mais
cela semble poser des soucis (voir dans `createModule` ou ``generateArchive`).

Fichier d'erreur pour l'utilisateur
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lorsque l'utilisateur upload ses cours sur Esc@pad, il se peut qu'il y ait des erreurs de syntaxe.
Pour informer l'utilisateur, un logging a été mis en place pour repertorier ses erreurs. Toutes
les erreurs n'ont pas été répertoriées et il faudrait lui rappeler la hiérarchie de son cours 
pour qu'il puisse rapidement vérifier que la génération de son cours n'a pas posé de soucis.

Pour l'instant les erreurs répertoriées (dans `model.py` grâce à la ligne `logging.warning(String)` :

- Les cours sans titre de niveau 2 (##) sont placés automatique sous un titre `Cours`.
- Il faut commencer son cours par un titre de niveau 1 (#).
- L'utilisateur peut mettre une option dans le header qui n'existe pas (exemple -> Chicken: cotcot)

Insérer des médias dans une archive imscc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Dans le dossier IMS, créer un dossier static et insérer ses images.
2. Dans imsmanifest.xml:

   1. Pour chaque image:

      ::

          <resource identifier="img1" type="webcontent">
              <file href="static/nom_image1.png"/>
          </resource>

   2. Pour chaque ressource utilisant les images : Ajouter les
      dépendances dès qu’elles sont nécessaires.

      ::

          <resource href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html" type="webcontent" identifier="doc_0_1">
              <file href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html"/>
              <dependency identifierref="img1"/>
              <dependency identifierref="img2"/>

          </resource>

3. Dans les fichiers html (dossier webcontent), faire référence avec
   src= "../static/image.png"

   ::

       <img alt="hiragana" src="../static/hira.gif"/>

**Comment fonctionne le code ?**

1. On copie tous les médias dans un dossier static à l'intérieur du dossier IMS
dans `generateImsArchiveLight(module, moduleOutDir, zipFile, mediaData, mediaNom)`.

2. Dans `model`, la fonction `parseMediaLinks()` dans la classe `Subsection`
permet d'extraire toutes les images du texte en leur associant un ID unique.
Place tous les médias dans l'attribut `medias`.

3. Pour chaque image, on va créer une balise dans manifest.xml de la
   sorte :

   ::

       <resource identifier="img1" type="webcontent">
       <file href="static/nom_image1.png"/>
       </resource>

dans la fonction `generateIMSManifest` de `toIMS`.

4. Pour chaque fichier, on recherchera les médias qui leurs sont
   associés, et on créera dans le fichier manifest.xml les dépendances
   dans le fichier en question :

   ::

           <resource href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html" type="webcontent" identifier="doc_0_1">
               <file href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html"/>
               <dependency identifierref="img1"/>
               <dependency identifierref="img2"/>

           </resource>

dans la fonction `generateIMSManifest` de `toIMS`.

5. On modifie ainsi la source de l'image du `/nom_du_module/media/nom_image.ext` à `../static/nom_image.ext`
dans `IMSMediaLinks()` de `model`.

**Problème**

Cette solution semble fonctionner pour les images dans les cours et dans les questions
de texte mais pas dans les feedbacks généraux. Pas de piste particulière.

Sortir le dossier static de `cn_app`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sortir le dossier static contenant toutes les images, icônes, css, etc, de cn_app (Pour que ce soit plus modulable pour une utilisation ouverte à tous).
Notamment grâce au header optionnel où on devrait pouvoir changer la CSS.

Changement de vocabulaire
~~~~~~~~~~~~~~~~~~~~~~~~~

Réfléchir au vocabulaire plus "métier"  et moins techno sur escapad : exemple repository ne me plaît pas

Différencier certains templates de `cn_app` dans les cours
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Réfléchir à ce qui doit être dans les templates de cours ou les templates de cn_app. Exemples : Gérer la page contact, ...

Passage à Python3
~~~~~~~~~~~~~~~~~
Il faut exécuter `cn_export` avec python3 et voir toutes les erreurs générées.
 
