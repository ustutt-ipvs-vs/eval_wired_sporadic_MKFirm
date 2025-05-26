import os

EVAL_PATH_SCHED = "/home/haugls/mnt_scratch/taurus/haugls2/emergency"
EVAL_PATH_SIM = "/scratch/haugls2/emergency2"

cplex_path = "/home/haugls/cplex/cpoptimizer/bin/x86-64_linux/cpoptimizer"
cp_based_scheduling_path = "../../cp-based-tsn-scheduling/main.py"
estn_scheduler_path = "../../e-tsn/main.py"
libtsndgm_path = "../../libtsndgm/release/DgmExec"

cplex_timelimit = 30 * 60 # 30 minutes

num_cpu_threads = os.cpu_count()
cplex_threads = 8
num_workers = num_cpu_threads // cplex_threads
num_sim_workers = num_cpu_threads - 1
