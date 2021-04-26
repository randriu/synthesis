"""
Plot stats from counterexample based synthesis.
"""

import pickle
import os
import os.path

import click

import stats

import numpy as np

import matplotlib as mpl
mpl.rcParams.update({'font.size': 12})


import matplotlib.pyplot as plt


import logging
import stormpy.utility
os.environ['PATH'] = os.environ['PATH'] + ':/Library/TeX/texbin/'

FIGX=5
FIGY=3

logger = logging.getLogger(__name__)

def load_stats(path):
    logger.info("Load stats from {}".format(path))
    tp = pickle.load(open(path, "rb"))
    logger.debug("done!")
    keyword = tp[0]
    if keyword != "cegis-stats":
        raise ValueError("Stats are not for cegis")
    constants_str = tp[1]
    description = tp[2]
    synthesiser_stats = tp[3]
    verifier_stats = tp[4]

    constants = dict()
    constants_pairs = constants_str.split(",")
    for cp in constants_pairs:
        kv = cp.split("=")
        constants[kv[0]] = float(kv[1])
    logger.debug("parsed constants.")
    return synthesiser_stats, verifier_stats, constants, description

def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

def print_details(s,v,c):
    print(c)
    print("Iterations: {} ({} s), Qualitative Iterations {}/{}".format(s.iterations,
                                                                       s.total_time,
                                                                       s.qualitative_iterations,
                                                                       s.iterations))
    print("Non-trivial counterexamples: {}".format(s.non_trivial_cex))
    print("Model Building Calls: {} ({} s)".format(v.model_building_calls,
                                                   v.model_building_time))
    print("Average model size: {} (range from {} to {})".format(v.average_model_size, v.min_model_size, v.max_model_size))
    print("Synthethiser Analysis: {} = {} + {} s".format(s.total_solver_time,
                                                         s.total_solver_analysis_time,
                                                         s.total_solver_clause_adding_time))
    print("Conflict analyses Calls: {} ({} s)".format(v.conflict_analysis_calls,
                                                      v.conflict_analysis_time))
    print("Qualitative Model Checking Calls: {} ({} s)".format(
        v.qualitative_model_checking_calls,
        v.qualitative_model_checking_time))
    print("Quantitative Model Checking Calls: {} ({} s)".format(
        v.quantitative_model_checking_calls,
        v.quantitative_model_checking_time))

    print("CA/Iterations: {}".format(v.total_conflict_analysis_iterations))
    print("CA/SMT solving: {} s".format(v.total_conflict_analysis_solver_time))
    print("CA/Analysis: {} s".format(v.total_conflict_analysis_analysis_time))
    print("CA/MC: {} s".format(v.total_conflict_analysis_mc_time))
    print("CA/Setup: {} s".format(v.total_conflict_analysis_setup_time))
    print("CA/Cuts: {} s".format(v.total_conflict_analysis_cut_time))


#"test.stats;test2.stats;test3.stats;test4.stats;test5.stats;test6.stats;test7.stats;test8.stats"
@click.command()
@click.option('--prefix', help='prefix to paths')
@click.option('--paths', help="path to stats", default="output/virus/stats_CMAX=0_T=10.0.sts,output/virus/stats_CMAX=0_T=15.0.sts,output/virus/stats_CMAX=0_T=20.0.sts")
@click.option('--constant-label', default="T")
@click.option('--names', default=None)
@click.option('--groupvar', default="CMAX")
@click.option('--plot-relative', is_flag=True)
@click.option('--plot-performance-graph', is_flag=True)
@click.option('--plot-relevant-holes', is_flag=True)
@click.option('--plot-conflict-sizes', is_flag=True)
def analyse(prefix, paths, constant_label, names, groupvar, plot_relative, plot_performance_graph, plot_relevant_holes, plot_conflict_sizes):
    syntstatsgroups = []
    verifstatsgroups = []
    constantsgroups = []
    descriptions = []
    if names:
        names = names.split(",")
    for path_group in paths.split(";"):
        syntstatsgroups.append([])
        verifstatsgroups.append([])
        constantsgroups.append([])
        descriptions.append([])
        path_list = path_group.split(",")
        for path in path_list:

            s, v, c, d = load_stats(os.path.join(prefix, path))
            syntstatsgroups[-1].append(s)
            verifstatsgroups[-1].append(v)
            constantsgroups[-1].append(c)
            descriptions[-1].append(d)

    plt.figure(1)

    for i in range(len(syntstatsgroups)):
        for s,v,c,d in zip(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i], descriptions[i]):
    # plot_timings(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i], relative=False)
            print("------------------------------")
            print("### {}".format(d))
            print_details(s,v,c)
            print("------------------------------")

    if plot_relative:
        for i in range(len(syntstatsgroups)):
            plot_timings(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i], label=constant_label, relative=True)


    if plot_conflict_sizes:
        for i in range(len(syntstatsgroups)):
            plot_conflict_sizes_histogram(verifstatsgroups[i], names)

    if plot_relevant_holes:
        rel_holes = []
        for i in range(len(syntstatsgroups)):
            for s, v, c, d in zip(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i], descriptions[i]):
                 # plot_timings(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i], relative=False)
                 for p in v.property_stats:
                     rel_holes.append(p.relevant_holes)
            plot_relevant_holes_fct(rel_holes)

    if plot_performance_graph:
        plot_simple_performance_graph(syntstatsgroups, verifstatsgroups, constantsgroups, constant_label, groupvar, names)
    #for i in range(len(syntstatsgroups)):
    #for i in range(len(syntstatsgroups)):
    #    for s, v, c in zip(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i]):
    #        iterations_plot(s,v,c)

