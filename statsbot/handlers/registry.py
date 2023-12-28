class HandlerRegistry(type):
    handlers = {}

    def __new__(cls, name, bases, dct):
        handler_cls = super().__new__(cls, name, bases, dct)
        if handler_cls.key is not None:
            assert handler_cls.key not in cls.handlers, (
                f"Handler for key {handler_cls.key} is already registered"
            )
            cls.handlers[handler_cls.key] = handler_cls
        return handler_cls

    @classmethod
    def get_handler(cls, key):
        return cls.handlers.get(key)

    @classmethod
    def get_handlers(cls):
        return cls.handlers.values()

