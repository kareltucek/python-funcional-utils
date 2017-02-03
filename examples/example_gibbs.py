#!/usr/bin/python

import random
import fp
from fp import *

#
# This is implementation of the gibb's motif-search algorithm. 
# 
# Problem:
#   Input: list of DNA sequences
#   Output: pattern of length k which occures in all input sequences with at most l mutations
#
# Algorithm:
# 1) pick one motif-candidate from each sequence
# 2) pick one of the sequences and refine the motif as follows:
#    - compute median string (the actual global motif candidate)
#    - compute its probability profile
#    - compute similarity of every mer of the selected sequence with the median string
#    - select new motif candidate for this sequence by roulette-wheel selection with proportional probabilities defined by the similarity
# 3) Repeat 2 until the result converges

#fasta header processing for readFasta
def procHeader(h):
    if h.startswith('>'):
        return h.replace('|', ' ').split(' ')[0] + "|"
    else:
        return h

#reads DNA sequences from file fn; Returns dictionary of DNA sequences
def readFasta(fn,verbose=1):
    with open(fn, 'rU') as fileObj:
        return F(fileObj.readlines())\
                .map(procHeader)\
                .map(lambda a: a.replace('\n', ''))\
                .mapFull(''.join)\
                .mapFull(lambda a: a.split('>'))\
                .filter(lambda a: '|' in a)\
                .map(lambda a: a.split('|'))\
                .map(lambda a: (a[0], a[1]))\
                .logLines(lambda a: "Sequence " + str(a[0]) + " of length " + str(len(a[1])) + " was read.", verbose)\
                .toMap()\
                .get()

#returns a map of frequencies of mers (subsequencies) of length k
def freq(seq, k):
    return F(range(len(seq) - k + 1))\
            .map(lambda i: seq[i:i+k])\
            .fold({}, lambda d, s: execute(d.update({s:(d.get(s, 0)+1)}), d))\
            .get()

def simplesum(a,b): 
    return a + b

def difference(a,b):
    return a - b

def product(a,b):
    return a * b

def max(a, b):
    return bfold(a > b, a, b)

#compute background (global) probability profile of the sequences, leaving out the ith one
def profile(dnas, i):
    return F(dnas)\
            .zipWithIndex()\
            .filter(tupled(lambda a,b: b != i))\
            .keys()\
            .mapFull(''.join)\
            .mapFull(lambda dna: F(freq(dna, 1)).mapValues(lambda a: a/float(len(dna))).get())\
            .toMap()\
            .get()

#compute similarity of seq according to profile. Similarity is constituted by the probability of occurence of seq given by profile.
def prob(seq, profile):
    return F(seq)\
            .map(lambda c: profile.get(c, 0.01))\
            .reduce(product)\
            .get()

#again compute the score. This time do so directly from the list of mers and do so character-wise
#seq = the picked dna sequence
#i = the index of seq 
#mers = motif candidates
#c = total count
#cf = zero-probability correction factor 
def prob2(seq, mers, i, c, cf):
    return F(range(len(seq)))\
            .map(lambda x:\
                    F(range(c))\
                            .filter(lambda y: y != i)\
                            .map(lambda y: bfold(seq[x] == mers[y][x], 1, 0))\
                            .fold(0, simplesum)
                            .get())\
            .map(lambda p: max(cf, p/float(c-1)))\
            .reduce(product)\
            .get()

#simple roulette selector returning index of the selected item
def roulette(probs):
    s = sum(probs)
    r = random.random() * sum(probs)
    return F(probs)\
            .fold((0,-1), lambda s, p: bfold(s[0] >= r, s, (s[0] + p, s[1] + 1)))\
            .mapFull(lambda a: a[1])\
            .get()

#refine motif-candidate of h th sequence
#mers = motif candidates
#h = index of the current mer
#Q = background profile of the sequence
#dna = currently picked sequence
#c = count of sequences
#l = searched motif length
def step(mers, h, Q, dna, l, c, cf):
    probs = F(range(len(dna)-l))\
            .map(lambda i: dna[i:i+l])\
            .map(lambda s: (s, prob2(s, mers, h, c, cf), prob(s,Q)))\
            .map(tupled(lambda s,a,b: (s, a/b, a, b)))\
            .values()\
            .get()
    r = random.random() * sum(probs)
    i = roulette(probs)
    return bfold(i == -1, mers[h], dna[i:i+l])

