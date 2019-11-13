import hashlib

f = open("random.txt","w")
a = 1
b = '20000'
c = '50000'
d = '70000'
# create tuples here or to file and process
for i in range(0, 20000):
    f.write(str(a) + ":" + str(b) + ":" + str(c) + ":"  + str(d) + "\n")
    b = hashlib.sha3_256(b.encode('utf-8')).hexdigest()[:10]
    c = hashlib.sha3_384 (c.encode('utf-8')).hexdigest()[:10]
    d = hashlib.sha3_512(d.encode('utf-8')).hexdigest()[:10]
    a = a + 1


