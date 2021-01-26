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
    \tres: [0..2] init 0;\n\
    \n\
    "
    
    for X in [1,2]:
        for Y in [1,2]:
            for Z in [1,2]:
                p = prob()
                templ += "\t[] res=0 & X={} & Y={} & Z={} -> {} : (res'=1) + {} : (res'=2);\n".format(X,Y,Z,p,1-p)
    templ += "\
    \t[] res != 0 -> true;\n\
    \n\
    endmodule\n\
    "

    allowed = ""
    values = ['1','2']
    for v in ['X','Y','Z']:
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

    print("generator1: done")

if __name__ == '__main__':
    run()