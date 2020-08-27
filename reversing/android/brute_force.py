y = [40999019, 2789358025, 656272715, 18374979, 3237618335, 1762529471, 685548119, 382114257, 1436905469, 2126016673, 3318315423, 797150821]

answers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def Ro(a, b): 
    if (a == 0):
        return [0, 1]

    x = Ro(b % a, a)
    return [x[1] - b // a * x[0], x[0]]


for i in range(32, 128):
    print("i:", i)
    for j in range(32, 128):
        for k in range(32, 128):
            for l in range(32, 128):
                # form test number using every possible character
                test = i | (j << 0x8) | (k << 0x10) | (l << 0x18)
                # run it through the modifying function
                ro_res = Ro(test, 0x100000000)
                # Cut off the top bits
                modified = (ro_res[0] % 0x100000000 + 0x100000000) % 0x100000000
                
                # if we find the number in the array, 
                if (modified in y):
                    answers[y.index(modified)] = test
                    print("Found bytes:", hex(modified))
                    print(hex(test))
                
for ans in answers:
    print(chr(ans & 0xFF), end='')
    print(chr((ans >> 0x08) & 0xFF), end='')
    print(chr((ans >> 0x10) & 0xFF), end='')
    print(chr((ans >> 0x18) & 0xFF), end='')

exit(0)
