import os

# Settings for the Schedulability analysis
EVAL_PATH_SCHED = "./dsn_eval/schedulability"

## Settings for the scheduler phase
cplex_path = "/home/haugls/cplex/cpoptimizer/bin/x86-64_linux/cpoptimizer"
cp_based_scheduling_path = "../../cp-based-tsn-scheduling/main.py"
estn_scheduler_path = "../../e-tsn/main.py"
libtsndgm_path = "../../libtsndgm/release/DgmExec"

cplex_timelimit = 30 * 60 # 30 minutes

num_cpu_threads = os.cpu_count()
cplex_threads = 8
num_workers = num_cpu_threads // cplex_threads


# Settings for the Worst Case Analysis Simulation
EVAL_PATH_SIM = "./dsn_eval/simulation"
INET_PATH = "/path/to/inet"
num_runs = 100
num_sim_workers = num_cpu_threads - 1