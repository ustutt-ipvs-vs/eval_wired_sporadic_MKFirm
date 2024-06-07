# Install requirements
For Linux / WSL.
```shell
pip install networkx
pip install pygraphviz
pip install PyQt6
sudo apt-get install graphviz graphviz-dev
```

# Generate Topology

Example for a star topology:
```shell
python3 topology/generate.py --star --nodes 20 
```

For more parameters and topology types execute
```shell
python3 topology/generate.py --help
```

# Generate TT-Streams
Example command with 5 streams:
```shell
python3 streams/generate.py -t examples/topology.json -i dummy_data/time-triggered_traffic.ini
```

For more parameters execute
```shell
python3 streams/generate.py --help
```

# Generate ET-Streams
Example command with 5 streams:
```shell
python3 emergency_streams/generate.py -t examples/topology.json -i dummy_data/emergency_traffic.ini
```

For more parameters execute
```shell
python3 emergency_streams/generate.py --help
```