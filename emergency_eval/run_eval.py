import collections
import json
import os
from functools import cmp_to_key

from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from eval import extract_data, eval_results, load_eval_files, check_arrival_delays, calc_metrics


def do_eval(run_folder, results):
    if not os.path.isdir(run_folder):
        return

    # Load num tt and et streams from streams.json and streams_et.json
    streams_file = f"{run_folder}/streams.json"
    streams_et_file = f"{run_folder}/streams_et.json"
    if not os.path.exists(streams_file) or not os.path.exists(streams_et_file):
        print(f"Skipping {run_folder}, no streams.json or streams_et.json")
        return
    with open(streams_file, "r") as f:
        streams = json.load(f)
    with open(streams_et_file, "r") as f:
        streams_et = json.load(f)
    num_streams = {"tt": len(streams), "et": len(streams_et)}

    schedulers = ["etsn", "libtsndgm"]
    for scheduler in schedulers:
        scheduler_out = f"{run_folder}/{scheduler}_out.json"
        scheduler_folder = f"{run_folder}/{scheduler}"
        if not os.path.exists(scheduler_out):
            results[scheduler_folder] = {
                "scheduled": False,
                "num_streams": num_streams,
            }
            continue

        extract_data(scheduler_folder)
        streams, emergency_streams, streams_meta = load_eval_files(scheduler_folder, f"{scheduler_folder}/stream_meta.json")
        check_arrival_delays(streams, streams_meta, False)

        results[scheduler_folder] = {
            "scheduled": True,
            "streams": streams,
            "metrics": calc_metrics(streams, streams_meta),
            "num_streams": num_streams,
        }
        pass

def custom_compare(folder_name1, folder_name2):
    # Implement your custom comparison logic here
    split1 = folder_name1[0].split("/")
    split2 = folder_name2[0].split("/")

    run1 = float(split1[2].split("_")[-1])
    run2 = float(split2[2].split("_")[-1])
    if split1[0] == split2[0] and split1[1] == split2[1] and run1 != run2:
        return run1 - run2
    elif split1 < split2:
        return -1
    elif split1 > split2:
        return 1
    else:
        return 0

def compare_results(results_by_folder, group_by_cycle=False):
    sorted_results = collections.OrderedDict(sorted(results_by_folder.items(),
                                                    #key=cmp_to_key(custom_compare))
                                                    ))

    delays = {}
    jitters = {}
    labels_delay = []
    labels_jitter = []

    for folder, result in results_by_folder.items():
        e_streams = result["emergency_streams"]
        for port, stream in e_streams.items():
            # Get cycle time from streams_meta
            key = f"{folder}_sporadic"
            if key not in delays:
                delays[key] = []
                label = f"sporadic\n{folder.split('/')[-1]}"
                labels_delay.append(label)
            delays[key].extend(stream["delay"][1])

        streams = result["streams"]
        streams_meta = result["streams_meta"]
        for port, stream in streams.items():
            # Get cycle time from streams_meta
            meta = streams_meta[port]
            cycle_time = meta["cycle_time"]
            key = f"{folder}_{cycle_time}"
            if key not in delays:
                delays[key] = []
                jitters[key] = []
                label = f"time-triggered\nperiod={cycle_time//1000}us\n{folder.split('/')[-1]}"
                labels_delay.append(label)
                labels_jitter.append(label)
            delays[key].extend(stream["delay"][1])
            jitters[key].extend([j for j in stream["offset_to_expected"] if j != 0])

    def seconds_to_microseconds(x, pos):
        return f"{x * 1e6:.0f}"  # Or use .1f if you want decimals

    def nanos_to_microseconds(x, pos):
        return f"{x / 1000:.0f}"

    # Plot delays
    fig1, ax1 = plt.subplots()
    ax1.boxplot(delays.values(), positions=range(len(labels_delay)), showmeans=True, widths=.5, showfliers=True, notch=True)
    ax1.set_xticks(range(len(labels_delay)))
    ax1.set_xticklabels(labels_delay)
    ax1.yaxis.set_major_formatter(FuncFormatter(seconds_to_microseconds))
    ax1.set_ylabel("delay [µs]")
    fig1.tight_layout()

    # Plot jitters
    fig2, ax2 = plt.subplots()
    ax2.boxplot(jitters.values(), positions=range(len(labels_jitter)), showmeans=True, widths=.5, showfliers=True, notch=True)
    ax2.set_xticks(range(len(labels_jitter)))
    ax2.set_xticklabels(labels_jitter)
    ax2.yaxis.set_major_formatter(FuncFormatter(nanos_to_microseconds))
    ax2.set_ylabel("offset to expected [µs]")
    fig2.tight_layout()
    plt.show()

    # # Export results to json
    # with open("results.json", "w+") as f:
    #     to_dump = {
    #         "delays": delays,
    #         "jitters": jitters,
    #     }
    #     json.dump(to_dump, f)


