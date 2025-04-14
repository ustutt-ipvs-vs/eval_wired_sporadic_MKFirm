import os

from matplotlib import pyplot as plt


def eval_for_folder(top_folder, stream_folder, run_folder, et_folder, results):
    num_streams = int(stream_folder.split("_")[1])
    num_et_streams = int(et_folder.split("_")[1])

    if num_streams not in results:
        results[num_streams] = {}
    if num_et_streams not in results[num_streams]:
        results[num_streams][num_et_streams] = {
            "etsn": 0,
            "libtsndgm": 0,
        }

    if os.path.exists(f"{top_folder}/{stream_folder}/{run_folder}/{et_folder}/etsn_out.json"):
        results[num_streams][num_et_streams]["etsn"] += 1
    if os.path.exists(f"{top_folder}/{stream_folder}/{run_folder}/{et_folder}/libtsndgm_out.json"):
        results[num_streams][num_et_streams]["libtsndgm"] += 1


def plot_results(results):
    for num_streams, res_now in results.items():
        res_now_sorted = sorted(res_now)
        fig, ax = plt.subplots(figsize=(12, 6))
        x = [x for x in res_now_sorted]
        y1 = [res_now[x]["etsn"] for x in res_now_sorted]
        y2 = [res_now[x]["libtsndgm"] for x in res_now_sorted]
        ax.plot(x, y1)
        ax.plot(x, y2)
        fig.suptitle(f"#tt-streams: {num_streams}")
        ax.set_xlabel(f"#et streams")
        ax.set_ylabel(f"#Streamset Scheduled")
        fig.show()



def run_scheduler_for_topology(top_folder):
    results = {}
    for stream_folder in os.listdir(top_folder):
        if stream_folder.startswith("p_"):
            for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                if run_folder.startswith("r_"):
                    for et_folder in os.listdir(f"{top_folder}/{stream_folder}/{run_folder}"):
                        if et_folder.startswith("et_"):
                            eval_for_folder(top_folder, stream_folder, run_folder, et_folder, results)
    print(results)
    plot_results(results)


if __name__ == "__main__":
    for folder in os.listdir("."):
        if folder.startswith("t_"):
            run_scheduler_for_topology(folder)