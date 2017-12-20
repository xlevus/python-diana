Python-Diana
=================================
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

   if __name__ == '__main__':
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


   @diana.inject(a_snake=Snake)
   @diana.param('a_snake', length=5)
   def snake_printer(a_snake):
       print(a_snake, "Hissss")

   if __name__ == '__main__':
       diana.injector.load_module(SnakeModule())

       snake_printer() # Prints: -=====e Hissss
