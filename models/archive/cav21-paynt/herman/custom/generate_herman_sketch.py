import click
import os


def construct_controller(stations):
    stations_str = f"\nconst int STATIONS = {stations};\n"
    head = "\nmodule controller\n"
    round_var = "\tround : [0..STATIONS] init 1;\n\n"
    sync = "\t[sync] round = 0 -> (round'=1);\n"
    steps = [f"\t[step{i}] round = {i} -> (round'={i + 1});" for i in range(1, stations)]
    step_p = f"\t[step{stations}] round = STATIONS -> (round'=0);\n"
    tail = "\nendmodule\n\n"
    return stations_str + head + round_var + sync + "\n".join(steps) + "\n" + step_p + tail


def construct_holes(dices):
    m0l = "hole int M0LFAIR in {" + ",".join(map(str, range(0, dices))) + "};\n"
    m0h = "hole int M0HFAIR in {" + ",".join(map(str, range(0, dices))) + "};\n"
    m1l = "hole int M1LFAIR in {" + ",".join(map(str, range(0, dices))) + "};\n"
    m1h = "hole int M1HFAIR in {" + ",".join(map(str, range(0, dices))) + "};\n"
    ms = "hole int MxxA in {0,1};\n" + "hole int MxxB in {0,1};\n" + "hole int MxxC in {0,1};\n"
    return m0l + m0h + m1l + m1h + ms


def construct_process(dices, stations):
    head = "\nmodule process1\n"
    x1 = "\n\t x1 : [0..1] init 0;\n"
    y1 = "\t y1 : [0..1] init 0;\n"
    m1 = "\t m1 : [0..1] init 0;\n"
    init = "\n\t[go] true -> 1: (x1'=1);\n\n"
    ms = ["M0LFAIR", "M0HFAIR", "M1LFAIR", "M1HFAIR"]
    guards_eq = [
        f"\t[step1]  (x1=x{stations}) & m1 = {m} & x1 = {x} & {ms[mx]}={i} -> " \
        f"p{i} : (y1'=0) & (m1'=MxxA) + 1-p{i} : (y1'=1) & (m1'=MxxB);"
        for mx, (m, x) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]) for i in range(0, dices)
    ]
    quards_neq = [
        f"\t[step1] !(x1=x{stations}) & m1 = {m} & x1 = {x} -> (y1'=x{stations}) & (m1'=MxxC);"
        for m, x in [(0, 0), (0, 1), (1, 0), (1, 1)]
    ]
    sync = "\n\t[sync] true -> (x1' = y1) & (y1' = 0);\n\n"
    tail = "endmodule\n"
    return head + x1 + y1 + m1 + init + "\n".join(guards_eq) + "\n\n" + "\n".join(quards_neq) + "\n" + sync + tail


@click.command()
@click.option('--dices', help="The number of considered dices for each combination.", required=False, default=5)
@click.option('--stations', help="The number of considered stations.", required=False, default=5)
@click.option('--step', help="The step between probabilities of considered dices.", required=False, default=0.01)
def generate_herman_sketch(dices, stations, step):
    if stations % 2 == 0:
        print("The number of stations must be even!")

    p_step = f"\nconst double P_STEP={step};\n\n"
    num_tokens = "\nformula num_tokens = " + \
                 "".join([f"(x{i}=x{i + 1}?1:0)+" for i in range(1, stations)] + [f"(x{stations}=x1?1:0);"])
    probs_const = ["\nconst double p0 = P_START;"] + \
                  [f"const double p{i} = p{i - 1}+P_STEP;" for i in range(1, dices + 1)]
    processes = [
        f"module process{i} = process1 [ x1=x{i}, y1=y{i}, x{stations}=x{i - 1}, m1=m{i}, step1=step{i} ] endmodule"
        for i in range(2, stations + 1)
    ]

    with open("cav21-benchmark/herman/custom/default.templ", "r") as default_templ:
        default_template = default_templ.read()
    if os.path.exists("cav21-benchmark/herman/custom/sketch.templ"):
        os.remove("cav21-benchmark/herman/custom/sketch.templ")
    with open("cav21-benchmark/herman/custom/sketch.templ", "w") as sketch_templ:
        sketch_templ.write(
            default_template + p_step + construct_holes(dices) + construct_controller(stations) +
            num_tokens + "\n" + "\n".join(probs_const) + "\n" +
            construct_process(dices, stations) + "\n" + "\n".join(processes)
        )


if __name__ == '__main__':
    generate_herman_sketch()
