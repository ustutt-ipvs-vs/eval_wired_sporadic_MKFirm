import collections
import json

import natsort
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter


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

    metrics_delay = {}
    for i, delays_now in delays.items():
        metrics_delay[i] = {
            "max": max(delays_now),
            "min": min(delays_now),
            "mean": sum(delays_now) / len(delays_now),
            "total": len(delays_now),
            "median": np.median(delays_now),
        }
    # Export
    with open("metrics_delay.json", "w+") as f:
        json.dump(metrics_delay, f, indent=4)

    # Plot jitters
    fig2, ax2 = plt.subplots()
    ax2.boxplot(jitters.values(), positions=range(len(labels_jitter)), showmeans=True, widths=.5, showfliers=True, notch=True)
    ax2.set_xticks(range(len(labels_jitter)))
    ax2.set_xticklabels(labels_jitter)
    ax2.yaxis.set_major_formatter(FuncFormatter(nanos_to_microseconds))
    ax2.set_ylabel("offset to expected [µs]")
    fig2.tight_layout()
    plt.show()

    metrics_jitter = {}
    for i, jitter in jitters.items():
        metrics_jitter[i] = {
            "max": max(jitter),
            "min": min(jitter),
            "mean": sum(jitter) / len(jitter),
            "total": len(jitter),
            "median": np.median(jitter),
        }
    # Export
    with open("metrics_jitter.json", "w+") as f:
        json.dump(metrics_jitter, f, indent=4)

    # for i, jitter in jitters.items():
    #     sorted_jitter = sorted(jitter, reverse=True)
    #     print(sorted_jitter[:1000])
    #     print(i, "mean:", sum(jitter) / len(jitter), "max:", max(jitter), "min:", min(jitter), "total:", len(jitter))

    # # Export results to json
    # with open("results.json", "w+") as f:
    #     to_dump = {
    #         "delays": delays,
    #         "jitters": jitters,
    #     }
    #     json.dump(to_dump, f)

def compare_results_single_stream(results_by_folder):

    delays_unsorted = collections.OrderedDict()
    jitters_unsorted = collections.OrderedDict()

    for folder, result in results_by_folder.items():
        folder_name = folder.split("/")[-1]
        e_streams = result["emergency_streams"]
        for port, stream in e_streams.items():
            # Get cycle time from streams_meta
            key = f"{folder_name}_sporadic_{port}"
            delays_unsorted[key] = (stream["delay"][1])

        streams = result["streams"]
        for port, stream in streams.items():
            key = f"{folder_name}_tt_{port}"
            delays_unsorted[key] = (stream["delay"][1])
            jitters_unsorted[key] = [j for j in stream["offset_to_expected"] if j != 0]

    def seconds_to_microseconds(x, pos=None):
        return f"{x * 1e6:.3f}"

    def nanos_to_microseconds(x, pos=None):
        return f"{x / 1000:.3f}"


    # Sort delays and jitters using natsort
    delays = natsort.natsorted(delays_unsorted.items(), key=lambda x: x[0])
    delays = collections.OrderedDict(delays)
    jitters = natsort.natsorted(jitters_unsorted.items(), key=lambda x: x[0])
    jitters = collections.OrderedDict(jitters)

    # Plot delays
    fig1, ax1 = plt.subplots(figsize=(32, 10))
    data_delay = ax1.boxplot(delays.values(), positions=range(len(delays)), showmeans=True, widths=.5, showfliers=True, notch=True)
    ax1.set_xticks(range(len(delays)))
    ax1.set_xticklabels(delays.keys(), rotation=90)
    ax1.yaxis.set_major_formatter(FuncFormatter(seconds_to_microseconds))
    ax1.set_ylabel("delay [µs]")
    fig1.tight_layout()
    rows_delay = []
    print("Delays")

    max_delays = {}
    max_jitters = {}

    for i in range(len(delays)):
        key = list(delays.keys())[i]
        box = data_delay["boxes"][i].get_ydata()[1:3]
        median = data_delay["medians"][i].get_ydata()[0]
        caps = [data_delay["caps"][i * 2].get_ydata()[1], data_delay["caps"][i * 2 + 1].get_ydata()[1]]
        fliers = data_delay["fliers"][i].get_ydata().tolist()
        means = data_delay["means"][i].get_ydata()[0]
        # print(key, max(max(fliers, default=0), max(caps)))

        key_split = key.split("_")
        delay_category = "_".join(key_split[0:2])
        if delay_category not in max_delays:
            max_delays[delay_category] = {}
        max_delays[delay_category][key_split[2]] = (max(max(fliers, default=0), max(caps)))

        rows_delay.append({
            "key": key,
            "box": box,
            "median": median,
            "caps": caps,
            "fliers": fliers,
            "means": means
        })
    df_delay = pd.DataFrame(rows_delay)
    df_delay.to_csv("delays.csv", index=False)


    # Plot jitters
    fig2, ax2 = plt.subplots(figsize=(32, 10))
    data_jitter = ax2.boxplot(jitters.values(), positions=range(len(jitters)), showmeans=True, widths=.5, showfliers=True, notch=True)
    ax2.set_xticks(range(len(jitters)))
    ax2.set_xticklabels(jitters.keys(), rotation=90)
    ax2.yaxis.set_major_formatter(FuncFormatter(nanos_to_microseconds))
    ax2.set_ylabel("offset to expected [µs]")
    fig2.tight_layout()
    plt.show()
    rows_jitter = []
    print("jitter")
    for i in range(len(jitters)):
        key = list(jitters.keys())[i]
        box = data_jitter["boxes"][i].get_ydata()[1:3]
        median = data_jitter["medians"][i].get_ydata()[0]
        caps = [data_jitter["caps"][i * 2].get_ydata()[1], data_jitter["caps"][i * 2 + 1].get_ydata()[1]]
        fliers = data_jitter["fliers"][i].get_ydata().tolist()
        means = data_jitter["means"][i].get_ydata()[0]

        key_split = key.split("_")
        delay_category = "_".join(key_split[0:2])
        if delay_category not in max_jitters:
            max_jitters[delay_category] = {}
        max_jitters[delay_category][key_split[2]] = (max(max(fliers, default=0), max(caps)))

        rows_jitter.append({
            "key": key,
            "box": box,
            "median": median,
            "caps": caps,
            "fliers": fliers,
            "means": means,
        })
    df_jitter = pd.DataFrame(rows_jitter)
    df_jitter.to_csv("jitters.csv", index=False)



    for delay_category in max_delays:
        print("###", delay_category)
        highest_delay = 0
        highest_delay_key = None

        highest_jitter = 0
        highest_jitter_key = None
        for port in max_delays[delay_category]:
            print(f"{port}: max delay = {max_delays[delay_category][port]}", end="")

            if max_delays[delay_category][port] > highest_delay:
                highest_delay = max_delays[delay_category][port]
                highest_delay_key = port

            if delay_category in max_jitters:
                print(f", max jitter = {max_jitters[delay_category][port]}")

                if max_jitters[delay_category][port] > highest_jitter:
                    highest_jitter = max_jitters[delay_category][port]
                    highest_jitter_key = port
            else:
                print()

        print(f"Highest delay: {highest_delay} in {delay_category}_{highest_delay_key}")
        print(f"Highest jitter: {highest_jitter} in {delay_category}_{highest_jitter_key}")