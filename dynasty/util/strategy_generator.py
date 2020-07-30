"""
strategy_generator.py

Contains a helper method to generate a prism module for a strategy. 
"""

def generate(path, membound, actions, observations):
    memupdate_holes = []
    pickaction = []
    updates = []

    for mem_guard in range(membound):
        for ob in observations:
            memupdate_holes.append("M_{}_{}".format(mem_guard, ob))
            pickaction.append("P_{}_{}".format(mem_guard, ob))
            updates.append("[] pick = 0 & mem = {} & o = {} -> (mem'={}) & (pick'={});".format(mem_guard, ob, memupdate_holes[-1], pickaction[-1]))

    with open(path + ".strategy", 'w') as file:
        for mu in memupdate_holes:
            file.write("const int {};\n".format(mu))
        for pa in pickaction:
            file.write("const int {};\n".format(pa))

        file.write("\n")
        file.write("module strategy\n")
        file.write("\tpick : [0..{}] init 0;\n".format(len(actions)))
        file.write("\tmem : [0..{}] init 0;\n".format(membound-1))
        for update in updates:
            file.write("\t{}\n".format(update))

        for idx, action in enumerate(actions):
            file.write("\t[{}] pick={} -> (pick'=0);\n".format(action, idx+1))


        file.write("endmodule")

    with open(path + ".allowed", 'w') as file:
        for mu in memupdate_holes:
            file.write("{}".format(mu))
            for val in range(membound):
                file.write(";{}".format(val))
            file.write("\n")
        for pa in pickaction:
            file.write("{}".format(pa))
            for val in range(1,len(actions)+1):
                file.write(";{}".format(val))
            file.write("\n")



generate("test", 4, ["north", "east", "south", "west"], [1])
