from emergency_eval.settings import EVAL_PATH_SCHED
from generate_Topology import main

if __name__ == "__main__":
    n = 3
    path = f"{EVAL_PATH_SCHED}/t_{n}x{n+1}"
    main(nodes=n, grid=True, output_path=path, processing_delay_ns=2000, propagation_delay_ns=200)