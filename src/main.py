#!/usr/bin/python
from itertools import permutations
from PIL import Image
import hashlib
import numpy as np
import sys


mask = []
mask_pattern_len = 0
key = ""
prev = 0
n = 0
k = 0


'''
Arguments:
    None
Return values:
    key, n, k
Description:
    Obtains encryption key, n and k parameters from user.
    Generates MD5(key) and stores this value for further use.
'''
def getParams():
    keyInput = raw_input("Enter key:\n> ")
    m = hashlib.md5()
    m.update(keyInput)
    key = m.digest()
    nInput = int(raw_input("Enter n:\n> "))
    kInput = int(raw_input("Enter k:\n> "))
    return key, nInput, kInput


'''
Arguments:
    Total number of shares (n), threshold number (k)
Return values:
    Length of bit mask.
Description:
    Generates all permutations of size n, having
    * k-1 zeroes
    * n-k+1 ones
    These serve as the masks for n shares
'''
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


'''
Arguments:
    Secret image in the form of a 1D array, height and width
Return values:
    shares, a list of n shares without the corresponding header information
Description:
    Selects bytes from image and encrypts them according to
    R = (Pi-1) ^ [(Pi) * K[j%16]) mod 251
    where:
        * R = encrypted byte
        * P = original chosen byte [(Pi-1) = 0]
        * K = key
'''
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


'''
Arguments:
    Path to image file to be shared.
Return values:
    Height, width, and 1D arrays corresponding to the R,G,B pixel values of
    each pixel in image.
Description:
    Utilizes Python's PIL library to convert given image to pixel matrices.
'''
def getImageMatrix(path):
    im = Image.open(path)
    pix = im.load()
    red = []
    green = []
    blue = []
    width, height = im.size
    for y in range(height):
        for x in range(width):
            try:
                R, G, B, A = pix[x, y]
            except:
                R, G, B = pix[x, y]
            red.append(R)
            green.append(G)
            blue.append(B)
    return red, green, blue, height, width


def saveImage(red, green, blue):
    n = len(red)
    h = len(red[0])
    w = len(red[0][0])
    images = [[[0 for j in range(w)] for k in range(h)] for i in range(n)]
    images = [[] for i in range(n)]
    for i in range(n):
        for j in range(h):
            for k in range(w):
                t = (red[i][j][k], green[i][j][k], blue[i][j][k])
                images[i].append(t)
    print images[0]
    for i in range(n):
        im = Image.new('RGB', (w, h))
        im.putdata(images[i])
        im.save("./"+str(i)+".png")

'''
Arguments:
    Shares (without header), width of these shares
Return values:
    Shares with header information.
Description:
    Multiplies shares with header matrix to generate "transmission-ready"
    shares with header info attached.
'''
def addHeader(shares, width):
    global key
    temp = []
    header_matrix = np.zeros(shape=(n, k))
    final_header = [[0 for j in range(k+1)] for i in range(n)]
    for i in range(len(shares)):
        count = 1
        for m in shares[i]:
            if(m != 0):
                temp.append(m)
                count = count + 1
            if (count > k):
                header_matrix[i] = temp
                temp = []
                break
    h = np.zeros(shape=(k, 1))
    h[0] = n
    h[1] = k
    for t in range(2, k):
        h[t] = ord(key[t-2])
    header_middle = np.dot(header_matrix, h)
    for x in range(len(header_middle)):
        binary = "{0:b}".format(int(header_middle[x]))
        binary = "0"*(8*k - len(binary)) + binary
        rev_binary = binary[::-1]
        binary_split = [[] for i in range(k)]
        for j in range(len(rev_binary)):
            binary_split[j/8].append(rev_binary[j])
        for i in range(k):
            binary_split[i] = binary_split[i][::-1]
            binary_split[i] = int(''.join(binary_split[i]), 2)
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

'''
Arguments:
    Tuple 'pieces' containing the header pieces.
Return value:
    Decimal value corresponding to joined pieces.
Description:
    Reverses the operation seen at the bottom of page 75.
'''
def headerPiecesToDecimal(pieces):
    joined = ''
    for p in pieces:
        s = bin(p)[2:]
        s = "0" * (8-len(s)) + s
        joined += s
    return int(joined, 2)


'''
Arguments:
    None
Return values:
    None
Description:
    Serves as a driver function that calls the various components of the
    implementation.
'''
def encrypt(path):
    global key, n, k, mask_pattern_len
    key, n, k = getParams()
    print "Key: " + bytes(key)
    mask_pattern_len = mask_generator(n, k)
    print "Mask pattern length: " + str(mask_pattern_len)
    print "Masks:"
    for m in mask:
        print m
    try:
        red, green, blue, h, w = getImageMatrix(path)
    except:
        print "That's not an image!"
        sys.exit(1)
    redShares = encipher(red, h, w)
    redShares = addHeader(redShares, w)
    greenShares = encipher(green, h, w)
    greenShares = addHeader(greenShares, w)
    blueShares = encipher(blue, h, w)
    blueShares = addHeader(blueShares, w)
    return redShares, greenShares, blueShares


'''
Arguments:
    Share numbers to be tried, threshold k
Return values:
    Reconstructed header
Description:
	Uses linear algebra ( AX = B => X = (A^-1)*B ) to recover header from k shares.
'''
def reconstructHeader(shareNumbers, k):
    shares = []
    for num in shareNumbers:
        r, g, b, h, w = getImageMatrix(num+".png")
        d = {
            'r': r,
            'g': g,
            'b': b,
            'h': h,
            'w': w
        }
        shares.append(d)
        '''
        Now, for each R (and G and B), take last column.
        Obtain the first k values in this column.
        Convert to bits, concat, convert to decimal. --> X
        RHS = column (X's)
        LHS = first k numbers of each row of image
        solve for header
        '''
    parts = [[] for i in range(k)]
    for idx, s in enumerate(shares):
        a = s['r']
        for count in range(k+1):
            parts[idx].append(a[(count+1)*w-1])
    # Putting them in order of shares...
    parts.sort(key=lambda x: int(x[0]))
    rhs = [[] for i in range(k)]
    for idx, p in enumerate(parts):
        print p
        rhs[idx].append(headerPiecesToDecimal(p[1:]))
    rhs = np.matrix(rhs)
    print rhs
    lhs = [[] for i in range(k)]
    for idx, s in enumerate(shares):
        a = s['r']
        count = 0
        i = 0
        while count < k:
            if a[i] != 0:
                lhs[idx].append(a[i])
                count += 1
            i += 1
    lhs = np.matrix(lhs)
    print lhs
    inv = np.linalg.inv(lhs)
    prod = inv * rhs
    return prod

'''
Arguments:
    None
Return values:
    None
Description:
    "Main" function, drives the entire program
'''
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: ./main.py -[e|d] <path>"
        sys.exit(1)
    if sys.argv[1] == "-e":
        path = sys.argv[2]
        redShares, greenShares, blueShares = encrypt(path)
        saveImage(redShares, greenShares, blueShares)
    elif sys.argv[1] == "-d":
        k = int(raw_input("Enter the value of k: "))
        shareNumbers = raw_input("Enter k share numbers:\n").split(' ')[:k]
        header = reconstructHeader(shareNumbers, k)
        print header
        # n = float(header[0])
        # k = float(header[1])
        # print n, k
        # mask_pattern_len = mask_generator(n, k)
