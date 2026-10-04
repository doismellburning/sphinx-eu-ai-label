Configuration
=============

These values go in ``conf.py``.

.. list-table::
   :header-rows: 1

   * - Setting
     - Default
     - Description
   * - ``eu_ai_label_variant``
     - ``"auto"``
     - Default colour variant: ``auto``, ``black``, ``white``, ``black-50`` or ``white-50``.
       ``auto`` uses ``black`` in light mode and ``white`` in dark mode, using
       ``prefers-color-scheme``.
   * - ``eu_ai_label_size``
     - ``"2.5em"``
     - Icon height, as any CSS length. The icons have wide margins built in, so the
       visible mark is smaller than this.
   * - ``eu_ai_label_texts``
     - ``{}``
     - Text to show next to each kind's icon, for example
       ``{"generated": "Généré par IA"}``. The directive's ``:text:`` option overrides it.

``auto`` follows the reader's operating system or browser setting. It also follows a
theme's own light/dark switch if the theme sets a ``data-theme="light"`` or
``data-theme="dark"`` attribute on ``<html>`` or ``<body>``, as Furo, PyData and Book do.
For other themes with a switch, set a fixed variant.

This site's configuration:

.. literalinclude:: conf.py
   :language: python
