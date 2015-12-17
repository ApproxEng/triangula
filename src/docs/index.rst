Welcome to Triangula's Python documentation!
============================================

This site contains documentation for Triangula, my competition entry for PiWars_ 2015.

.. youtube:: https://www.youtube.com/watch?v=pnrAbDw4_EQ

Triangula's code is a mix of Python running on a Raspberry Pi, and C code running on an Arduino microcontroller. This
site primarily addresses the Python code, which should hopefully be re-usable in other projects. To get the code from
PyPi you can run ``pip install triangula``, although this will only work properly when run on a Raspberry Pi as it
depends on some native libraries which are exclusive to Linux. I haven't tried using it on other Linux systems.

To work with the code on other platforms you'll want to clone it from GitHub_, it's available under the ASL, the same as
almost everything Python based, and should hopefully provide a good starting point for your own robot exploration. The
code should be useful to you in particular if you're interested in Holonomic_ robots, or wish to use a PlayStation3
controller with your project.

.. toctree::
    :maxdepth: 4
    :glob:

    config
    sixaxis
    api

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

.. _GitHub: https://github.com/basebot/triangula

.. _PiWars: http://piwars.org

.. _Holonomic: https://en.wikipedia.org/wiki/Holonomic_(robotics)