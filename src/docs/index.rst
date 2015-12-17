Welcome to Triangula's Python documentation!
============================================

This site contains documentation for Triangula, more details can be found on GitHub_

Contents:

.. toctree::
    :maxdepth: 2
    :glob:

    config
    sixaxis
    api
    api/*



Just to show we can do graphs and maths
---------------------------------------

.. graphviz::

    digraph G {
        a->b->c;
        b->d;
        a [fillcolor=pink,style=filled];
        c [label="hello world"]
        d [];
        e [];
    }

Some inline maths, for example :math:`a^2 + b^2 = c^2` or :math:`\sum_{i=1}^{10} t_i`

.. math:: e^{i\pi} + 1 = 0
    :label: euler

Euler's identity, equation :eq:`euler`, was elected one of the most
beautiful mathematical formulas.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _GitHub: https://github.com/basebot/triangula