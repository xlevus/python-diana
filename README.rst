Python-Diana
=================================
A simple dependency injection framework for python.



Simple Example
^^^^^^^^^^^^^^

.. code-block:: python

   from diana import injector, Key


   def my_factory():
       return "FactoryValue"

   FactoryValue = Key('FactoryValue')
   injector.provide(FactoryValue, factory=my_factory)

   OtherValue = 'OtherValue'  # dependency keys can be any hashable type.
   injector.provide(OtherValue, value="OtherValue")

   # Hard injection, provider must exist
   @injector(fish=FactoryValue, cat=OtherValue)
   def foo(fish=None, cat=None):
       return (fish, cat)

   # Soft injection, missing dependencies will be filled with `None`
   @injector.soft(horse=MissingValue)
   def bar(horse):
       return horse

   foo()  # Returns `('FactoryValue', 'OtherValue')`
   bar()  # Returns `None`


You can also decorate factories:

.. code-block:: python

   from diana import injector

   FactoryValue = Key('FactoryValue')

   @injector.factory(FactoryValue)
   def my_factory():
       return "FactoryValue"


Keys
^^^^

Keys are just a simple container around hashable types. Two keys with the same
class and name will always be equal, and return the same hash.

.. code-block:: python

   class Clients(Key):
       pass

   IRC = Clients('irc')
   IRC == Clients('irc')

   Clients('irc') != Key('irc')


Aliases
^^^^^^^

You might not want to have to handle importing of 'loose' objects.
Diana supports aliases for provided dependencies.

.. code-block:: python

   from diana import injector
   FactoryValue = Key('FactoryValue')

   @injector.factory(FactoryValue, aliases=('FactoryValue', 'trout'))
   def my_factory():
       return "FactoryValue"

   @injector(fish='trout')
   def foo(fish):
       return fish

   foo()  # Returns "FactoryValue"


Contextual Overrides
^^^^^^^^^^^^^^^^^^^^

In some situations, you may not want to use the default value for a
given dependency (e.g. testing). You can override the default
temporarily like so:


.. code-block:: python

   from diana import injector
   FactoryValue = Key('FactoryValue')

   @injector.factory(FactoryValue)
   def my_factory():
       return "FactoryValue"

   @injector(fish='trout')
   def foo(fish):
       return fish

   with injector.override(FactoryValue, factory=lambda: "Other"):
       foo()  # Returns "Other"

   foo()  # Returns "FactoryValue"

.. caution:: Contextual overrides are not thread safe.


Scopes
^^^^^^

The lifecycle of provided dependencies can be managed with scopes. A few
scopes are shipped with Diana by default.

.. code-block:: python

   from diana import injector, Const
   FactoryValue = Key('FactoryValue')

   @injector.factory(FactoryValue, scope=Const)
   def my_factory():
       time.sleep()
       return "FactoryValue"

   @injector(fish=FactoryValue)
   def foo(fish):
       return fish

   foo()
   foo()  # `my_factory` is not called a second time.

