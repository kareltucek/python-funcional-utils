#!/usr/bin/python

#want: map, flatMap, reduce, fold, filter, flatten, zipWithIndex, toSeq, toMap, keys, values, mapValues

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

    def get(self):
        return self.val

    def check(self, msg = ""):
        print msg, type(self.val), ": ", self.val
        return self

    def log(self, f = identity, on = True):
        if(on):
            print f(self.val)
        return self

    def logLines(self, f = identity, on = True):
        if(on):
            for a in self._toSeq():
                print f(a)
        return self

    def echo(self):
        print self.val
        return self

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

    def toSeq(self):
        return F(self._toSeq())

    #def toOrig(self, a):
    #    return self

    def toOrig(self, a):
        if(type(a) == dict and type(self.val) != dict):
            return F(dict(self.val))
        else:
            return self

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

    def keys(self):
        return F(self._toSeq()).map(lambda a: a[0])
            
    def values(self):
        return F(self._toSeq()).map(lambda a: a[1])

    def mapValues(self, f):
        return F(self._toSeq()).map(lambda a: (a[0], f(a[1])))

    def mapKeys(self, f):
        return F(self._toSeq()).map(lambda a: (f(a[0]), a[1]))

    def toMap(self):
        return F(dict(self.val))

    def map(self, f):
        return F(map(f, self._toSeq())).toOrig(self.val)

    def mapFull(self, f):
        return F(f(self.val))

    def flatMap(self, f):
        return F(map(f, self._toSeq())).flatten().toOrig(self.val)

    def fold(self, d, f):
        if(type(self.val) == bool):
            if(self.val):
                return F(d)
            else:
                return F(f)
        else:
            return F(reduce(f, self._toSeq(), d))

    def reduce(self, f):
        seq = self._toSeq()
        if(len(seq) == 0):
            return F(None)
        else:
            return F(reduce(f, seq[1:], seq[0]))

    def zipWithIndex(self):
        seq = self._toSeq()
        return F([(seq[i], i) for i in range(len(seq))])

    def filter(self, f):
        return F(filter(f, self._toSeq())).toOrig(self.val)