def plot_relevant_holes_fct(rel_holes):
    print(rel_holes)
    ind = np.arange(len(rel_holes[0].keys()))  # the x locations for the groups
    width = 0.35  # the width of the bars: can also be len(x) sequence
    ind_dt = [i + width for i in ind]

    bars = []
    for r in rel_holes:
        bars.append(plt.bar(ind, list(r.values()), width))

    plt.ylabel('Times in a conflict')
    plt.xlabel('Hole Identifier')
    #plt.title("Relevant holes")
    plt.xticks(ind, [k for k in rel_holes[0].keys()])
    #plt.yticks(np.arange(0, maxheight, 0.1 * maxheight))
    #plt.legend((p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p8[0], p9[0]),
     #          ('Solver', 'Building', 'Analysis', 'Other',
     #           'Analysis/Setup', 'Analysis/Cut', 'Analysis/Solver', 'Analysis/MC', 'Analysis/Eval'))

    plt.tight_layout()
    plt.savefig("output.pgf")
    plt.show()



def plot_conflict_sizes_histogram(verifstats, names, prop_indices = [0,1,2]):
    prop_stats = []

    for v in verifstats:
        prop_stats.append([])
        for prop_index in range(len(v.property_stats)):
            prop_stats[-1].append(list(v.property_stats)[prop_index])
    width = 0.2

    markers = [".", "+", "x", "s", "^"]
    for dics, m in zip(prop_stats, markers):
        xs = list(dics[0].histogram().keys())
        ys = [0 for x in dics[0].histogram().keys()]
        for dic in dics:
            for id, y in enumerate(list(dic.histogram().values())):
                ys[id] += y
        #print(xs)
        #print(ys)
        plt.yscale('log')
        plt.plot(xs, ys, m, linestyle="-", markersize=4)

        #plt.plot([x + offset/len(prop_stats) for x in dic.histogram().keys()], dic.histogram().values(), width, color='g')
    plt.xlabel("conflicts")
    plt.ylabel("conflict size")
    plt.legend(tuple(names))
    plt.savefig("output.pgf")
    plt.show()



def iterations_plot(syntstat, verifstat, constants):
    fig, ax1 = plt.subplots()

    ax2 = ax1.twinx()
    width = 0.2
    ind = np.arange(syntstat.iterations-1)
    b2 = [x+width for x in ind]
    b0 = [x-width for x in ind]

    #print(len(verifstat._model_sizes))
    ax1.bar(b0, verifstat._model_sizes, width, align="center")
    ax2.bar(ind, verifstat._model_building_time, width, color="green", align="center")
    ax2.bar(b2, [x.total_time for x in verifstat._conflict_analysis_stats], width, color="red", align="center")


    plt.show()




