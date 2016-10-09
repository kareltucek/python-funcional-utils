#!/usr/bin/python
#
# Introduction
# ============
# This library provides sensible api to python's functional features. 
# We define a new class F, which wraps a data container (e.g., a list
# or a map) and provides common functional constructs as methods.
# This allows transformations to be chained in a readable manner.
#
# The api is inspired by Scala.
#
# Example
# =======
# F(['dog', 'fish', 'elephant'])\               # first we we create a list container and wrap it in F
#         .map(lambda a: a[0].upper + a[1:])\   # animal names are capitalized
#         .zipWithIndex()\                      # every record is zipped with its index, e.g. the result is F([('dog', 0), ('fish',1)...])
#         .map(lambda a: (a[1], a[0]))\         # the pair is swapped
#         .toMap()\                             # the pair representation is converted to a dictionary
#         .get()                                # finally we strip the F, so we have a plain dictionary
#
# Dictionaries
# ============
# Note that dictionaries are automatically transformed into sequences 
# of tuples. This is due to python's map's semantics, which otherwise
# maps only keys (values are discarded). For performance reasons, we
# do not convert the list interpretation back automatically.

def identity(a):
    return a

def bfold(c, a, b):
    if c:
        return a
    else: 
        return b

class F:
    def _mapToSeq(self, m):
        return map(lambda k: (k, m.get(k)), m)

    def __init__(self, v):
        self.val = v
        return 

    def __str__(self):
        return self.val.__str__()

    def __repr__(self):
        return "F(" + self.__str__() + ")"

    def _toSeq(self):
        if(type(self.val) == dict):
            return self._mapToSeq(self.val)
        elif(type(self.val) == str):
            return self.val
        elif(type(self.val) == list):
            return self.val
        elif(type(self.val) == set):
            return self.val
        else:
            print "warning: unflattenning an object of type" + type(self.val)
            return [self.val]

    # Returns the data container, i.e., strips the F
    def get(self):
        return self.val

    # Debug method printing type and value
    def check(self, msg = ""):
        print msg, type(self.val), ": ", self.val
        return self

    # Log prints the contained container using 'f' if 'on' is true; Returns again itself, so the computation can continue
    def log(self, f = identity, on = True):
        if(on):
            print f(self.val)
        return self

    # As log, but prints on every line
    def logLines(self, f = identity, on = True):
        if(on):
            for a in self._toSeq():
                print f(a)
        return self

    # Converts the data into a representation suitable for mapping.
    # i.e., dictionary is transformed into a list of pairs. This is necessary because python destroys values when dictionary is mapped.
    def toSeq(self):
        return F(self._toSeq())

    # Inverse transformation of toSeq. I.e., if 'a' is dictionary, contained container is transformed into dictionary.
    def toOrig(self, a):
        if(type(a) == dict and type(self.val) != dict):
            return F(dict(self.val))
        else:
            return self

    # flattens the structure. E.g., takes a list of dictionaries and merges them into a single element.
    def flatten(self):
        if(len(self.val) == 0):
            return F([])
        elif(type(self.val[0]) == dict):
            return F(reduce(lambda a,b: a.update(b), self.val, dict()))
        elif(type(self.val[0]) == set):
            return F(reduce(lambda a,b: a.union(b), self.val, dict()))
        elif(type(self.val[0]) == str):
            return F(reduce(lambda a,b: a + " " +  b, self.val, ''))
        elif(type(self.val[0]) == list):
            return F(reduce(lambda a,b: a + b, self.val, []))
        elif(type(self.val[0]) == bool):
            return F(reduce(lambda a,b: a and b, self.val, True))
        else:
            print "warning: unhandled type in flatten:", type(self.val)
            return F(None)

    # Transforms the underlaying container to a dictionary.
    def toMap(self):
        return F(dict(self.val))

    # Maps elements using the function f: A -> B.
    def map(self, f):
        return F(map(f, self._toSeq()))

    # Maps the entire container (e.g., F(['a','b']).mapFull(''.join) produces F('ab').
    def mapFull(self, f):
        return F(f(self.val))

    # Maps the content over f and flattens the result. I.e., the expected type is 
    # f: A -> Container[B], mapping a type List[A] to Container[B]
    # (of course all container types may be used)
    def flatMap(self, f):
        return F(map(f, self._toSeq())).flatten()

    # Takes a function f: (A x B) -> B and an element 'd' of type B. Then the elements are 
    # added to 'd' using 'f'. I.e., F([a,b,c]).fold(d, f) => F((a f (b f (c f d))))
    def fold(self, d, f):
        if(type(self.val) == bool):
            if(self.val):
                return F(d)
            else:
                return F(f)
        else:
            return F(reduce(f, self._toSeq(), d))

    # Takes a function f: (A x A) -> A. Then interleaves the elements by f.
    # E.g., F([a,b,c]).reduce(f) => F((a f (b f c)))
    def reduce(self, f):
        seq = self._toSeq()
        if(len(seq) == 0):
            return F(None)
        else:
            return F(reduce(f, seq[1:], seq[0]))

    # Applies a map f: A -> A x N by adding indices to the elements of type A
    def zipWithIndex(self):
        seq = self._toSeq()
        return F([(seq[i], i) for i in range(len(seq))])

    # Filters the content of the contained container by f: A -> Boolean.
    def filter(self, f):
        return F(filter(f, self._toSeq())).toOrig(self.val)

    # Extracts keys from a container of pairs (typically a dictionary)
    def keys(self):
        return F(self._toSeq()).map(lambda a: a[0])
            
    # Extracts values from a container of pairs (typically a dictionary)
    def values(self):
        return F(self._toSeq()).map(lambda a: a[1])

    # Maps only the second elements in a container of pairs (typically a dictionary)
    def mapValues(self, f):
        return F(self._toSeq()).map(lambda a: (a[0], f(a[1])))

    # Maps only the first elements in a container of pairs (typically a dictionary)
    def mapKeys(self, f):
        return F(self._toSeq()).map(lambda a: (f(a[0]), a[1]))


