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

``auto`` follows the reader's operating system or browser setting. It does not follow a
theme's own light/dark switch (such as Furo's), so set a fixed variant if that matters.

This site's configuration:

.. literalinclude:: conf.py
   :language: python
