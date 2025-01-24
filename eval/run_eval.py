import collections
import os
from functools import cmp_to_key

from matplotlib import pyplot as plt

from eval import extract_data, eval_results, load_eval_files, check_arrival_delays, calc_metrics


def do_eval(folder):
    if not os.path.isdir(folder):
        return

    extract_data(folder)
    streams, emergency_streams, streams_meta = load_eval_files(folder, f"{folder}/stream_meta.json")
    check_arrival_delays(streams, streams_meta, False)
    return streams, calc_metrics(streams, streams_meta)

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

def compare_results(results_by_folder):
    sorted_results = collections.OrderedDict(sorted(results_by_folder.items(), key=cmp_to_key(custom_compare)))
    labels = []

    fig1, ax1 = plt.subplots(figsize=(12, 6))
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    i=0

    last_top = None
    last_stream = None
    for folder, result in sorted_results.items():
        labels.append(folder)
        streams = result["streams"]
        all_delays_now = []
        all_jitters_now = []
        for port, stream in streams.items():
            all_delays_now += stream["delay"][1]
            all_jitters_now += stream["offset_to_expected"]

        ax1.boxplot(all_delays_now, positions=[i], showmeans=True, widths=.5, showfliers=False)
        ax2.boxplot(all_jitters_now, positions=[i], showmeans=True, widths=.5, showfliers=False)

        top_now = folder.split("/")[0]
        stream_now = folder.split("/")[1]
        if top_now != last_top and last_top is not None:
            # Plot axvline
            ax1.axvline(x=i-.5, color='black', linestyle='--', linewidth=1)
            ax2.axvline(x=i-.5, color='black', linestyle='--', linewidth=1)
        elif stream_now != last_stream and last_stream is not None:
            ax1.axvline(x=i-.5, color='black', linestyle='--', linewidth=0.5)
            ax2.axvline(x=i-.5, color='black', linestyle='--', linewidth=0.5)

        last_stream = stream_now
        last_top = top_now

        i += 1


    ax1.set_xticklabels(labels)
    fig1.autofmt_xdate(rotation=90)

    ax2.set_xticklabels(labels)
    ax2.set_ylim(top=5)
    fig2.autofmt_xdate(rotation=90)

    fig1.tight_layout()
    fig2.tight_layout()
    plt.show()






if __name__ == "__main__":
    results_by_folder = {}

    # Beautiful code <3
    for top_folder in os.listdir("."):
        if top_folder.startswith("t_"):
            for stream_folder in os.listdir(top_folder):
                if stream_folder.startswith("s_"):
                    for sim_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                        result = do_eval(f"{top_folder}/{stream_folder}/{sim_folder}")
                        if result:
                            results_by_folder[f"{top_folder}/{stream_folder}/{sim_folder}"] = {
                                "streams": result[0],
                                "metrics": result[1]
                            }

    compare_results(results_by_folder)
