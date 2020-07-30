import random

def prob():
    return round(random.random(),2)

def run(): 
    templ = ""
    templ += "\
    dtmc \n\
    \n\
    const int X;\n\
    const int Y;\n\
    const int Z;\n\
    \n\
    module m\n\
    \n\
    \tc1: [0..2] init 0;\n\
    \tc2: [0..2] init 0;\n\
    \tres: [0..2] init 0;\n\
    \n\
    "

    values = ['1','2']
    for v in values:
        p = prob()
        templ += "\t[] c1=0 & X={} -> {} : (c1'=1) + {} : (c1'=2);\n".format(v,p,1-p)
    for c1 in [1,2]:
        for v in values:
            p = prob()
            if random.randint(0,1) == 0:
                templ += "\t[] c1={} & c2=0 & Y={} -> {} : (c2'=1) + {} : (c2'=2);\n".format(c1,v,p,1-p)
            else:
                templ += "\t[] c1={} & c2=0 & Y={} -> {} : (c1'=0) + {} : (c2'=c1);\n".format(c1,v,p,1-p)
    for c2 in [1,2]:
        for v in values:
            p = prob()
            if random.randint(0,1) == 0:
                templ += "\t[] c2={} & res=0 & Z={} -> {} : (res'=1) + {} : (res'=2);\n".format(c2,v,p,1-p)
            else:
                templ += "\t[] c2={} & res=0 & Z={} -> {} : (c2'=0) + {} : (res'=c2);\n".format(c2,v,p,1-p)

    templ += "\
    \t[] res != 0 -> true;\n\
    \n\
    endmodule\n\
    "

    holes = ['X','Y','Z']
    allowed = ""
    for v in holes:
        order = values.copy()
        if random.randint(0,1) == 1:
            order.reverse()
        allowed += "{};{};{}\n".format(v,order[0],order[1])

    properties = "P<={} [F res=1]\n".format(prob())

    with open('workspace/examples/random/sketch.templ','w') as file:
        file.write(templ)
    with open('workspace/examples/random/sketch.allowed','w') as file:
        file.write(allowed)
    with open('workspace/examples/random/sketch.properties','w') as file:
        file.write(properties)

    print("generator2: done")

if __name__ == '__main__':
    run()