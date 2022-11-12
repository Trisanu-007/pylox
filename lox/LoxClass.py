from LoxCallable import LoxCallable
from LoxInstance import LoxInstance

class LoxClass(LoxCallable) : 
    def __init__(self, name, methods, superclass) -> None:
        self.name = name
        self.methods = methods
        self.superclass = superclass

    def __str__(self) -> str:
        return self.name

    def call(self, interpreter, arguments): 
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer is not None: 
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def find_method(self, name): 
        if name in self.methods.keys(): 
            return self.methods[name]
        
        if self.superclass is not None : 
            return self.superclass.find_method(name)

    def arity(self):
        initializer = self.find_method("init")
        if initializer is None :
            return 0
        return initializer.arity()
        