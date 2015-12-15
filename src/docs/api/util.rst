triangula.util: Helpful Things
==============================

The ``triangula.util`` package contains functionality that's generally useful but which doesn't belong anywhere else. At
the moment this includes a function to get the current IP address and a class :class:`triangula.util.IntervalCheck`
which is incredibly helpful when handling potentially slow responding hardware, or hardware which cannot be polled at
above a certain rate, within a fast polling loop such as Triangula's task framework or PyGame's event loop.

Using IntervalCheck
-------------------

You'll often find you're running code in an event loop, this is a loop which has to run as fast as possible and which
services everything you need to handle - input, output, providing feedback, reading sensors etc. Some of your sensors
or output devices probably can't keep up with this rate, and it's possible you want to do expensive calculations that
don't have to be done on every single iteration through the loop. You want the loop to complete as fast as possible to
keep everything responsive, so littering your code with ``time.sleep()`` calls is a bad idea, but you also need to
ensure that e.g. you only update your motor speeds at most twenty times per second.

The :class:`triangula.util.IntervalCheck` can be used in several different ways to handle several corresponding timing
issues:

Rate limiting
    You want to update e.g. an LCD display within a fast polling event loop, but the display will flicker like mad if
    you try to update every time around the loop, and the delay imposed by performing the update will unreasonably slow
    down everything else.

    .. code-block:: python

        from triangula.util import IntervalCheck
        once_per_second = IntervalCheck(interval = 1)
        while 1:
            if once_per_second.should_run():
                # Do the thing that must happen at most once per second
                pass
            # Do the stuff that has to happen every time around the loop
            pass

    This will ensure that the code within the ``if`` statement will only be run at most once per second. Note that this
    makes no guarantee about delays between the code finishing and the next iteration starting - if the code in this
    block takes exactly a second to run there will be no delays at all.

Delay padding
    You have a piece of hardware which can be written to or read from, but you must leave at least a certain delay
    between consecutive operations. You don't want to just use ``time.sleep()`` because you'd like to be able to get on
    with other things while you wait.

    You can use two different kinds of delay here. The first will sleep for a minimum delay since the last time the
    sleep method was called:

    .. code-block:: python

        from triangula.util import IntervalCheck
        delay = IntervalCheck(interval = 1)
        while 1:
            # If it's been less than a second since we last ran, sleep until it'll be exactly a second
            delay.sleep()
            # Run the thing you want to run
            pass

    This, again, makes no guarantee that there will actually be a delay. The second's delay (in this case) is counted
    from when the previous sleep() call was made. There will be cases where you absolutely must have a delay between a
    block of code completing and the next time that same block is called, for this you can use the ``with`` binding
    provided by the IntervalCheck:

    .. code-block:: python

        from triangula.util import IntervalCheck
        padding = IntervalCheck(interval = 1)
        while 1:
            with padding:
                # Any code here will be run immediately the first time, then on
                # subsequent occasions, on entry to the ``with`` block there will
                # be a pause if required such that the time from the previous
                # completion of the ``with`` block to the start of this one is at
                # least one second
                pass

.. automodule:: triangula.util
    :members: