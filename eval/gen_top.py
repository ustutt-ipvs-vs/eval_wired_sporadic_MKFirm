from generate_Topology import main

if __name__ == "__main__":
    for n in range(2,5):
        path = f"t_{n}x{n+1}"
        main(nodes=n, grid=True, output_path=path, processing_delay_ns=2000, propagation_delay_ns=200)