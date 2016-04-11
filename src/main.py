#!/usr/bin/python
from itertools import permutations
from PIL import Image
import hashlib
import numpy as np
import sys
import math
import gmpy


mask = []
mask_pattern_len = 0
key = ""
prev = 0
n = 0
k = 0
headerStructure = []
zeroCount = []
size = [0, 0]
counter = 0

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
    headerStructure.append(nInput)
    headerStructure.append(kInput)
    l = list(key)
    for ch in l:
        headerStructure.append(ord(ch))
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
        if len(sortedPerms):
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
    shares = [[] for i in range(n)]
    L = height * width
    for j in range(L):
        for i in range(n):
            if (mask[i][j % mask_pattern_len] == '1'):
                secretByte = plain[j]
                R = prev ^ (secretByte * ord(key[j % 16])) % 251
                shares[i].append(R)
        prev = secretByte
    for s in shares:
        toAdd = width - (len(s) % width)
        if toAdd != width:
            for i in range(toAdd):
                s.append(32)
    return shares


def decipher(cipheredByte, j, prev, key):
    P = ((prev ^ cipheredByte) * gmpy.invert(ord(key[j % 16]), 251)) % 251
    return P


def expandMatrix(shares, key, size):
    global prev, mask, mask_pattern_len
    mat = [[] for k in range(len(shares))]
    count = [-1 for i in range(len(shares))]
    for j in range(size):
        for i, s in enumerate(shares):
            if (mask[i][j % mask_pattern_len] == '1'):
                count[i] += 1
                P = int(decipher(s[count[i]], j, prev, key))
                mat[i].append(P)
            if (mask[i][j % mask_pattern_len] == '0'):
                mat[i].append(0)
        prev = P
    return mat

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
    global size
    im = Image.open(path)
    pix = im.load()
    red = []
    green = []
    blue = []
    width, height = im.size
    size[0] = height
    size[1] = width
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
    for i in range(n):
        im = Image.new('RGB', (w, h))
        im.putdata(images[i])
        im.save("./"+str(i)+".png")


def saveImage1D(red, green, blue, height, width):
    image = []
    for i in range(len(red)):
        t = (red[i], green[i], blue[i])
        if t[2] == 234:
            image.append((251, 255, 234))
        else:
            image.append(t)
    im = Image.new('RGB', (width, height))
    im.putdata(image)
    im.save("./reconstructed.png")

'''
Arguments:
    Shares (without header), width of these shares
Return values:
    Shares with header information.
Description:
    Multiplies shares with header matrix to generate "transmission-ready"
    shares with header info attached.
'''
def addHeader(shares, width, offset):
    global key, zeroCount
    temp = []
    header_matrix = np.zeros(shape=(n, k))
    for i in range(len(shares)):
        count = 1
        idx = offset + zeroCount[i]
        while count <= k:
            m = shares[i][idx]
            if (m != 0):
                temp.append(m)
                count += 1
            if (m == 0):
                zeroCount[i] += 1
            idx += 1
        header_matrix[i] = temp
        temp = []

    h = np.zeros(shape=(k, 1))
    for t in range(k):
        h[t] = headerStructure[(offset+t) % 19] # 19 hardcoded since size of header structure is always this
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
    return header_matrix

def finalAddHeader(shares, width):
    global zeroCount
    zeroCount = [0 for i in range(len(shares))]
    offset = 0
    count = 0
    limit = math.ceil(float(19) / k)
    allOut = []
    final_header = [[0 for j in range(k+1)] for i in range(n)]
    while count < limit:
        hmatrix = addHeader(shares, width, offset)
        allOut.append(hmatrix)
        offset += k
        count += 1
    final = [[] for i in range(len(allOut[0]))]
    for a in allOut:
        for i in range(len(a)):
            for j in range(k):
                final[i].append(a[i][j])

    for i in range(n):
        final_header[i] = [i+1] + [int(num) for num in final[i]]
    realShares = []
    limit = int((math.ceil(float(19) / k) * k) + 1)
    for s in shares:
        realShares.append([s[i:i+width] + [0] for i in range(0, len(s), width)])
    lastPos = len(realShares[0][0]) - 1
    for idx, s in enumerate(realShares):
        for jdx, row in enumerate(s):
            if jdx >= limit:
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


