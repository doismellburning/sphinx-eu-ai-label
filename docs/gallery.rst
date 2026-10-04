Gallery
=======

Each example shows the rendered label, then the source that produced it.

Kinds
-----

The Commission publishes three icons. With no argument, the directive uses ``basic``.

.. ai-label:: basic

.. code-block:: rst

   .. ai-label:: basic

.. ai-label:: generated

.. code-block:: rst

   .. ai-label:: generated

.. ai-label:: modified

.. code-block:: rst

   .. ai-label:: modified

Variants
--------

Each icon comes in ``black``, ``white``, ``black-50`` and ``white-50``. The ``-50``
variants are 50% transparent, and the white ones are for dark backgrounds. The dark
panels below come from this site's own CSS, added with ``:class:``.

.. ai-label:: generated
   :variant: black

.. code-block:: rst

   .. ai-label:: generated
      :variant: black

.. ai-label:: generated
   :variant: black-50

.. code-block:: rst

   .. ai-label:: generated
      :variant: black-50

.. ai-label:: generated
   :variant: white
   :class: dark-panel

.. code-block:: rst

   .. ai-label:: generated
      :variant: white
      :class: dark-panel

.. ai-label:: generated
   :variant: white-50
   :class: dark-panel

.. code-block:: rst

   .. ai-label:: generated
      :variant: white-50
      :class: dark-panel

The default variant is ``auto``, which shows ``black`` or ``white`` depending on the
reader's ``prefers-color-scheme``. This site sets ``eu_ai_label_variant = "black"``
because its theme has no dark mode.

Text
----

For ``basic``, the text goes before the icon, so it reads as a sentence ending in "AI".

.. ai-label:: basic
   :text: Summary generated with

.. code-block:: rst

   .. ai-label:: basic
      :text: Summary generated with

For the other kinds, the text goes after the icon.

.. ai-label:: modified
   :text: Illustrations modified with AI

.. code-block:: rst

   .. ai-label:: modified
      :text: Illustrations modified with AI

An empty ``:text:`` shows the icon on its own, even if ``eu_ai_label_texts`` sets text
for that kind.

.. code-block:: rst

   .. ai-label:: modified
      :text:

Alignment
---------

.. ai-label:: generated
   :align: left

.. code-block:: rst

   .. ai-label:: generated
      :align: left

.. ai-label:: generated
   :align: center

.. code-block:: rst

   .. ai-label:: generated
      :align: center

.. ai-label:: generated
   :align: right

.. code-block:: rst

   .. ai-label:: generated
      :align: right

Inline role
-----------

The role puts a label in running text.

This sentence was :ai-label:`generated`.

.. code-block:: rst

   This sentence was :ai-label:`generated`.

Add a variant after the kind, and put text before it in angle brackets, as with links.

:ai-label:`This paragraph was written with <basic black-50>`

.. code-block:: rst

   :ai-label:`This paragraph was written with <basic black-50>`
