Guide d'utilisation
====================


Cette section est destinée à tous ceux souhaitant utiliser la solution Esc@pad afin de produire un contenu pédagogique utilisable via un mini-site Web, ou via les plateformes de e-learning ([LMS](https://en.wikipedia.org/wiki/Learning_management_system)) Moodle et EDX. Nous abordons les points suivants:

* les étapes préliminaires: i.e la préparation d'un dépot git contenant les fichiers sources de cours, l'enregistrement de ce dépôt sur Esc@pad, l'éventuel ajout du webhook sur la plateforme git adoptée
* La modification des sources du cours en suivant la structuration proposée
* la génération du mini-site web correspondant au contenu de cours édité, et la récupération des archives exportables (EDX, IMSCC)


## Principe général

Le principe d'Esc@pad consiste à transformer une arborescence de modules de cours en différents formats d'exports (mini-site web et archives pour LMS). Le point de départ est donc un dossier contenant un ou plusieurs modules de cours, appelé "programme de cours", à l'instar des cours [Culture Numérique](https://culturenumerique.univ-lille3.fr/) qui comprennent plusieurs modules et qui sont générés par Esc@pad à partir des sources disponibles sur [ce dépôt GitHub](https://github.com/CultureNumerique/cn_modules).

Chaque module de cours doit suivre la syntaxe qui est basée sur le format Markdown pour le contenu de cours, et sur le format GIFT pour la rédaction de quiz. Les fichiers source doivent ensuite suivre une structuration définie dans la [section syntaxe](syntaxe.html). Le résultat de l'export est un dossier contenant un mini-site Web (un dossier de fichiers HTML) reprenant tous les modules de cours et incluant les liens vers des archives IMSCC et EDX (e.g [réutiliser le module CultureNumerique - Internet](https://culturenumerique.univ-lille3.fr/module1.html#sec_A) ). Pour plus de détails sur l'usage des archives EDX et IMSCC-Moodle, et les correspondances adoptés avec le modèle Esc@pad, voir le chapitre  [export](export.html).

L'illustration ci-dessous reprend la chaine éditoriale complète:

1. Le point de départ est un fichier source au format Markdown+GIFT et structuré selon les guides Culture Numérique. Il peut s'éditer depuis n'importe quel éditeur de texte.
2. Les fichiers sources sont synchronisé sur une plateforme git
3. à chaque modification, le service hébérgé sur escapad.univ-lille3.fr régénère le mini-site web et les archives IMSCC-Moodle et EDX.

![workflow](media/cn_workflow.jpg)

## Obtenir et éditer les fichiers sources des modules de cours

### Dépôt git

Esc@pad est pensé pour le travail collaboratif et l'application nécessite l'url d'un dépôt git contenant les fichiers sources de votre programme de cours. Le premier prérequis est donc de disposer d'un compte sur un fournisseur de dépôt git, comme :

- [GitHub](http://github.com/)
- [FramaGit](https://framagit.org/public/projects)
- [BitBucket](https://bitbucket.org/)
- [Gitlab](https://gitlab.com/)
- ou celui de votre choix dans [cette liste](https://en.wikipedia.org/wiki/Comparison_of_source_code_hosting_facilities)

Nous vous conseillons donc pour démarrer de partir de ce [ce dépôt exemple](https://github.com/CultureNumerique/course_template) proposant un patron de programme de cours et que vous pourrez ensuite modifier. A ce niveau 2 choix:

- *(le + simple)* Si vous avez choisi GitHub, forker simplement le dépôt `course_template` depuis GitHub à l'aide du bouton "fork"
- Si vous avez choisi un autre fournisseur git, téléchargez le dépôt localement, puis téléversez votre clone local sur votre compte en suivant les consignes de votre fournisseur.

Dans les 2 cas vous disposerez ainsi de l'adresse "git" de votre propre version d'un dossier de cours transformable par Esc@pad.


### Edition du contenu

Selon votre fournisseur git, vous pouvez soit éditer directement depuis l'interface web (possible par ex. sur GitHub, FramaGit/GitLab, etc), soit "cloner" votre dépôt localement et le modifier à partir d'un éditeur de texte. Idéalement, choisissez un éditeur reconnaissant la syntaxe Markdown sur laquelle Esc@pad s'appuie. Dans le deuxième cas, vous aurez à maitriser l'environnement git qui est expliqué par exemple [ici](https://www.atlassian.com/git/tutorials/)

La structure du template de programme de cours est la suivante:


    - module1/
        - moncours.md
        - media/
            - uneimage.png
            - image2.jpg
    - home.md
    - logo.png
    - title.md        

- un programme de cours se décompose en "modules" chacun contenu dans un dossier nommé `moduleX` avec `X` le numéro de chaque module qui déterminera l'ordre dans lequel les modules sont rangés.
- dans chaque dossier de module, il y a un fichier `moncours.md` et un dossier `media` contenant les images insérées dans chaque module de cours. La syntaxe utilisé pour éditer le fichier `moncours.md` un module de cours est expliquée sur [cette page](syntaxe.html)

Ensuite, pour personnaliser le mini-site qui sera généré par l'application, vous pouvez modifier les autres fichiers:

- dans le fichier home.md (ce présent fichier), remplacer le texte par le contenu de votre page d'accueil.
- pour personnaliser le logo remplacez le fichier `logo.png` par le fichier de votre choix que vous renommerez `logo.png|jpg|gif` en fonction du type d'image utilisée.
- enfin, pour personnaliser le titre de votre programme de cours, éditer le fichier `title.md` et, sans le renommer, insérez votre titre en première ligne.


### Cas particulier de la page d'accueil

Si aucun fichier `home.md` n'est présent dans le dossier de cours, le parser Escapad utilisera le fichier `default_home.html` situé dans [le code source de cn_app](https://github.com/CultureNumerique/cn_app) dans le dossier `templates`.

## Générer le site vitrine et les archives

Une fois que vous avez modifié votre contenu et mis à jour votre dépôt git, vous pouvez passer à l'étape de génération du site vitrine et des archives IMS et EDX.

6. pour générer votre site, connectez vous sur l'application web Esc@pad http://escapad.univ-lille3.fr/admin, loguez-vous avec les accès qui vous ont été fournis,  et cliquez sur "Ajouter un dépôt".
7. renseignez le champs "url du dépôt" avec l'adresse de votre url git, modifiez au besoin la branche par défaut. Validez.
3. depuis la page listant les "repositories", les liens "build" et "visit" permettent de respectivement générer et de visiter le mini-site généré par Esc@pad.
5. La fonctionnalité "Build and zip" permet de télécharger un fichier zip contenant le mini-site web généré
2. Les archives d'export IMS (nommées e.g `module5.imscc.zip`) et EDX (e.g `module5_edx.tar.gz`) sont disponibles pour chaque module du site généré (menu en haut à droite), à la section "Réutilisez ce module" (valable aussi lorsque "build and zip" est utilisé)


### Importer dans EDX

Dans le studio EDX, une fois dans la page de votre cours (la fonction "créer un cours
depuis une archive EDX" n'est à notre connaissance pas encore disponible), cliquez sur "importer".
Suivez ensuite les étapes. Plus d'explications [ici](http://edx.readthedocs.io/projects/edx-partner-course-staff/en/latest/releasing_course/export_import_course.html)


### Importer l'IMS-CC dans Moodle

Esc@pad peut générer un fichier `module_folder.imscc.zip` qui peut
être importé dans Moodle en tant que cours (cf [restauration d'un cours
depuis une archive IMSCC sous Moodle](https://docs.moodle.org/28/en/IMS_Common_Cartridge_import_and_export)).

1. Allez dans *Administration > Administration du cours > Restauration*
2. Selectionnez votre archive avec *Choisir un fichier..* ou glisser la dans l'emplacement flêché.
3. Appuyer sur *RESTAURATION*
4. Choisissez les différentes options suivant vos préférences.
5. **ATTENTION** Dans la partie 4, pour ne pas perdre vos droits d'enseignant, mettez *'Oui'* pour *Conservez vos rôles et droits d'accès actuels* et oui également si vous souhaitez conserver les groupes.
6. Votre cours s'est normalement généré.

Cette archive contient également toutes les activités avec les questions
associées déjà intégrées.


### Afficher les bonnes réponses et les feedbacks dans le site vitrine

Il est possible d'activer l'option permettant d'afficher les réponses et les feedbacks des questions des tests inclus dans *tous* les modules pour la version Web uniquement (les autres exports LMS contiennent dans tous les cas les bonnes réponses, mais qui ne s'affichent que sous certains conditions, selon les réglages propre à votre instance de LMS).

Usage :

- Pour activer l'option "show feedback" au niveau d'un dépôt sur escapad, il faut éditer la fiche de ce dépôt
- depuis la liste des dépôts cliquer sur le dépot de son choix
- cocher la case "show feedback"
- Enregistrer
- ensuite chaque "build" intégrera les feedbacks; il n'y a pas de sous-dossier "staging" ou autre supplémentaire
- pour revenir en arrière, il suffit d'éditer à nouveau la fiche détaillée d'un dépôt et de décocher la case puis enregistrer ET de régénérer le site, sinon les feedbacks et réponses seront encore visibles

## Automatisation de le génération des contenus

Cette section s'adresse à ceux souhaitant automatiser la ré-génération des contenus à chaque publication de changement (commit+push) sur leur dépôt de cours.

Sur la page détaillée de chaque dépôt, accessible en cliquant sur le nom du dépôt, le lien "Build link" peut être utilisé comme webhook pour les plateformes Git le supportant (framagit, github). Ce mécanisme de webhook est proposé par certaines plateformes git (GitHub, FramaGit, etc.) et permet de renseigner une url qui sera appelée (requête POST) à chaque fois qu'un certains nombres d'actions (paramétrables) sont réalisées sur votre dépôt.

Dans le cas de GitHub, l'ajout de webhook se fait de la manière suivante depuis la page d'un dépôt:
- Settings
- Webhooks
- Add webhook
- coller le lien "build" copié depuis Esc@pad dans le champ "Payload URL"
- laisser les autres champs à leur valeurs par défaut et cliquer sur "Add webhook"

Généralement l'action par défaut est le "push" qui correspond à la publication des dernières mises à jour d'un dépôt par l'un des contributeurs au dépôt de code. Ainsi, après avoir ajouté l'adresse "Build" de votre dépôt Esc@pad comme webhook, à chaque mise à jour de votre code source de cours (commit+push), le site vitrine sera régénéré et visible à l'adresse "Visit".
