#!/usr/bin/python
from itertools import permutations
import hashlib


mask = []
key = ""
n = 0
k = 0


class Header():

    def __init__(self):
        self.shareNumber = -1
        self.totalShares = n
        self.thresholdNumber = k
        self.key = key
# DUMMY VALUE CHANGE THIS TO WIDTH OF IMAGE
        self.totalSecretBytes = 42


def getParams():
    keyInput = raw_input("Enter key:\n> ")
    m = hashlib.md5()
    m.update(keyInput)
    key = m.hexdigest()
    nInput = int(raw_input("Enter n:\n> "))
    kInput = int(raw_input("Enter k:\n> "))
    return key, nInput, kInput


def mask_generator(n, k):
    global mask
    toPermute = "0"*(k-1) + "1"*(n-k+1)
    perms = set([''.join(p) for p in permutations(toPermute)])
    sortedPerms = sorted(perms)
    k = 0
    while len(sortedPerms):
        mask.append(sortedPerms.pop(len(sortedPerms)-1))
        mask.append(sortedPerms.pop(0))
    mask = [list(p) for p in mask]
    mask_pattern_len = len(mask)
    '''
    for line in mask:
        print line
    Transpose the matrix
    print '================================'
    '''
    mask = [[line[i] for line in mask] for i in range(n)]
    '''
    #for line in mask:
    #    print line
    '''
    return mask_pattern_len


def run():
    key, n, k = getParams()
    mask_generator(n, k)
    print mask

if __name__ == "__main__":
    run()