#hamming distance of sequences a and b
def hamdist(a,b):
    return F(range(len(a)))\
            .map(lambda i: bfold(a[i] == b[i], 0, 1))\
            .reduce(simplesum)\
            .get()

#median character of a string
def med(s):
    return F(freq(''.join(s), 1))\
            .reduce(lambda a, b: bfold(a[1] > b[1], a, b))\
            .mapFull(lambda a: a[0])\
            .get()

#returns median string
def medstring(mers, l):
    return F(range(l))\
            .map(lambda i: F(mers).map(lambda m: m[i]).get())\
            .map(med)\
            .mapFull(lambda l: ''.join(l))\
            .get()

#checks that every motif candidate (i.e., the best string found in every sequence) has at most e mutations; if so, we have found the result
def isok(med, mers, l, e):
    return F(mers)\
            .map(lambda mer: hamdist(mer, med))\
            .map(lambda a: a <= e)\
            .reduce(lambda a, b: a and b)\
            .get()

#variation of hamming distance
def meddist(med, mers, l, e):
    return F(mers)\
            .map(lambda mer: hamdist(mer, med))\
            .reduce(max)\
            .get()

#variation of hamming distance
def sumdist(mers):
    return F(mers)\
            .map(lambda m: hamdist(m, mers[0]))\
            .reduce(simplesum)\
            .get()

#initialization = take motif at index 'seed' and find the most similar sequences
def init(dnas, l, profiles, seed):
    seed = seed % (len(dnas[0]) - l)
    print "INITIALIZING SEED ", seed
    mers = F(dnas).map(lambda a: dnas[0][seed:seed+l]).get()
    for i in range(len(dnas)-1):
        mers[i+1] = step(dnas, i+1, profiles[i+1], dnas[i+1], l, i+2, 0.05)
    return mers 

#the main event loop of the algorithm
def sample(dnas, l, e):
    print "starting sampling"
    profiles = F(range(len(dnas))).map(lambda i: profile(dnas, i)).get()
    i = 0
    logFreq = 100
    ad = 0.0
    ad2 = 0.0
    f = 100
    sql = l * l
    cycle = 500
    seed = random.randrange(len(dnas[0]))
    mers = init(dnas, l, profiles, seed)
    candidate = mers[0]
    while True:
        i = i+1;
        r = random.randrange(len(dnas))
        lm = mers[r]
        cf = 0.15*max(0, cycle-i)/float(cycle)
        mers[r] = step(mers, r, profiles[r], dnas[r], l, len(mers), cf)
        d = hamdist(lm, mers[r])
        d2 = hamdist(mers[0], mers[r])
        ad = (ad*20 + d2)/21
        ad2 = (ad2*20 + d)/21
        if ad2 < 0.01:
            candidate = medstring(mers, l)
            dd = sumdist([candidate] + mers)
            md = meddist(candidate, mers, l, e)
            if md <= e:
                print "found candidate: ", candidate, " ", md
                F(mers).logLines()
                return candidate
        if i > 2*cycle or ad2 < 0.01:
                md = meddist(candidate, mers, l, e)
                print "candidate ", candidate, "(", md, " ", dd, ") does not suffice, resetting"
                f = 100
                i = 0
                ad = float(l)
                ad2 = float(l)
                seed = seed+ random.randrange(len(dnas[0]))
                mers = init(dnas, l, profiles, seed)
        if(i%32 == 0):
            md = meddist(candidate, mers, l, e)
            if md <= e:
                print "found candidate: ", candidate, " ", md
            print i, " hamdist, derivative, hamdist*derivative, sum of median distances: ", ad, " ", ad2, " ", ad*ad2*100/sql, sumdist([medstring(mers,l)] + mers)


#main control
def gibbs(fn, l, e):
    dnas = readFasta(fn).values()
    sample(dnas, l, e)

gibbs("data/MotSam.fasta", 15, 5)