def plot_timings(syntstats, verifstats, constants, label, relative=True):
    ind = np.arange(len(syntstats))  # the x locations for the groups
    width = 0.35  # the width of the bars: can also be len(x) sequence
    ind_dt = [i+width for i in ind]

    solvertimes = []
    modelbuilding_times = []
    modelanalysis_times = []
    modelanalysis_times_bottom = []
    other_times = []
    other_times_bottom = []
    modelanalysis_setup_times = []
    modelanalysis_cut_times = []
    modelanalysis_cut_bottom = []
    modelanalysis_mc_times = []
    modelanalysis_mc_bottom = []
    modelanalysis_sat_times = []
    modelanalysis_sat_bottom = []
    modelanalysis_ana_times = []
    modelanalysis_ana_bottom = []

    scale = 1
    maxheight = 1 if relative else 0
    for s, v, c in zip(syntstats, verifstats, constants):

        if relative:
            scale = s.total_time
        else:
            maxheight = max(s.total_time, maxheight)

        assert s.total_time
        solvertimes.append(s.total_solver_time/scale)
        modelbuilding_times.append(v.model_building_time/scale)
        modelanalysis_times.append(v.conflict_analysis_time/scale)
        modelanalysis_times_bottom.append(solvertimes[-1] + modelbuilding_times[-1])
        other_times.append((s.total_time - s.total_solver_time - v.model_building_time - v.conflict_analysis_time)/scale)
        other_times_bottom.append(modelanalysis_times_bottom[-1] + modelanalysis_times[-1])
        modelanalysis_setup_times.append(v.total_conflict_analysis_setup_time/scale)
        modelanalysis_cut_bottom.append(modelanalysis_times_bottom[-1] + modelanalysis_setup_times[-1])
        modelanalysis_cut_times.append(v.total_conflict_analysis_cut_time/scale)
        modelanalysis_sat_bottom.append(modelanalysis_cut_bottom[-1] + modelanalysis_cut_times[-1])
        modelanalysis_sat_times.append(v.total_conflict_analysis_solver_time/scale)
        modelanalysis_mc_bottom.append(modelanalysis_sat_times[-1] + modelanalysis_sat_bottom[-1])
        modelanalysis_mc_times.append(v.total_conflict_analysis_mc_time/scale)
        modelanalysis_ana_bottom.append(modelanalysis_mc_bottom[-1] + modelanalysis_mc_times[-1])
        modelanalysis_ana_times.append(v.total_conflict_analysis_analysis_time/scale)


    p1 = plt.bar(ind, solvertimes, width)
    p2 = plt.bar(ind, modelbuilding_times, width,
                 bottom=solvertimes)
    p3 = plt.bar(ind, modelanalysis_times, width, bottom=modelanalysis_times_bottom)
    p4 = plt.bar(ind, other_times, width, bottom=other_times_bottom)
    p5 = plt.bar(ind_dt, modelanalysis_setup_times, width/2, bottom=modelanalysis_times_bottom)
    p6 = plt.bar(ind_dt, modelanalysis_cut_times, width / 2, bottom=modelanalysis_cut_bottom)
    p7 = plt.bar(ind_dt, modelanalysis_sat_times, width/2, bottom=modelanalysis_sat_bottom)
    p8 = plt.bar(ind_dt, modelanalysis_mc_times, width / 2, bottom=modelanalysis_mc_bottom)
    p9 = plt.bar(ind_dt,  modelanalysis_ana_times, width/2, bottom=modelanalysis_ana_bottom)

    plt.ylabel('Fraction of Time')
    title = "Relative Timings" if relative else "Absolute Timings"
    plt.title(title)
    plt.xticks(ind, [ c[label] for c in constants])
    plt.yticks(np.arange(0, maxheight, 0.1*maxheight))
    plt.legend((p1[0], p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p8[0], p9[0]),
               ('Solver', 'Building', 'Analysis', 'Other',
                'Analysis/Setup', 'Analysis/Cut', 'Analysis/Solver', 'Analysis/MC', 'Analysis/Eval'))

    plt.tight_layout()
    plt.savefig("output.pgf")
    plt.show()

def plot_simple_performance_graph(syntstatsgroups, verifstatsgroups, constantsgroups, label, groupvar, names, inner_iterations=False):

    plt.subplot(111)
    fig, ax1 = plt.subplots()

    fig.set_size_inches(FIGX, FIGY)

    ax2 = ax1.twinx()

    # red dashes, blue squares and green triangles
    symbols = ["o", "x", "+"]

    for i in range(len(syntstatsgroups)):

        xlabels = []
        iter = []
        inner_iter = []
        total_time = []
        for s, v, c in zip(syntstatsgroups[i], verifstatsgroups[i], constantsgroups[i]):
            if not names:
                xlabels.append(c[label])
            print(c[groupvar])
            iter.append(s.iterations)
            inner_iter.append(v.total_conflict_analysis_iterations)
            total_time.append(s.total_time)

        if names:
            xlabels = [i+1 for i in range(len(names))]

        if inner_iterations:
            ax1.plot(xlabels, inner_iter, symbols[i], label="inner iterations ({})".format(i), color="g")
        else:
            ax1.plot(xlabels, iter, symbols[i], label="outer iterations ({})".format(i), color="g")
        ax2.plot(xlabels, total_time, symbols[i], label="CMAX={}".format(constantsgroups[i][0][groupvar]), color="b", markersize=5)


    ax1.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)

    if names:
        plt.xticks(xlabels, names)
        ax1.set_xlabel('Variants'.format(label))
    else:
        ax1.set_xlabel('Constant: {}'.format(label))
    if inner_iterations:
        ax1.set_ylabel('inner iterations', color='g')
    else:
        ax1.set_ylabel('nr designs', color='g')
    ax2.set_ylabel('time', color='b')
    if len(syntstatsgroups) > 1:
        leg = plt.legend(loc='best', ncol=1, shadow=True, fancybox=True)
        leg.get_frame().set_alpha(0.5)

    plt.tight_layout()
    plt.savefig("output.pgf")
    plt.show()


if __name__ == '__main__':
    analyse()