#!/usr/bin/python
from itertools import permutations
from PIL import Image
import hashlib


mask = []
mask_pattern_len = 0
key = ""
prev = 0
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
    key = m.digest()
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


# plain is a 1D matrix (row-wise read of image matrix)
def encipher(plain, height, width):
    global n, key, mask, mask_pattern_len, prev
    PS = 0
    shares = [[] for i in range(n)]
    L = height * width
    Index = [0 for j in range(L)]
    for j in range(L):
        PS += (ord(key[j % 16]) * ord(key[(j+1) % 16]))
        PS %= L
        while Index[PS] != 0:
            PS = (PS+1) % L
        secretByte = plain[PS]
        Index[PS] = 1
        for i in range(n):
            if (mask[i][j % mask_pattern_len] == '1'):
                R = (prev ^ (secretByte * ord(key[j % 16]))) % 251
                shares[i].append(R)
                prev = secretByte
    print shares


def getImageMatrix(path):
    im = Image.open(path)
    pix = im.load()
    red = []
    green = []
    blue = []
    width, height = im.size
    for x in range(width):
        for y in range(height):
            R, G, B, A = pix[x, y]
            red.append(R)
            green.append(G)
            blue.append(B)
    return red, green, blue, height, width


def run():
    global key, n, k, mask_pattern_len
    key, n, k = getParams()
    mask_pattern_len = mask_generator(n, k)
    red, green, blue, h, w = getImageMatrix("/home/kishor/pictures/test.png")
    # print mask
    encipher(red, h, w)

if __name__ == "__main__":
    run()
