Python-Diana
=================================

.. image:: https://img.shields.io/pypi/v/diana.svg?style=for-the-badge
   :target: https://pypi.python.org/pypi/diana/

.. image:: https://img.shields.io/pypi/pyversions/diana.svg?style=for-the-badge
   :target: https://pypi.python.org/pypi/diana/

.. image:: https://img.shields.io/travis/xlevus/python-diana.svg?style=for-the-badge
   :target: https://travis-ci.org/xlevus/python-diana


A simple async-friendly dependency injection framework for Python 3.

Supports:
 - Async methods
 - Parametrized dependencies
 - Type annotations


Simple Example
^^^^^^^^^^^^^^

.. code-block:: python

   import diana

   class MyThing(object):
       def __init__(self, prefix):
           self.prefix = prefix

       def get(self, suffix):
           return self.prefix + suffix

   class MyModule(diana.Module):
       @diana.provider
       def provide_thing(self) -> MyThing:
           return MyThing("a_prefix_")


   @diana.injector
   def requires_a_thing(*, thing: MyThing):
       return thing.get('suffix')

   diana.injector.load_module(MyModule())

   requires_a_thing()  # returns "a_prefix_suffix"


Parametrized Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import diana
   import typing

   Snake = typing.NewType('Snake', str)

   class SnakeModule(diana.Module):
       @diana.provider
       def provide_snake(self, length: int) -> Snake:
           return Snake('-' + ('=' * length) + e)


   @diana.injector(a_snake=Snake)
   @diana.injector.param('a_snake', length=5)
   def snake_printer(a_snake):
       print(a_snake, "Hissss")

   diana.injector.load_module(SnakeModule())

   snake_printer() # Prints: -=====e Hissss


Modules
^^^^^^^

Modules provide dependencies.

.. note:: The same dependency can be provided by both an async and sync providers
   as shown in the `AType` providers below.

.. code-block:: python

   class MyModule(diana.Module):
       def load(self, injector):
           # Called when the module is loaded against `injector`.
           pass

       def unload(self, injector):
           # Called when the module is unloaded against `injector`.
           pass

       @diana.provider
       def provide_atype(self) -> AType:
           return AType()

       @diana.provider
       async def provide_atype_async(self) -> AType:
           await async_stuff()
           return AType()

       @diana.provides(BType)
       def provide_btype(self):
           return BType()


   @MyModule.provider
   def provide_ctype(module) -> CType:
       return CType()

   
   @MyModule.provides(DType)
   def provide_dtype(module):
       return DType()


Injection Styles
^^^^^^^^^^^^^^^^

There are three formats for injecting dependencies into functions

 * Type Annotation w/ inspect
 * Explicit
 * Parametrized

The following examples are all equivalent.

.. code-block:: python

   # Type Annotation w/ Inspect
   @diana.injector
   def func_a(*, a: AType, b: BType):
       pass

   # Explicit
   @diana.injector.inject(a=AType, b=BType)
   def func_a(*, a, b):
       pass

   # Parametrized.
   # Note, if the second argument to param() is omitted, the type must be
   # hinted by one of the previous methods.
   @diana.injector.param('a', AType, a_param=...)
   @diana.injector.param('b', BType, b_param=...)
   def func_a(*, a, b):
       pass

In all cases, injected arguments must be keyword-only.

Alternatively, a dependency can be manually provided, bypassing any injection.

.. code-block:: python

   func_a(a=AType(), b=BType())


Missing Features
^^^^^^^^^^^^^^^^

Compared to other dependency injection frameworks, a few features are missing.

 * Scope management - Currently there is no provision for scope to be managed by
   diana and remains the Module/provider's responsibility.
 * Constructor/Instance Injecting - it is not possible to have Diana set attributes
   on instances by decorating the class definition.
 * Thread safety - There have been no attempts to make Diana thread safe. In theory,
   if modules are only loaded once (presumably at runtime), thread safety can be managed
   by the Modules/providers.
