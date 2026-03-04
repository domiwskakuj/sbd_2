import random

n = 200
max = 999
test = []
m = 0
def generate(n, m, max):                                    # generate records and keys for testing
    file = open("operations.txt", "w")
    for i in range(0, max):
        test.append(0)

    for i in range(0,n):
        r = 0
        while True:
            r = random.randint(0, max - 1)
            if test[r] == 0:
                test[r] = 1
                break
        file.write(f"i {r}\n")

    for i in range(0, m):
        r = 0
        while True:
            r = random.randint(0, max - 1)
            if test[r] == 1:
                test[r] = 0
                break
        file.write(f"d {r}\n")
        file.write("s\n")
    file.close()

