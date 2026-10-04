sphinx-eu-ai-label
==================

.. ai-label:: basic
   :text: Parts of this site were written with

A `Sphinx <https://www.sphinx-doc.org/>`_ extension for adding the European Commission's
`icons for labelling AI-generated content
<https://digital-strategy.ec.europa.eu/en/policies/eu-icons-labelling-ai-generated-content>`_
to your documentation.

This site is built with the extension, so every label on it is real output.

.. important::

   This is an unofficial project. It is not affiliated with or endorsed by the European
   Commission or the AI Office. Using these icons does not make you compliant with
   Article 50 of the EU AI Act. You are still responsible for meeting its disclosure
   requirements. Using the icons also does not signal that you have signed the
   Code of Practice on marking and labelling of AI-generated content.

Quick start
-----------

Install it from GitHub:

.. code-block:: console

   pip install git+https://github.com/doismellburning/sphinx-eu-ai-label

Add it to your ``conf.py``:

.. code-block:: python

   extensions = [
       # ...
       "sphinx_eu_ai_label",
   ]

Then label a page:

.. code-block:: rst

   .. ai-label:: generated

.. ai-label:: generated

The `README <https://github.com/doismellburning/sphinx-eu-ai-label#readme>`_ has the full
reference, including accessibility and placement guidance.

.. toctree::
   :maxdepth: 2

   gallery
   myst
   configuration
