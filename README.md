# PicCrypt
Key Based Threshold Cryptography for Secret Image

## Details
This is/was our implementation for a sixth-semester minor project. Includes:
* threshold cryptography and secret sharing
* symmetric/private-key encryption/decryption
* a way of generating n encrypted image shares, such that any k of them can be used to reconstruct the original message.

## Todo
* Iron out kinks.
* Figure out a way to get around the fact that pixel values range from 0 to 255, whereas according to scheme we can only encrypt/decrypt values up to 251.
* Improve user interface!

## References
We ([Sagar](https://github.com/gitsagar) and I) implemented the algorithm(s) detailed [here](https://www.researchgate.net/profile/Prabir_Naskar2/publication/280611285_A_Key_Based_Secure_Threshold_Cryptography_for_Secret_Image/links/55beed0908ae092e96651821.pdf).

**Disclaimer**: there are errors in that paper!
