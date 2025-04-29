import configparser
import os

from emergency_eval.settings import EVAL_PATH
from generate_TT import main as main_tt
from generate_ET import main as main_et

if __name__ == "__main__":
    # Find folders starting with t_

    streams_per_device = [0.5, 1, 1.5, 2]

    ini_path_tt = f"time-triggered_traffic.ini"
    config_tt = configparser.ConfigParser()
    if not os.path.isfile(ini_path_tt):
        raise FileNotFoundError
    config_tt.read(ini_path_tt)

    ini_path_et = f"emergency_traffic.ini"
    config_et = configparser.ConfigParser()
    if not os.path.isfile(ini_path_et):
        raise FileNotFoundError
    config_et.read(ini_path_et)

    for folder in os.listdir(EVAL_PATH):
        if folder.startswith("t_"):
            folder = f"{EVAL_PATH}/{folder}"
            print(f"Generate streams for {folder}")

            grid_size = folder.split("_")[1].split("x")
            devices = int(grid_size[0]) * int(grid_size[1])

            for perc_tt in streams_per_device:
                n_tt = int(devices * perc_tt)
                config_tt.set("generic", "number_of_tt_streams", str(n_tt))

                for i in range(100):
                    for n_et in range(1, 2 * n_tt + 1):
                        out_folder_tt = f"{folder}/p_{n_tt}/r_{i}"
                        out_folder_et = f"{folder}/p_{n_tt}/r_{i}/et_{n_et}"
                        os.makedirs(out_folder_et, exist_ok=True)
                        main_tt(topology=f"{folder}/topology.json", output=f"{out_folder_tt}/streams.json",
                                config=config_tt)

                        config_et.set("generic", "number_of_emergency_streams", str(n_et))

                        # TODO: figure out how to generate ET streams
                        main_et(f"{folder}/topology.json",
                                config_et,
                                f"{out_folder_et}/streams_et.json"
                                # f"{out_folder}/streams.json", # TODO use or not?
                                )
