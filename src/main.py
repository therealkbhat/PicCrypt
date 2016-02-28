#!/usr/bin/python
from itertools import permutations
from PIL import Image
import hashlib
import numpy as np


mask = []
mask_pattern_len = 0
key = ""
prev = 0
n = 0
k = 0


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
    mask = [[line[i] for line in mask] for i in range(n)]
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
    return shares


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


def addHeader(shares, width):
    global key
    temp = []
    header_matrix = np.zeros(shape=(n,k))
    final_header = [[0 for j in range(k+1)] for i in range(n)]
    for i in range(len(shares)):
        count = 1
        for m in shares[i]:
            if(m!=0):
                temp.append(m);
                count = count + 1
            if (count > k):
                header_matrix[i] = temp
                temp = []
                break
    h = np.zeros(shape=(k,1))
    h[0] = n
    h[1] = k
    for t in range(2,k):
        h[t] = ord(key[t-2])
    header_middle = np.dot(header_matrix,h)
    for x in range(len(header_middle)):
        binary = "{0:b}".format(int(header_middle[x]))
        binary = "0"*(8*k - len(binary)) + binary
        rev_binary = binary[::-1]
        binary_split = [[] for i in range(k)]
        for j in range(len(rev_binary)):
            binary_split[j/8].append(rev_binary[j])
        for i in range(k):
            binary_split[i] = binary_split[i][::-1]
            binary_split[i] = int(''.join(binary_split[i]),2)
        binary_split = binary_split[::-1]
        header_matrix[x] = binary_split
    for i in range(n):
        final_header[i] = [i+1] + [int(num) for num in header_matrix[i]]
    realShares = []
    for s in shares:
        realShares.append([s[i:i+width] + [0] for i in xrange(0, len(s), width)])
    lastPos = len(realShares[0][0]) - 1
    for idx, s in enumerate(realShares):
        for jdx, row in enumerate(s):
            if jdx > k:
                el = 0
            else:
                el = final_header[idx][jdx]
            realShares[idx][jdx][lastPos] = el
    return realShares


def run():
    global key, n, k, mask_pattern_len
    key, n, k = getParams()
    mask_pattern_len = mask_generator(n, k)
    red, green, blue, h, w = getImageMatrix("/home/kishor/pictures/test.png")
    shares = encipher(red, h, w)
    shares = addHeader(shares, w)

if __name__ == "__main__":
    run()
