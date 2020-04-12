class KeyMaker:
    """
    Abstraction for turning a function invocation into a cache key
    """
    def __call__(self, fn, args, kwargs):
        """
        Return a cache key based on the function called and its arguments
        """
        raise NotImplemented()


class ReprKeyMaker(KeyMaker):
    def __init__(self, hash=None, hash_args=False):
        self.hash_args = hash_args
        self.hash = hash

    def __call__(self, fn, args, kwargs):
        # Get a list of arguement names from the func_code
        # attribute on the function/method instance, so we can
        # test for the presence of self or cls, as decorator
        # wrapped instances lose frame and no longer contain a
        # reference to their parent instance/class within this
        # frame
        argnames = fn.__code__.co_varnames[:fn.__code__.co_argcount]
        is_method = len(argnames) > 0 and argnames[0] in ['self', 'cls']

        if is_method:
            args = args[1:]

        repr_all_args = ", ".join([
            repr(arg)
            for arg in args
        ] + [
            f"{repr(key)}: {repr(value)}"
            for key, value in kwargs.items()
        ])

        if self.hash_args:
            repr_all_args = self.hash_args(repr_all_args.encode('utf-8')).hexdigest()

        key = f"{fn.__module__}:{fn.__qualname__}({repr_all_args})"
        if self.hash:
            key =  self.hash(key.encode('utf-8')).hexdigest()
        return key.encode('utf-8')
