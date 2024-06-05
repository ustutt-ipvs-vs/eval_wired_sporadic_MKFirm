# Generate Topology

Example for a star topology:
```shell
python3 topology/generate.py --star --nodes 20 
```

For more parameters and topology types execute
```shell
python3 topology/generate.py --help
```

# Generate Streams
Example command with 5 streams:
```shell
python3 streams/generate.py --ns 5 --cycle 1000000 --topology examples/topology.json
```

For more parameters execute
```shell
python3 streams/generate.py --help
```