def final_combination(sh,key,width,height):
    for s in sh[1:]:
        for idx,i in enumerate(s):
                sh[0][idx] = sh[0][idx] | i

    return sh[0]


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
    mask_pattern_len = mask_generator(n, k)
    try:
        red, green, blue, h, w = getImageMatrix(path)
        red_mod = []
        green_mod = []
        blue_mod = []
        for i in range(len(red)):
            if red[i] >= 251:
                red_mod.append(250)
            else:
                red_mod.append(red[i])
            if green[i] >= 251:
                green_mod.append(250)
            else:
                green_mod.append(green[i])
            if blue[i] >= 251:
                blue_mod.append(250)
            else:
                blue_mod.append(blue[i])
        headerStructure.append(h*w)
    except:
        print "That's not an image!"
        sys.exit(1)
    redShares = encipher(red_mod, h, w)
    redShares = finalAddHeader(redShares, w)
    greenShares = encipher(green_mod, h, w)
    greenShares = finalAddHeader(greenShares, w)
    blueShares = encipher(blue_mod, h, w)
    blueShares = finalAddHeader(blueShares, w)
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
    temp = []
    prods = []
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
    redShares = [[] for i in range(len(shares))]
    '''
    Now, for each R (and G and B), take last column.
    Obtain the first k values in this column.
    Convert to bits, concat, convert to decimal. --> X
    RHS = column (X's)
    LHS = first k numbers of each row of image
    solve for header
    '''
    parts = [[] for i in range(k)]
    limit = int((math.ceil(float(19)/k) * k) + 1)
    for idx, s in enumerate(shares):
        a = s['r'] # Only need one component of one image to construct RHS
        for count in range(limit):
            parts[idx].append(a[(count+1)*w-1])
    # Putting them in order of shares...
    parts.sort(key=lambda x: int(x[0]))
    rhs = [[] for i in range(k)]
    actualParts = [[] for i in range(k)]
    final = [[] for i in range(k)]
    for idx, p in enumerate(parts):
        actualParts[idx] = p[1:]
    for idx, p in enumerate(actualParts):
        for i in range(0, len(p), k):
            final[idx].append(p[i:i+k])
    rhs = [[] for i in range(len(final[0]))]
    for f in final:
        for idx, l in enumerate(f):
            rhs[idx].append(headerPiecesToDecimal(l))

    for idx, s in enumerate(shares):
        for element in s['r']:
            if element != 0:
                redShares[idx].append(element)

    for pos, r in enumerate(rhs):
        r = [[num] for num in r]
        r = np.matrix(r)

        lhs = [redShares[i][pos*k:(pos+1)*k] for i in range(k)]
        lhs = np.matrix(lhs)
        H = np.linalg.solve(lhs, r)
        prods.append(H)
    return prods, shares

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
        header, shares = reconstructHeader(shareNumbers, k)
        recoveredHeader = [int(round(r)) for m in header for r in list(m)][:19]
        recovered_n = recoveredHeader[0]
        recovered_k = recoveredHeader[1]
        recovered_key = ''.join([chr(num) for num in recoveredHeader[2:18]])
        recovered_size = recoveredHeader[18]
        mask_pattern_len = mask_generator(recovered_n, recovered_k)

        reds = [s['r'] for s in shares]
        # Removing last column
        reds_final = [[] for i in range(len(reds))]
        width = size[1]
        height = size[0]

        noTouch = [(r * width) - 1 for r in range(1, height+1)]
        for idx, r in enumerate(reds):
            for pos, num in enumerate(r):
                if pos not in noTouch:
                    reds_final[idx].append(num)

        m = expandMatrix(reds_final, recovered_key, recovered_size)
        ansRed = final_combination(m, recovered_key, width-1, recovered_size/(width-1))

        prev = 0
        greens = [s['g'] for s in shares]
        greens_final = [[] for i in range(len(greens))]

        noTouch = [(r * width) - 1 for r in range(1, height+1)]
        for idx, r in enumerate(greens):
            for pos, num in enumerate(r):
                if pos not in noTouch:
                    greens_final[idx].append(num)
        
        m = expandMatrix(greens_final, recovered_key, recovered_size)
        ansGreen = final_combination(m, recovered_key, width-1, recovered_size/(width-1))

        prev = 0
        blues = [s['b'] for s in shares]
        # Removing last column
        blues_final = [[] for i in range(len(blues))]

        noTouch = [(r * width) - 1 for r in range(1, height+1)]
        for idx, r in enumerate(blues):
            for pos, num in enumerate(r):
                if pos not in noTouch:
                    blues_final[idx].append(num)
        
        m = expandMatrix(blues_final, recovered_key, recovered_size)
        ansBlue = final_combination(m, recovered_key, width-1, recovered_size/(width-1))

        width -= 1
        height = recovered_size / width
        saveImage1D(ansRed, ansGreen, ansBlue, height, width)