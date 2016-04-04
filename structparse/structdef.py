"""Allows defining serializable simple types and structs."""

from collections import namedtuple

def unzip(x): return zip(*x)

class Type:
    """Defines a type that can be serialized and unserialized."""

    @staticmethod
    def unpack_from(buf):
        """Constructs a Python value from the given buffer.

        Signature: buffer -> (parsed data, rest of the buffer)
        """
        raise NotImplementedError

    def pack(self):
        """Packs itself into `bytes`, returns that buffer.

        Signature: data -> buffer
        """
        raise NotImplementedError

    @classmethod
    def unpack(cls, buf):
        """Unpacks the whole buffer into this Type.

        Raises ValueError if len(buf) doesn't exactly match the type size.
        """
        x, rest = cls.unpack_from(buf)
        if len(rest) > 0: raise ValueError('buffer size != struct size')
        return x


class _StructMixin(Type):
    """Mixin providing the `pack`, `unpack` and `unpack_from` methods for a struct."""
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and args[0].__class__ is cls:
            return args[0]  # assumes immutability
        if len(args) + len(kwargs) != len(cls._fields):
            raise TypeError('Must be initialized with exactly {} arguments'.format(len(cls._fields)))
        field_types = dict(zip(cls._fields, cls._fieldtypes))
        to_convert = dict(zip(cls._fields, args), **kwargs)
        converted = { n: field_types[n](v) for (n, v) in to_convert.items() }
        return super().__new__(cls, **converted)

    @classmethod
    def unpack_from(cls, buf):
        """Constructs a new instance by unpacking the given buffer."""
        vals = []
        for t in cls._fieldtypes:
            val, buf = t.unpack_from(buf)
            vals.append(val)
        return cls(*vals), buf

    def pack(self):
        """Returns itself packed as `bytes`."""
        return b''.join([ t.pack(x) for t,x in zip(self._fieldtypes, self) ])


def struct(name, *fields):
    """Creates a "C struct" -- a namedtuple that can be packed and unpacked."""
    fieldtypes, fieldnames = unzip(fields)
    class Cls(_StructMixin, namedtuple(name, fieldnames)): pass
    Cls.__name__ = name
    Cls._fieldtypes = fieldtypes
    return Cls
