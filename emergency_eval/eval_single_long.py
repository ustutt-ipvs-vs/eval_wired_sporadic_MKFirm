import os

import pickle

from emergency_eval.run_eval import compare_results
from emergency_eval.settings import EVAL_PATH_SIM
from eval import extract_data, load_eval_files, check_arrival_delays, calc_metrics


def eval_for_path_with_run(path, run_num, results, results_merged):
    extract_data(path, run_num)
    streams, emergency_streams, streams_meta = load_eval_files(path, f"{path}/stream_meta.json", run_num)
    check_arrival_delays(streams, streams_meta, True)

    if path not in results_merged:
        results_merged[path] = {
            "streams": streams,
            "emergency_streams": emergency_streams,
            "streams_meta": streams_meta,
        }
    else:
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

    metrics = calc_metrics(streams, streams_meta, False)

    if path not in results:
        results[path] = {}

    results[path][run_num] = {
        'streams': streams,
        'emergency_streams': emergency_streams,
        'streams_meta': streams_meta,
        'metrics': metrics
    }



if __name__ == "__main__":
    top_folder = os.path.join(EVAL_PATH_SIM, "t_3x4")
    run_folder = os.path.join(top_folder, "p_24/r_9/")
    scenario_folder = os.path.join(run_folder, "et_24")

    et_out = f"{scenario_folder}/etsn"
    et_out_2 = f"{scenario_folder}/etsn2"
    lib_out = f"{scenario_folder}/libtsndgm"

    eval_folders = [
        et_out,
        et_out_2,
        lib_out
    ]

    result_file = f"{scenario_folder}/results.pkl"
    result_file_merged = f"{scenario_folder}/results_merged.pkl"

    results = {}
    results_merged = {}

    if not os.path.exists(result_file):
        for i in range(200):
            for folder in eval_folders:
                eval_for_path_with_run(folder, i, results, results_merged)

        for folder in eval_folders:
            metrics = calc_metrics(results_merged[folder]["streams"], results_merged[folder]["streams_meta"], True)
            results_merged[folder]["metrics"] = metrics

        # Save results as pickle
        with open(result_file, "wb") as f:
            pickle.dump(results, f)
        with open(result_file_merged, "wb") as f:
            pickle.dump(results_merged, f)
    else:
        # with open(result_file, "rb") as f:
            # results = pickle.load(f)
        with open(result_file_merged, "rb") as f:
            results_merged = pickle.load(f)

    for folder in eval_folders:
        # Sanity check
        for port, stream in results_merged[folder]["streams"].items():
            intended_len = len(stream['delay'][0])
            if len(stream['delay'][0]) != intended_len:
                print(f"Error: {folder} {port} stream['delay'][0] {len(stream['delay'][0])} != {intended_len}")
            if len(stream['delay'][1]) != intended_len:
                print(f"Error: {folder} {port} stream['delay'][1] {len(stream['delay'][1])} != {intended_len}")
            if len(stream['offset_to_expected']) != intended_len:
                print(f"Error: {folder} {port} stream['offset_to_expected'][0] {len(stream['offset_to_expected'][0])} != {intended_len}")

    compare_results(results_merged)


