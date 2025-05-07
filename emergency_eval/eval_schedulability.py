import os

from matplotlib import pyplot as plt

from emergency_eval.settings import EVAL_PATH


def eval_for_folder(top_folder, stream_folder, run_folder, et_folder, results):
    num_streams = int(stream_folder.split("_")[1])
    num_et_streams = int(et_folder.split("_")[1])

    if num_streams not in results:
        results[num_streams] = {}
    if num_et_streams not in results[num_streams]:
        results[num_streams][num_et_streams] = {
            "etsn": 0,
            "libtsndgm": 0,
            "etsn2": 0,
            "etsn_better": 0,
            "libtsndgm_better": 0,
        }

    etsn_success = False
    etsn2_success = False
    libtsndgm_succes = False

    if os.path.exists(f"{top_folder}/{stream_folder}/{run_folder}/{et_folder}/etsn_out.json"):
        results[num_streams][num_et_streams]["etsn"] += 1
        etsn_success = True
    if os.path.exists(f"{top_folder}/{stream_folder}/{run_folder}/{et_folder}/libtsndgm_out.json"):
        results[num_streams][num_et_streams]["libtsndgm"] += 1
        libtsndgm_succes = True
    if os.path.exists(f"{top_folder}/{stream_folder}/{run_folder}/{et_folder}/etsn2_out.json"):
        results[num_streams][num_et_streams]["etsn2"] += 1
        etsn2_success = True

    if etsn_success and not libtsndgm_succes:
        results[num_streams][num_et_streams]["etsn_better"] += 1
        print(f"etsn better for {top_folder}/{stream_folder}/{run_folder}/{et_folder}")
    elif libtsndgm_succes and not etsn_success:
        results[num_streams][num_et_streams]["libtsndgm_better"] += 1

    if etsn2_success and not etsn_success:
        print("ETSN2 is better than etsn??", top_folder, stream_folder, run_folder, et_folder)
    elif etsn_success and not etsn2_success:
        print("etsn better than etsn2", top_folder, stream_folder, run_folder, et_folder)

    if etsn_success and libtsndgm_succes and etsn2_success:
        pass
        print(f"all schedulers succeeded for {stream_folder} {et_folder} {run_folder}")

def plot_results(results):
    for num_streams, res_now in results.items():
        res_now_sorted = sorted(res_now)

        fig, ax = plt.subplots(figsize=(12, 6))
        x = [x for x in res_now_sorted]
        y1 = [res_now[x]["etsn"] for x in res_now_sorted]
        y2 = [res_now[x]["libtsndgm"] for x in res_now_sorted]
        y3 = [res_now[x]["etsn2"] for x in res_now_sorted]
        ax.plot(x, y1, label="etsn")
        ax.plot(x, y2, label="libtsndgm")
        ax.plot(x, y3, label="etsn2")
        fig.suptitle(f"#tt-streams: {num_streams}")
        ax.legend()
        ax.set_xlabel(f"#et streams")
        ax.set_ylabel(f"#Streamset Scheduled")
        fig.show()

        fig2, ax2 = plt.subplots(figsize=(12, 6))
        y1 = [res_now[x]["etsn_better"] for x in res_now_sorted]
        y2 = [res_now[x]["libtsndgm_better"] for x in res_now_sorted]
        # Plot as bar charts
        bar_width = 0.4
        ax2.bar([i - bar_width / 2 for i in x], y1, bar_width, label="etsn")
        ax2.bar([i + bar_width / 2 for i in x], y2, bar_width, label="libtsndgm")
        fig2.suptitle(f"#tt-streams: {num_streams}")
        ax2.legend()
        ax2.set_xlabel(f"#et streams")
        ax2.set_ylabel(f"#Additional Streamset Scheduled")
        fig2.show()


def plot_scatter(results):
    x = []
    y = []
    c = []
    colors = ["red", "blue", "green"]

    for num_tt_streams, res_tt in results.items():
        for num_et_streams, res in res_tt.items():
            if res["etsn"] == 0 and res["libtsndgm"] == 0:
                continue

            x.append(num_tt_streams)
            y.append(num_et_streams)
            if res["etsn"] > 0 and res["libtsndgm"] > 0:
                c.append(colors[2])
            elif res["etsn"] > 0:
                c.append(colors[0])
            elif res["libtsndgm"] > 0:
                c.append(colors[1])

    fig, ax = plt.subplots(figsize=(12, 6))
    scatter = ax.scatter(x, y, c=c)
    ax.set_xlabel("#tt-streams")
    ax.set_ylabel("#et-streams")
    ax.set_title("Scatter plot of schedulability results")
    legend_labels = ["etsn", "libtsndgm", "both"]
    legend_colors = [colors[0], colors[1], colors[2]]
    for i, label in enumerate(legend_labels):
        ax.scatter([], [], c=legend_colors[i], label=label)
    ax.legend()
    fig.show()





def eval_for_top(top_folder):
    results = {}
    for stream_folder in os.listdir(top_folder):
        if stream_folder.startswith("p_"):
            for run_folder in os.listdir(f"{top_folder}/{stream_folder}"):
                if run_folder.startswith("r_"):
                    for et_folder in os.listdir(f"{top_folder}/{stream_folder}/{run_folder}"):
                        if et_folder.startswith("et_"):
                            eval_for_folder(top_folder, stream_folder, run_folder, et_folder, results)
    plot_results(results)
    # plot_scatter(results)


if __name__ == "__main__":
    for folder in os.listdir(EVAL_PATH):
        if folder.startswith("t_"):
            folder = os.path.join(EVAL_PATH, folder)
            eval_for_top(folder)