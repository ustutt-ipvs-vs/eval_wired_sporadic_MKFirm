import copy
import os
import pickle

from emergency_eval import settings
from emergency_eval.run_eval import compare_results_single_stream
from emergency_eval.settings import EVAL_PATH_SIM
from eval import extract_data, load_eval_files, calc_offset_to_expected, calc_metrics, check_arrival_times


def eval_for_path_with_run(path, run_num, results):
    extract_data(path, run_num)
    streams, emergency_streams, streams_meta = load_eval_files(path, f"{path}/stream_meta.json", run_num)
    calc_offset_to_expected(streams, streams_meta)

    metrics = calc_metrics(streams, streams_meta, False)

    if path not in results:
        results[path] = {}

    results[path][run_num] = {
        'streams': streams,
        'emergency_streams': emergency_streams,
        'streams_meta': streams_meta,
        'metrics': metrics
    }


def merge_runs_for_path(results, path, results_merged):
    for run_num in results[path]:
        if path not in results_merged:
            results_merged[path] = {
                'streams': copy.deepcopy(results[path][run_num]['streams']),
                'emergency_streams': copy.deepcopy(results[path][run_num]['emergency_streams']),
                'streams_meta': copy.deepcopy(results[path][run_num]['streams_meta']),
            }
            continue

        streams = results[path][run_num]['streams']
        emergency_streams = results[path][run_num]['emergency_streams']

        for port, stream in streams.items():
            intended_len = len(stream['delay'][0])
            if len(stream['delay'][0]) != intended_len:
                print(f"Error: {folder} {port} stream['delay'][0] {len(stream['delay'][0])} != {intended_len}")
            if len(stream['delay'][1]) != intended_len:
                print(f"Error: {folder} {port} stream['delay'][1] {len(stream['delay'][1])} != {intended_len}")
            if len(stream['offset_to_expected']) != intended_len:
                print(
                    f"Error: {folder} {port} stream['offset_to_expected'][0] {len(stream['offset_to_expected'][0])} != {intended_len}")

            results_merged[path]["streams"][port]['delay'][0] += stream['delay'][0]
            results_merged[path]["streams"][port]['delay'][1] += stream['delay'][1]
            results_merged[path]["streams"][port]['offset_to_expected'] += stream['offset_to_expected']
            results_merged[path]["streams"][port]['too_early'] += stream['too_early']
            results_merged[path]["streams"][port]['too_late'] += stream['too_late']
            results_merged[path]["streams"][port]['delayed'] += stream['delayed']

        for port, emergency_stream in emergency_streams.items():
            if port not in results_merged[path]["emergency_streams"]:
                results_merged[path]["emergency_streams"][port] = emergency_stream
            else:
                results_merged[path]["emergency_streams"][port]['delay'][0] += emergency_stream['delay'][0]
                results_merged[path]["emergency_streams"][port]['delay'][1] += emergency_stream['delay'][1]

    metrics = calc_metrics(results_merged[path]["streams"], results_merged[path]["streams_meta"], True)
    results_merged[path]["metrics"] = metrics


def single_streams(results_merged):
    # Compare results
    import pandas as pd
    df = pd.DataFrame()
    # Add column names without content
    df = df.reindex(
        columns=["scheduler", "type", "stream", "lower_whisker", "lower_quartile", "median", "mean", "upper_quartile",
                 "upper_whisker", "outliers"])
    for folder, folder_data in results_merged.items():
        folder_name = os.path.basename(folder)
        for stream_name, stream_data in folder_data["streams"].items():
            # Add stream data to DataFrame
            df = df.append({
                "scheduler": folder_name,
                "type": "tt",
                "stream": stream_name,
                "delays": stream_data['delay'][1],
            }, ignore_index=True)
            pass
        for emergency_stream_name, emergency_stream_data in folder_data["emergency_streams"].items():
            pass
        pass


if __name__ == "__main__":
    top_folder = os.path.join(EVAL_PATH_SIM, "t_3x4")
    run_folder = os.path.join(top_folder, "p_24/r_9/")
    scenario_folder = os.path.join(run_folder, "et_24")

    et_out = f"{scenario_folder}/etsn"
    et_out_2 = f"{scenario_folder}/etsn2"
    lib_out = f"{scenario_folder}/libtsndgm"

    eval_folders = [
        et_out,
        lib_out
    ]

    # Load results per run
    result_file = f"{scenario_folder}/results.pkl"
    results = {}

    result_file_merged = f"{scenario_folder}/results_merged.pkl"
    results_merged = {}

    if not os.path.exists(result_file_merged):
        if not os.path.exists(result_file):
            print("Extracting data...")
            for i in range(settings.num_runs):
                for folder in eval_folders:
                    eval_for_path_with_run(folder, i, results)

            with open(result_file, "wb") as f:
                pickle.dump(results, f)
        else:
            print("Load results.pkl")
            with open(result_file, "rb") as f:
                results = pickle.load(f)

        # Merge results of multiple runs of the same folder
        print("Merging results")
        for path in results:
            merge_runs_for_path(results, path, results_merged)

        with open(result_file_merged, "wb") as f:
            pickle.dump(results_merged, f)
    else:
        print("Load results_merged.pkl")
        with open(result_file_merged, "rb") as f:
            results_merged = pickle.load(f)

    # Perform evaluation on merged results
    print("Sanity check")
    for folder in eval_folders:
        check_arrival_times(results_merged[folder]["streams"])

        print(folder, results_merged[folder]["metrics"])
        for port, stream in results_merged[folder]["streams"].items():
            intended_len = len(stream['delay'][0])
            if len(stream['delay'][0]) != intended_len:
                print(f"Error: {folder} {port} stream['delay'][0] {len(stream['delay'][0])} != {intended_len}")
            if len(stream['delay'][1]) != intended_len:
                print(f"Error: {folder} {port} stream['delay'][1] {len(stream['delay'][1])} != {intended_len}")
            if len(stream['offset_to_expected']) != intended_len:
                print(f"Error: {folder} {port} stream['offset_to_expected'][0] {len(stream['offset_to_expected'][0])} != {intended_len}")

    print("Calc results")
    compare_results_single_stream(results_merged)
