import os
import sys


def construct_allowed(n):
    m0l = "M0LFAIR;" + ";".join(map(str, range(0, n))) + "\n"
    m0h = "M0HFAIR;" + ";".join(map(str, range(0, n))) + "\n"
    m1l = "M1LFAIR;" + ";".join(map(str, range(0, n))) + "\n"
    m1h = "M1HFAIR;" + ";".join(map(str, range(0, n))) + "\n"
    ms = "MxxA;0;1\n" + "MxxB;0;1\n" + "MxxC;0;1\n"
    return m0l + m0h + m1l + m1h + ms


def construct_process(n, p):
    head = "\nmodule process1\n"
    x1 = "\n\t x1 : [0..1] init 0;\n"
    y1 = "\t y1 : [0..1] init 0;\n"
    m1 = "\t m1 : [0..1] init 0;\n"
    init = "\n\t[go] true -> 1: (x1'=1);\n\n"
    ms = ["M0LFAIR", "M0HFAIR", "M1LFAIR", "M1HFAIR"]
    guards_eq = [
        f"\t[step1]  (x1=x{p}) & m1 = {m} & x1 = {x} & {ms[mx]}={i} -> " \
        f"p{i} : (y1'=0) & (m1'=MxxA) + 1-p{i} : (y1'=1) & (m1'=MxxB);"
        for mx, (m, x) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]) for i in range(0, n)
    ]
    quards_neq = [
        f"\t[step1] !(x1=x{p}) & m1 = {m} & x1 = {x} -> (y1'=x{p}) & (m1'=MxxC);"
        for m, x in [(0, 0), (0, 1), (1, 0), (1, 1)]
    ]
    sync = "\n\t[sync] true -> (x1' = y1) & (y1' = 0);\n\n"
    tail = "endmodule\n"
    return head + x1 + y1 + m1 + init + "\n".join(guards_eq) + "\n\n" + "\n".join(quards_neq) + "\n" + sync + tail


def generate(n, p):
    num_tokens = "\nformula num_tokens = " + "".join([f"(x{i}=x{i+1}?1:0)+" for i in range(1, p)] + [f"(x{p}=x1?1:0);"])
    probs_const = ["\nconst double p0 = P_START;"] + [f"const double p{i} = p{i - 1}+P_STEP;" for i in range(1, n + 1)]
    processes = [
        f"module process{i} = process1 [ x1=x{i}, y1=y{i}, x{p}=x{i-1}, m1=m{i}, step1=step{i} ] endmodule"
        for i in range(2, p+1)
    ]
    with open("workspace/examples/herman/custom/sketch.allowed", "w") as allowed:
        allowed.write(construct_allowed(n))
    with open("workspace/examples/herman/custom/default.templ", "r") as default_templ:
        default_template = default_templ.read()
    if os.path.exists("workspace/examples/herman/custom/sketch.templ"):
        os.remove("workspace/examples/herman/custom/sketch.templ")
    with open("workspace/examples/herman/custom/sketch.templ", "w") as sketch_templ:
        sketch_templ.write(
            default_template + num_tokens + "\n" + "\n".join(probs_const) + "\n" +
            construct_process(n, p) + "\n" + "\n".join(processes)
        )


if __name__ == '__main__':
    generate(int(sys.argv[1]), int(sys.argv[2]))
