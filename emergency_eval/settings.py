EVAL_PATH = "/scratch/haugls2/emergency"

cplex_path = "/home/haugls/cplex/cpoptimizer/bin/x86-64_linux/cpoptimizer"
cp_based_scheduling_path = "../../cp-based-tsn-scheduling/main.py"
estn_scheduler_path = "../../e-tsn/main.py"
libtsndgm_path = "../../libtsndgm/release/DgmExec"

cplex_timelimit = 30 * 60 # 30 minutes

num_cpu_threads = 96
cplex_threads = 8
num_workers = num_cpu_threads // cplex_threads