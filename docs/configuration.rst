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
     - Icon height for directive labels, as any CSS length. The icons have wide margins
       built in, so the visible mark is smaller than this.
   * - ``eu_ai_label_inline_size``
     - ``"1.75em"``
     - Icon height for role labels. It's smaller so that labels in running text don't
       stretch the line as much.
   * - ``eu_ai_label_texts``
     - ``{}``
     - Text to show next to each kind's icon, for example
       ``{"generated": "Généré par IA"}``. The directive's ``:text:`` option overrides it.
   * - ``eu_ai_label_page``
     - ``None``
     - A label for the top of every page, such as ``"generated"`` or ``"modified white"``.
       A page can set its own with ``:ai-label:`` metadata, or opt out with
       ``:ai-label: none``.
   * - ``eu_ai_label_latex_size``
     - ``"2.5em"``
     - Icon height for directive labels in LaTeX output, as a LaTeX length.
   * - ``eu_ai_label_latex_inline_size``
     - ``"1.75em"``
     - Icon height for role labels in LaTeX output, as a LaTeX length.

``auto`` follows the reader's operating system or browser setting. It also follows a
theme's own light/dark switch if the theme sets a ``data-theme="light"`` or
``data-theme="dark"`` attribute on ``<html>`` or ``<body>``, as Furo, PyData and Book do.
For other themes with a switch, set a fixed variant.

This site's configuration:

.. literalinclude:: conf.py
   :language: python
