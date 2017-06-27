Code API
========

We document here the source code of the Escapad parser located in ``src`` folder. It is divided into 2 main parts:

1. the parser model located in ``src/model.py``
2. the rest of the parser code, that is the scripts that manipulate the files and generate the exports in Web, IMS and EDX formats


Detailed documentation of ``model.py``
--------------------------------------

This file ``model.py`` contains the logic of the Escapad parser that parse a whle course directory to build a Course Program object.
The order of presentation follows the building of Course Program structure whereby :

* a CourseProgram contains one or several modules and is stored in a repository (folder)
* A module is made of one source file that is parsed and optionnaly a media folder
* Each module has a header part for the metadata and is divided in Sections, each containing one or several activities (AnyActivity)
* Each activity can be typed as
    - Cours : can contain also video parts
    - AnyActivity that has 3 subclasses:
          - Comprehension: for simple quizzes
          - Activite (simple) : for simple exercises involving personnal research
          - ActiviteAvancee : for more advanced activity involving both research and personnal reflexion

Course Program
~~~~~~~~~~~~~~

.. autoclass:: model.CourseProgram
    :members:
    :undoc-members:


Module
~~~~~~

.. autoclass:: model.Module
    :members:
    :undoc-members:

Section
~~~~~~~

.. autoclass:: model.Section
    :members:
    :undoc-members:



Subsection
~~~~~~~~~~

.. autoclass:: model.Subsection
    :members:
    :undoc-members:


Cours
~~~~~~

Subclass of Subsection

.. autoclass:: model.Cours
    :members:
    :undoc-members:


AnyActivity
~~~~~~~~~~~

Subclass of Subsection

.. autoclass:: model.AnyActivity
    :members:
    :undoc-members:


Comprehension
~~~~~~~~~~~~~~

Subclass of AnyActivity

.. autoclass:: model.Comprehension
    :members:
    :undoc-members:


Activite
~~~~~~~~~~

Subclass of AnyActivity

.. autoclass:: model.Activite
    :members:
    :undoc-members:

ActiviteAvancee
~~~~~~~~~~~~~~~

Subclass of AnyActivity

.. autoclass:: model.ActiviteAvancee
    :members:
    :undoc-members:


Scripts du parser Escapad
-------------------------

Here we detail the code documentation of the rest of the Escapad parser.

cnExport
~~~~~~~~
.. automodule:: cnExport
  :members:

cnExportLight
~~~~~~~~~~~~~
.. automodule:: cnExportLight
  :members:

fromGift
~~~~~~~~
.. automodule:: fromGIFT
  :members:

toEDX
~~~~~
.. automodule:: toEDX
  :members:

toIMS
~~~~~
.. automodule:: toIMS
  :members:

utils
~~~~~
.. automodule:: utils
  :members:
