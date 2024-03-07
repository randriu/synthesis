import sys
import os
from subprocess import DEVNULL, STDOUT, check_call

dir_path = os.path.dirname(os.path.realpath(__file__))
result_folder = os.fsencode(dir_path + '/output/source')

def get_4x3_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={4x3-95},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Rmax]},\n\
    xmin=0, xmax=15,\n\
    ymin=1.7, ymax=1.9,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={1.7,1.74,1.78,1.82,1.86,1.9},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=1.5:2.1,\n\
    ymajorgrids=true,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_milos_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={Milos-97},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Rmax]},\n\
    xmin=0, xmax=15,\n\
    ymin=31, ymax=43,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={31,33,35,37,39,41,43},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=25:50,\n\
    ymajorgrids=true,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_refuel_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={Refuel-20},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Pmax]},\n\
    xmin=0, xmax=15,\n\
    ymin=0, ymax=0.25,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={0,0.05,0.1,0.15,0.2,0.25},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=0:0.4,\n\
    ymajorgrids=true,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_query_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={Query-s3},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Rmax]},\n\
    xmin=0, xmax=15,\n\
    ymin=415, ymax=515,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={415,435,455,475,495,515},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=400:530,\n\
    ymajorgrids=true,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_lanes_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={Lanes+},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Rmin]},\n\
    xmin=0, xmax=15,\n\
    ymin=4000, ymax=20000,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={4000,8000,12000,16000,20000},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=2000:22000,\n\
    ymajorgrids=true,\n\
    y dir=reverse,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_hallway_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={Hallway},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Rmin]},\n\
    xmin=0, xmax=15,\n\
    ymin=12, ymax=17,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={12,13,14,15,16,17},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=10:20,\n\
    ymajorgrids=true,\n\
    y dir=reverse,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_network_header():
    return "\\begin{tikzpicture}\n\\begin{axis}[\n\
    title={Network-3-8-20},\n\
    xlabel={Time [min]},\n\
    ylabel={Value [Rmin]},\n\
    xmin=0, xmax=15,\n\
    ymin=10, ymax=12,\n\
    xtick={0,2,4,6,8,10,12,14},\n\
    ytick={10,10.4,10.8,11.2,11.6,12},\n\
    xtick pos=left,\n\
    ytick pos=left,\n\
    restrict y to domain=8:14,\n\
    ymajorgrids=true,\n\
    y dir=reverse,\n\
    grid style=dashed,\n\
    height=8cm,\n\
    width=12cm,\n\
    legend style ={ at={(1.03,1)},\n\
        anchor=north west, draw=black, \n\
        fill=white,align=left},\n]\n"


def get_end(file):
    print("\\end{axis}\n\\end{tikzpicture}\n", file=file)


def get_plots(output_file, enhanced_saynt_file, saynt_file):

    # Enhanced SAYNT
    enhanced_saynt_log = enhanced_saynt_file.read()
    enhanced_saynt_storm_coordinates = ""
    enhanced_saynt_paynt_coordinates = ""

    split1 = enhanced_saynt_log.split("-----------Storm-----------")
    for i in range(len(split1)):
        if i > 0:
            split2 = split1[i].split()
            val = round(float(split2[2]),5)
            time = float(split2[7][:-1])
            time = round(time/60,2)
            enhanced_saynt_storm_coordinates = enhanced_saynt_storm_coordinates + f"({time}, {val})"

    print("\\addplot[\n\
    color=red,\n\
    every mark/.append style={solid, fill=red},\n\
    mark=square*,\n\
    line width=1.5pt,mark size=2pt,]\n\
    coordinates {\n" + enhanced_saynt_storm_coordinates + "\n\
    };\n\
    \\addlegendentry{Enhanced SAYNT $F_{B}$};\n", file=output_file)

    split1 = enhanced_saynt_log.split("-----------PAYNT-----------")
    for i in range(len(split1)):
        if i > 0:
            split2 = split1[i].split()
            val = round(float(split2[2]),5)
            time = float(split2[7][:-1])
            time = round(time/60,2)
            enhanced_saynt_paynt_coordinates = enhanced_saynt_paynt_coordinates + f"({time}, {val})"
    if time < 15.0:
        enhanced_saynt_paynt_coordinates = enhanced_saynt_paynt_coordinates + f"(15, {val})"

    print("\\addplot[\n\
    color=orange,\n\
    every mark/.append style={solid, fill=orange},\n\
    mark=triangle*,\n\
    line width=1.5pt,mark size=2pt,]\n\
    coordinates {\n" + enhanced_saynt_paynt_coordinates + "\n\
    };\n\
    \\addlegendentry{Enhanced SAYNT $F_{I}$};\n", file=output_file)
    


    # SAYNT
    saynt_log = saynt_file.read()
    saynt_storm_coordinates = ""
    saynt_paynt_coordinates = ""

    split1 = saynt_log.split("-----------Storm-----------")
    for i in range(len(split1)):
        if i > 0:
            split2 = split1[i].split()
            val = round(float(split2[2]),5)
            time = float(split2[7][:-1])
            time = round(time/60,2)
            saynt_storm_coordinates = saynt_storm_coordinates + f"({time}, {val})"

    print("\\addplot[\n\
    color=blue,\n\
    every mark/.append style={solid, fill=blue},\n\
    mark=square*,\n\
    line width=1.5pt,mark size=2pt,]\n\
    coordinates {\n" + saynt_storm_coordinates + "\n\
    };\n\
    \\addlegendentry{SAYNT $F_{B}$};\n", file=output_file)

    split1 = saynt_log.split("-----------PAYNT-----------")
    for i in range(len(split1)):
        if i > 0:
            split2 = split1[i].split()
            val = round(float(split2[2]),5)
            time = float(split2[7][:-1])
            time = round(time/60,2)
            saynt_paynt_coordinates = saynt_paynt_coordinates + f"({time}, {val})"
    if time < 15.0:
        saynt_paynt_coordinates = saynt_paynt_coordinates + f"(15, {val})"

    print("\\addplot[\n\
    color=green,\n\
    every mark/.append style={solid, fill=green},\n\
    mark=triangle*,\n\
    line width=1.5pt,mark size=2pt,]\n\
    coordinates {\n" + saynt_paynt_coordinates + "\n\
    };\n\
    \\addlegendentry{SAYNT $F_{I}$};\n", file=output_file)



def get_graphs(enhanced_saynt_experiment):
    saynt_path = os.fsencode(dir_path + '/saynt')
    enhanced_saynt = os.fsencode(dir_path + '/' + enhanced_saynt_experiment)

    models = [ f.path for f in os.scandir(enhanced_saynt) if f.is_dir() ]

    for model in models:
        model_name = os.path.basename(model).decode("utf-8")

        try:

            saynt_file = open(saynt_path.decode("utf-8") + "/" + model_name + "/logs.txt", mode='r')

            enhanced_saynt_file = open(enhanced_saynt.decode("utf-8") + "/" + model_name + "/logs.txt", mode='r')

            header = ""
            output_file_name = ""

            if model_name == "4x3-95":
                header = get_4x3_header()
                output_file_name = "source-4x3-95.tex"
            elif model_name == "milos-aaai97":
                header = get_milos_header()
                output_file_name = "source-milos-97.tex"
            elif model_name == "refuel-20":
                header = get_refuel_header()
                output_file_name = "source-refuel-20.tex"
            elif model_name == "query-s3":
                header = get_query_header()
                output_file_name = "source-query-s3.tex"
            elif model_name == "lanes-100-combined-new":
                header = get_lanes_header()
                output_file_name = "source-lanes.tex"
            elif model_name == "hallway":
                header = get_hallway_header()
                output_file_name = "source-hallway.tex"
            elif model_name == "network-3-8-20":
                header = get_network_header()
                output_file_name = "source-network-3-8-20.tex"


            with open(result_folder.decode("utf-8") + "/" + output_file_name, "w") as text_file:
                print(header, file=text_file)
                get_plots(text_file, enhanced_saynt_file, saynt_file)
                get_end(text_file)

                enhanced_saynt_file.close()
                saynt_file.close()

                text_file.close()

        except:
            print(f"ERROR WHILE CREATING GRAPHS!!! Couldn't process logs for model {model_name} to create the graph!")
            continue


def get_figure_start():
    return "\\documentclass{article}\n\
\\usepackage[utf8]{inputenc}\n\n\
\\usepackage{tikz}\n\
\\usepackage{pgfplots}\n\
\\pagenumbering{gobble}\n\n\
\\begin{document}\n"

def get_figure_end():
    return "\\end{document}"

def get_string_if_file_exists(path):
    try:
        source_file = open(path, mode='r')
        source_string = source_file.read()
        source_file.close()
        return source_string
    except:
        return ""

def get_figure(enhanced_saynt_experiment):
    string_4x3 = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-4x3-95.tex")
    string_lanes = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-lanes.tex")
    string_milos = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-milos-97.tex")
    string_hallway = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-hallway.tex")
    string_network = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-network-3-8-20.tex")
    string_query = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-query-s3.tex")
    string_refuel = get_string_if_file_exists(result_folder.decode("utf-8") + "/source-refuel-20.tex")

    figure_contents = string_4x3 + string_lanes + string_milos + string_hallway + string_network + string_query + string_refuel

    with open(result_folder.decode("utf-8") + f"/figure-{enhanced_saynt_experiment}.tex", "w") as text_file:
        print(get_figure_start(), file=text_file)
        print(figure_contents, file=text_file)
        print(get_figure_end(), file=text_file)

        text_file.close()

    source_file = result_folder.decode("utf-8") + f"/figure-{enhanced_saynt_experiment}.tex"
    result_table_folder = result_folder.decode("utf-8") + "/../figure"

    os.makedirs(result_table_folder, exist_ok=True)
    check_call(['pdflatex', f'--output-directory={result_table_folder}', source_file], stdout=DEVNULL, stderr=STDOUT)

    print(f"PDF for figure generated to {result_table_folder}")

if __name__ == '__main__':

    if not os.path.isdir(dir_path + "/output"):
        os.mkdir(dir_path + "/output")

    if not os.path.isdir(dir_path + "/output/source"):
        os.mkdir(dir_path + "/output/source")

    get_graphs(sys.argv[1])

    get_figure(sys.argv[1])