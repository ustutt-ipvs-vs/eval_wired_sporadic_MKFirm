import os
from concurrent.futures import ThreadPoolExecutor

from emergency_eval.settings import EVAL_PATH
from eval import extract_data


def eval_for_path_with_run(path, run_num):
    extract_data(path, run_num)


if __name__ == "__main__":
    top_folder = os.path.join(EVAL_PATH, "t_3x4")
    run_folder = os.path.join(top_folder, "p_24/r_76/")
    scenario_folder = os.path.join(run_folder, "et_18")

    et_out = f"{scenario_folder}/etsn"
    et_out_2 = f"{scenario_folder}/etsn2"
    lib_out = f"{scenario_folder}/libtsndgm"

    with ThreadPoolExecutor(max_workers=6) as executor:
        for i in range(200):
            executor.submit(eval_for_path_with_run, et_out, i)
            executor.submit(eval_for_path_with_run, et_out_2, i)
            executor.submit(eval_for_path_with_run, lib_out, i)
