# Pistes d'améliorations de l'application
===========================================================

Il réside encore certains problèmes sur l'application Esc@pad.
Nous souhaitons notamment permettre à l'utilisateur de disposer d'archive d'import EDX/IMS qui contiendrait des médias.
Ces médias pourraient être directement uploadés sur Moodle/Edx en même temps que le cours.

Ce qui se faisait précédemment était que les médias étaient stockés sur le serveur Esc@pad et les cours Moodle/Edx accédaient à ces médias depuis l'instance Esc@pad.


## Insérer des médias dans une archive edx
1. Dans le dossier EDX, créer un dossier static et insérer ses images.
2. Dans les fichiers HTML (dossier html) : faire référence aux images avec src="/static/kata.png"
    ```
    <img alt="katakana" src="/static/kata.png"/>
    ```

## Insérer des médias dans une archive imscc

1. Dans le dossier IMS, créer un dossier static et insérer ses images.
2. Dans imsmanifest.xml:
    1. Pour chaque image:
        ```
        <resource identifier="img1" type="webcontent">
            <file href="static/nom_image1.png"/>
        </resource>
        ```
    2. Pour chaque ressource utilisant les images :
    Ajouter les dépendances dès qu’elles sont nécessaires.
        ```
        <resource href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html" type="webcontent" identifier="doc_0_1">
            <file href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html"/>
            <dependency identifierref="img1"/>
            <dependency identifierref="img2"/>

        </resource>
        ```


3. Dans les fichiers html (dossier webcontent), faire référence avec src= "../static/image.png"
    ```
    <img alt="hiragana" src="../static/hira.gif"/>
    ```

## Piste de code pour EDX

1. Copier les images dans un dossier static.

2. Modifier absolutizeMediaLinks / Créer relativeEDXMediaLinks
Afin de pouvoir effectuer le toHTML correctement ?

## Piste de code pour IMSCC

1. Copier les médias dans un dossier static.

2. Créer fonction similaire a parseVideoLinks dans la classe cours (model.py).
Celle-ci créerait un dictionnaire de données pour chaque média, on leur associerait des identifiants « mediaX ».

3. Pour chaque image, on va créer une balise dans manifest.xml de la sorte :
    ```
    <resource identifier="img1" type="webcontent">
    <file href="static/nom_image1.png"/>
    </resource>
    ```
4. Pour chaque fichier, on recherchera les médias qui leurs sont associés, et on créerait dans le fichier manifest.xml les dépendances dans le fichier en question :
    ```
        <resource href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html" type="webcontent" identifier="doc_0_1">
            <file href="webcontent/1-2presentation-des-deux-alphabets_webcontent.html"/>
            <dependency identifierref="img1"/>
            <dependency identifierref="img2"/>

        </resource>
    ```

5. Modifier absolutizeMediaLinks/ Créer relativeIMSMediaLinks
Afin de pouvoir effectuer le toHTML() correctement ?

