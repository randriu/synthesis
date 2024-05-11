import paynt.cli
import os



def main():

    f = open("gridGeneratedTransactions.txt", "w")

    

    
    f.write(f"# Meeting in a gridn\nagents: 2\ndiscount: 0.9\nvalues: reward\nstates: ")
    for x1 in range(8):
        for y1 in range(8):
            for x2 in range(8):
                for y2 in range(8):
                    f.write(f"s{x1}{y1}{x2}{y2} ")
    f.write(f"\nstart:\n")

    for x1 in range(8):
        for y1 in range(8):
            for x2 in range(8):
                for y2 in range(8):
                    if x1 == 2 and y1 == 5 and x2 == 6 and y2 == 2:
                        f.write(f"1.0 ")
                    else:
                        f.write(f"0.0 ")
    f.write(f"\nactions:\na0 a1 a2 a3\na0 a1 a2 a3\nobservations:\no0 o1\no0 o1\n")
    for a1 in range(4):
        for a2 in range(4):
            for x1 in range(8):
                for y1 in range(8):
                    for x2 in range(8):
                        for y2 in range(8):
                            ox1 = x1
                            ox2 = x2
                            oy1 = y1
                            oy2 = y2
                            agent_1_changed = False
                            agent_2_changed = False
                           
                            if a1==0:
                                if not(y1 == 0 or (y1 == 2 and x1 <2) or (y1 == 7 and x1>2) or (y1 == 4 and x1 ==5)):
                                    oy1 = y1 -1
                                    agent_1_changed = True
                            if a1==1:
                                if not(x1 == 0 or (x1 == 2 and y1 <2) or (x1 == 6 and y1<4) or (x1 == 4 and y1 <6 and y1 >2)) :
                                    ox1 = x1 -1
                                    agent_1_changed = True
                            if a1==2:
                                if not(y1 == 7 or (y1 == 5 and x1 >3) or (y1 == 2 and x1 ==3)):
                                    oy1 = y1 +1
                                    agent_1_changed = True
                            if a1==3:
                                if not(x1 == 7 or (x1 == 2 and y1 <7 and y1 >2) or (x1 == 4 and y1 <4)) :
                                    ox1 = x1 +1
                                    agent_1_changed = True

                            if a2==0:
                                if not(y2 == 0 or (y2 == 2 and x2 <2) or (y2 == 7 and x2>2) or (y2 == 4 and x2 ==5)):
                                    oy2 = y2 -1
                                    agent_2_changed = True
                            if a2==1:
                                if not(x2 == 0 or (x2 == 2 and y2 <2) or (x2 == 6 and y2<4) or (x2 == 4 and y2 <6 and y2 >2)) :
                                    ox2 = x2 -1
                                    agent_2_changed = True
                            if a2==2:
                                if not(y2 == 7 or (y2 == 5 and x2 >3) or (y2 == 2 and x2 ==3)):
                                    oy2 = y2 +1
                                    agent_2_changed = True
                            if a2==3:
                                if not(x2 == 7 or (x2 == 2 and y2 <7 and y2 >2) or (x2 == 4 and y2 <4)) :
                                    ox2 = x2 +1
                                    agent_2_changed = True
                            # if (x1  == 4 and y1 == 4 and x2  == 4 and y2 == 4):
                            #     f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 1.0\n")
                            if ((x1 == x2) and (y1 == y2)):
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 1.0\n")
                            elif (x1  == 2 and y1 == 4 and x2  == 7 and y2 == 7):
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 1.0\n")
                            elif not(agent_1_changed) and not(agent_2_changed) :
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 1.0\n")
                            elif not(agent_1_changed) and agent_2_changed :
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{ox2}{oy2} : 0.9\n")
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 0.1\n")
                            elif agent_1_changed and not(agent_2_changed) :
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{ox1}{oy1}{x2}{y2} : 0.9\n")
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 0.1\n")
                            elif agent_1_changed and agent_2_changed :
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{ox1}{oy1}{ox2}{oy2} : 0.81\n")
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{ox2}{oy2} : 0.09\n")
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{ox1}{oy1}{x2}{y2} : 0.09\n")
                                f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 0.01\n")
                            # print(f"state = {x1}{y1}{x2}{y2}")
                            # print(f"state = {x1}{y1}{x2}{y2} action1 = {a1} action2 = {a2}, end in  = {ox1}{oy1}{ox2}{oy2}")
                            # if (x1 == ox1) and (y1 == oy1) and (x2 == ox2) and (y2 == oy2) :
                            #     f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 1.0\n")
                            # else:
                            #     f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{ox1}{oy1}{ox2}{oy2} : 0.9\n")
                            #     f.write(f"T: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : s{x1}{y1}{x2}{y2} : 0.1\n")
    # for a1 in range(4):
    #     for a2 in range(4):
    #         for x1 in range(8):
    #             for y1 in range(8):
    #                 for x2 in range(8):
    #                     for y2 in range(8):
    #                         o1 = 0
    #                         o2 = 0
    #                         if (x1 == 7 or (x1 == 2 and y1 <7 and y1 >2) or (x1 == 4 and y1 <4)) :
    #                             o1 = 1
    #                         if (x2 == 0 or (x2 == 2 and y2 <2) or (x2 == 6 and y2<4) or (x2 == 4 and y2 <6 and y2 >2)) : 
    #                             o2 = 1
    #                         f.write(f"O: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : o{o1} o{o2} : 1.0\n")

    for a1 in range(4):
        for a2 in range(4):
            for x1 in range(8):
                for y1 in range(8):
                    for x2 in range(8):
                        for y2 in range(8):
                            o1 = 0
                            o2 = 0
                            if (x1 == 7 or (x1 == 2 and y1 <7 and y1 >2) or (x1 == 4 and y1 <4)) :
                                o1 = 1
                            if (x2 == 0 or (x2 == 2 and y2 <2) or (x2 == 6 and y2<4) or (x2 == 4 and y2 <6 and y2 >2)) : 
                                o2 = 1
                            # if (x1 == x2 and y1 == y2) :
                            #     f.write(f"O: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : target target : 1.0\n")
                            # else:
                            f.write(f"O: a{a1} a{a2} : s{x1}{y1}{x2}{y2} : o{o1} o{o2} : 1.0\n")
    f.write(f"#\nR: * *: * : * : * : -1 \n#")
    f.close()

if __name__ == "__main__":
    main()