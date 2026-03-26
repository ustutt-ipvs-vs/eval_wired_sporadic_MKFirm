import os

# Settings for the Schedulability analysis
EVAL_PATH_SCHED = "./dsn26_schedulability"

## Settings for the scheduler phase
cplex_path = ""
cp_based_scheduling_path = ""
estn_scheduler_path = ""
libtsndgm_path = ""

cplex_timelimit = 0

num_cpu_threads = os.cpu_count()
cplex_threads = 8
num_workers = num_cpu_threads // cplex_threads


# Settings for the Worst Case Analysis Simulation
EVAL_PATH_SIM = "./dsn26_worstcase"
INET_PATH = "../inet"
num_runs = 2
sim_time_seconds = 1
num_sim_workers = 4