def scheduleability_analysis(results_by_folder):
    # Plot schedulability for etsn and libtsndgm per streamnumber
    by_num_total_streams = {}
    by_num_tt_streams = {}
    by_num_et_streams = {}
    by_et_stream_ratio = {}
    for folder, result in results_by_folder.items():
        num_streams = result["num_streams"]
        num_total_streams = sum(num_streams.values())
        et_stream_ratio = round(num_streams["et"] / num_streams["tt"] * 2) / 2
        if num_total_streams not in by_num_total_streams:
            by_num_total_streams[num_total_streams] = {
                "etsn": 0,
                "libtsndgm": 0,
            }
        if num_streams["tt"] not in by_num_tt_streams:
            by_num_tt_streams[num_streams["tt"]] = {
                "etsn": 0,
                "libtsndgm": 0,
            }
        if num_streams["et"] not in by_num_et_streams:
            by_num_et_streams[num_streams["et"]] = {
                "etsn": 0,
                "libtsndgm": 0,
            }
        if et_stream_ratio not in by_et_stream_ratio:
            by_et_stream_ratio[et_stream_ratio] = {
                "etsn": 0,
                "libtsndgm": 0,
            }

        if result["scheduled"]:
            by_num_total_streams[num_total_streams][folder.split("/")[-1]] += 1
            by_num_tt_streams[num_streams["tt"]][folder.split("/")[-1]] += 1
            by_num_et_streams[num_streams["et"]][folder.split("/")[-1]] += 1
            by_et_stream_ratio[et_stream_ratio][folder.split("/")[-1]] += 1

    for name, array_now in {"total": by_num_total_streams,
                            "tt": by_num_tt_streams,
                            "et": by_num_et_streams,
                            "ratio": by_et_stream_ratio}.items():
        # Sort by num_total_streams
        sorted_by_num_streams = collections.OrderedDict(sorted(array_now.items()))
        x = []
        y_etsn = []
        y_libtsndgm = []
        for num_streams, result in sorted_by_num_streams.items():
            x.append(num_streams)
            y_etsn.append(result["etsn"])
            y_libtsndgm.append(result["libtsndgm"])

        width = 0.4
        if name == "ratio":
            width = 0.2

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar([i - (width / 2) for i in x], y_etsn, label="etsn", width=width)
        ax.bar([i + (width / 2)for i in x], y_libtsndgm, label="libtsndgm", width=width)
        ax.set_xlabel(f"Number of {name} streams")
        ax.set_ylabel("Number of successful runs")
        ax.legend()
        plt.show()



if __name__ == "__main__":
    results_by_folder = {}

    # Beautiful code <3
    for top_folder in os.listdir("."):
        if top_folder.startswith("t_"):
            for stream_folder in os.listdir(top_folder):
                if stream_folder.startswith("s_"):
                    for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                        if run_folder.startswith("r_"):
                            run_folder_full = f"{top_folder}/{stream_folder}/{run_folder}"
                            result = do_eval(run_folder_full, results_by_folder)


    # json.dump(results_by_folder, open("results.json", "w+"))
    scheduleability_analysis(results_by_folder)
    compare_results(results_by_folder)
