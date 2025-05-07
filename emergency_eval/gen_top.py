from emergency_eval.settings import EVAL_PATH
from generate_Topology import main

if __name__ == "__main__":
    for n in range(3,4):
        path = f"{EVAL_PATH}/t_{n}x{n+1}"
        main(nodes=n, grid=True, output_path=path, processing_delay_ns=2000, propagation_delay_ns=200)
    main(nodes=3, line=True, output_path=f"{EVAL_PATH}/l_3", processing_delay_ns=2000, propagation_delay_ns=200)