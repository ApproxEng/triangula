Welcome to Triangula's Python documentation!
============================================

.. note::

    Coming to EMF2016_ ? I'll be doing a talk_ about this code, maths and all the hardware on the Sunday at 10am, come
    along and heckle me for my poor documentation skills and over-caffeinated presentation style!

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
    maths

.. _GitHub: https://github.com/basebot/triangula

.. _PiWars: http://piwars.org

.. _Holonomic: https://en.wikipedia.org/wiki/Holonomic_(robotics)

.. _EMF2016: https://www.emfcamp.org

.. _talk: https://www.emfcamp.org/line-up/2016/11-holonomic-robots-and-why-you-should-build-one