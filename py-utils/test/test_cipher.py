#!/bin/env python3

CLUSTER_ID = "ABCD"

def test1():
    try:
        key = Cipher.generate_key(CLUSTER_ID, "test1")
    except:
        key = None
    print("test1: Cipher.generate_key: key={}\n".format(key))

def test2():
    try:
        key = Cipher.gen_key(CLUSTER_ID, "test2")
    except:
        key = None
    print("test2: Cipher.gen_key: key={}\n".format(key))

def test3():
    try:
        key = Cipher.get_key(CLUSTER_ID, "test3")
    except:
        key = None
    print("test3: Cipher.get_key: key={}\n".format(key))

if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../src/utils/security"))
    from cipher import Cipher

    test1()
    test2()
    test3()
