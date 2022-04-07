class Wrapper(object):
    """
    Wrapper class that provides proxy access to an instance of some
    internal instance.
    @see `StackOverflow answer <https://stackoverflow.com/a/9059858>`_.

    **Usage:**

    ::

        class DictWrapper(Wrapper):
            __wraps__ = dict

        wrapped_dict = DictWrapper(dict(a=1, b=2, c=3))

        # make sure it worked....
        assert "b" in wrapped_dict                        # __contains__
        assert wrapped_dict == dict(a=1, b=2, c=3)        # __eq__
        assert "'a': 1" in str(wrapped_dict)              # __str__
        assert wrapped_dict.__doc__.startswith("dict()")  # __doc__

    """

    __wraps__  = None
    __ignore__ = "class mro new init setattr getattr getattribute"

    def __init__(self, obj):
        if self.__wraps__ is None:
            raise TypeError("base class Wrapper may not be instantiated")
        elif isinstance(obj, self.__wraps__):
            self._obj = obj
        else:
            raise ValueError("wrapped object must be of %s" % self.__wraps__)

    # provide proxy access to regular attributes of wrapped object
    def __getattr__(self, name):
        return getattr(self._obj, name)

    # create proxies for wrapped object's double-underscore attributes
    class __metaclass__(type):
        def __init__(cls, name, bases, dct):

            def make_proxy(name):
                def proxy(self, *args):
                    return getattr(self._obj, name)
                return proxy

            type.__init__(cls, name, bases, dct)
            if cls.__wraps__:
                ignore = set("__%s__" % n for n in cls.__ignore__.split())
                for name in dir(cls.__wraps__):
                    if name.startswith("__"):
                        if name not in ignore and name not in dct:
                            setattr(cls, name, property(make_proxy(name)))
