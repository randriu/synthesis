import itertools


x1 = [0,1,2]
x2 = [1,2,3]
d1 = [0,1,2,3] # directions: 0 - up, 1 - right, 2 - down, 3 - left
d2 = [0,1,2,3]
act1 = [0,1,2,3] # actions: 0 - turnLeft, 1 - turnRight, 2 - moveForward, 3 - stay
act2 = [0,1,2,3]
unresolved = 0

for e in itertools.product(x1, x2, d1, d2, act1, act2):
    if (e[0] == e[1]) or (e[0] > e[1]):
        continue
    print(f"\t[act] goal=0 & x1={e[0]} & x2={e[1]} & d1={e[2]} & d2={e[3]} & a1={e[4]} & a2={e[5]} -> ", end="")
    if e[4] == 3 and e[5] == 3:
        print("1: true", end="")
    elif e[4] == 0 and e[5] == 3:
        print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
    elif e[4] == 1 and e[5] == 3:
        print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
    elif e[4] == 3 and e[5] == 0:
        print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
    elif e[4] == 3 and e[5] == 1:
        print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
    elif e[4] == 0 and e[5] == 0:
        print(f"0.81: (d1'={(e[2] - 1) % 4})&(d2'={(e[3] - 1) % 4}) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")
    elif e[4] == 1 and e[5] == 0:
        print(f"0.81: (d1'={(e[2] + 1) % 4})&(d2'={(e[3] - 1) % 4}) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")
    elif e[4] == 0 and e[5] == 1:
        print(f"0.81: (d1'={(e[2] - 1) % 4})&(d2'={(e[3] + 1) % 4}) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")
    elif e[4] == 1 and e[5] == 1:
        print(f"0.81: (d1'={(e[2] + 1) % 4})&(d2'={(e[3] + 1) % 4}) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")
    elif e[4] == 2 or e[5] == 2:
        if e[5] == 3:
            if e[0] == 0 and e[2] == 0:
                print(f"0.9: (goal'=1) + 0.1: true", end="")
            if e[0] == 0 and e[2] == 1:
                if e[1] > 1:
                    print(f"0.9: (x1'=1) + 0.1: true", end="")
                else:
                    print("1: true", end="")
            if e[0] == 0 and e[2] == 2:
                print("1: true", end="")
            if e[0] == 0 and e[2] == 3:
                print("1: true", end="")

            if e[0] == 1 and e[2] == 0:
                print("1: true", end="")
            if e[0] == 1 and e[2] == 1:
                if e[1] > 2:
                    print(f"0.9: (x1'=2) + 0.1: true", end="")
                else:
                    print("1: true", end="")
            if e[0] == 1 and e[2] == 2:
                print("1: true", end="")
            if e[0] == 1 and e[2] == 3:
                print(f"0.9: (x1'=0) + 0.1: true", end="")

            if e[0] == 2 and e[2] == 0:
                print("1: true", end="")
            if e[0] == 2 and e[2] == 1:
                print("1: true", end="")
            if e[0] == 2 and e[2] == 2:
                print("1: true", end="")
            if e[0] == 2 and e[2] == 3:
                print(f"0.9: (x1'=1) + 0.1: true", end="")

        elif e[4] == 3:
            if e[1] == 3 and e[3] == 0:
                print(f"0.9: (goal'=2) + 0.1: true", end="")
            if e[1] == 3 and e[3] == 3:
                if e[0] < 2:
                    print(f"0.9: (x2'=2) + 0.1: true", end="")
                else:
                    print("1: true", end="")
            if e[1] == 3 and e[3] == 2:
                print("1: true", end="")
            if e[1] == 3 and e[3] == 1:
                print("1: true", end="")

            if e[1] == 2 and e[3] == 0:
                print("1: true", end="")
            if e[1] == 2 and e[3] == 3:
                if e[0] < 1:
                    print(f"0.9: (x2'=1) + 0.1: true", end="")
                else:
                    print("1: true", end="")
            if e[1] == 2 and e[3] == 2:
                print("1: true", end="")
            if e[1] == 2 and e[3] == 1:
                print(f"0.9: (x2'=3) + 0.1: true", end="")

            if e[1] == 1 and e[3] == 0:
                print("1: true", end="")
            if e[1] == 1 and e[3] == 3:
                print("1: true", end="")
            if e[1] == 1 and e[3] == 2:
                print("1: true", end="")
            if e[1] == 1 and e[3] == 1:
                print(f"0.9: (x2'=2) + 0.1: true", end="")

        elif e[5] == 0:
            if e[0] == 0 and e[2] == 0:
                print(f"0.9: (goal'=1) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")
            if e[0] == 0 and e[2] == 1:
                if e[1] > 1:
                    print(f"0.81: (x1'=1)&(d2'={(e[3] - 1) % 4}) + 0.09: (x1'=1) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 0 and e[2] == 2:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 0 and e[2] == 3:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")

            if e[0] == 1 and e[2] == 0:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 1 and e[2] == 1:
                if e[1] > 2:
                    print(f"0.81: (x1'=2)&(d2'={(e[3] - 1) % 4}) + 0.09: (x1'=2) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 1 and e[2] == 2:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 1 and e[2] == 3:
                print(f"0.81: (x1'=0)&(d2'={(e[3] - 1) % 4}) + 0.09: (x1'=0) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")

            if e[0] == 2 and e[2] == 0:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 2 and e[2] == 1:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 2 and e[2] == 2:
                print(f"0.9: (d2'={(e[3] - 1) % 4}) + 0.1: true", end="")
            if e[0] == 2 and e[2] == 3:
                print(f"0.81: (x1'=1)&(d2'={(e[3] - 1) % 4}) + 0.09: (x1'=1) + 0.09: (d2'={(e[3] - 1) % 4}) + 0.01: true", end="")

        elif e[5] == 1:
            if e[0] == 0 and e[2] == 0:
                print(f"0.9: (goal'=1) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")
            if e[0] == 0 and e[2] == 1:
                if e[1] > 1:
                    print(f"0.81: (x1'=1)&(d2'={(e[3] - 1) % 4}) + 0.09: (x1'=1) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 0 and e[2] == 2:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 0 and e[2] == 3:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")

            if e[0] == 1 and e[2] == 0:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 1 and e[2] == 1:
                if e[1] > 2:
                    print(f"0.81: (x1'=2)&(d2'={(e[3] + 1) % 4}) + 0.09: (x1'=2) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 1 and e[2] == 2:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 1 and e[2] == 3:
                print(f"0.81: (x1'=0)&(d2'={(e[3] + 1) % 4}) + 0.09: (x1'=0) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")

            if e[0] == 2 and e[2] == 0:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 2 and e[2] == 1:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 2 and e[2] == 2:
                print(f"0.9: (d2'={(e[3] + 1) % 4}) + 0.1: true", end="")
            if e[0] == 2 and e[2] == 3:
                print(f"0.81: (x1'=1)&(d2'={(e[3] + 1) % 4}) + 0.09: (x1'=1) + 0.09: (d2'={(e[3] + 1) % 4}) + 0.01: true", end="")

        elif e[4] == 0:
            if e[1] == 3 and e[3] == 0:
                print(f"0.9: (goal'=2) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.01: true", end="")
            if e[1] == 3 and e[3] == 3:
                if e[0] < 2:
                    print(f"0.81: (x2'=2)&(d1'={(e[2] - 1) % 4}) + 0.09: (x2'=2) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 3 and e[3] == 2:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 3 and e[3] == 1:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")

            if e[1] == 2 and e[3] == 0:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 2 and e[3] == 3:
                if e[0] < 1:
                    print(f"0.81: (x2'=1)&(d1'={(e[2] - 1) % 4}) + 0.09: (x2'=1) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 2 and e[3] == 2:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 2 and e[3] == 1:
                print(f"0.81: (x2'=3)&(d1'={(e[2] - 1) % 4}) + 0.09: (x2'=3) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.01: true", end="")

            if e[1] == 1 and e[3] == 0:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 1 and e[3] == 3:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 1 and e[3] == 2:
                print(f"0.9: (d1'={(e[2] - 1) % 4}) + 0.1: true", end="")
            if e[1] == 1 and e[3] == 1:
                print(f"0.81: (x2'=2)&(d1'={(e[2] - 1) % 4}) + 0.09: (x2'=2) + 0.09: (d1'={(e[2] - 1) % 4}) + 0.01: true", end="")

        elif e[4] == 1:
            if e[1] == 3 and e[3] == 0:
                print(f"0.9: (goal'=2) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.01: true", end="")
            if e[1] == 3 and e[3] == 3:
                if e[0] < 2:
                    print(f"0.81: (x2'=2)&(d1'={(e[2] + 1) % 4}) + 0.09: (x2'=2) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 3 and e[3] == 2:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 3 and e[3] == 1:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")

            if e[1] == 2 and e[3] == 0:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 2 and e[3] == 3:
                if e[0] < 1:
                    print(f"0.81: (x2'=1)&(d1'={(e[2] + 1) % 4}) + 0.09: (x2'=1) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.01: true", end="")
                else:
                    print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 2 and e[3] == 2:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 2 and e[3] == 1:
                print(f"0.81: (x2'=3)&(d1'={(e[2] + 1) % 4}) + 0.09: (x2'=3) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.01: true", end="")

            if e[1] == 1 and e[3] == 0:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 1 and e[3] == 3:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 1 and e[3] == 2:
                print(f"0.9: (d1'={(e[2] + 1) % 4}) + 0.1: true", end="")
            if e[1] == 1 and e[3] == 1:
                print(f"0.81: (x2'=2)&(d1'={(e[2] + 1) % 4}) + 0.09: (x2'=2) + 0.09: (d1'={(e[2] + 1) % 4}) + 0.01: true", end="")

        else:
            unresolved += 1

    print(";")

print(f"unresolved: {unresolved}")