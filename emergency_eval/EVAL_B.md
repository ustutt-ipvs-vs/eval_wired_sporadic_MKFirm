# Evaluation in Wired TSN with Sporadic Release Times

This document describes how to reproduce the results Section VI.B _Evaluation in Wired TSN with Sporadic Release Times_ of the paper.

## 1. Schedulability analysis

This section describes how to reproduce the schedulability analysis of the paper.

**Code**: The scripts used for the schedulability analysis are provided **TODO**

**Datasets**: The respective dataset of the (intermediate) results can be found [here](https://doi.org/10.5281/zenodo.19188040).

### Topology Generation

The topology is generated using the `gen_top.py` script.
The generated topology file `topology.json` used in our evaluation is provided in the root folder of the dataset.

### Streamset generation

The streamsets are generated using the `gen_streams.py` script.
The resulting streamsets used in our paper are provided in the `p_24` folder of the dataset with the following structure:
- Each `r_x` folder contains one isochronous streamset `streams.json` and multiple `et_y` subfolders.
- Each `et_y` subfolder contains one sporadic streamset `streams_et.json`, where `y` corresponds to the number of sporadic streams.

**TODO** We didn't use the line topology in this paper, did we?
If not, remove the `gen_streams_schedulabilitytest.py` script

### Scheduling

For the schedule calculation the following projects are required:
1. Our approch:
   1. The CP-based scheduler for the primary schedule for isochronous streams **TODO: Name? and folder name**
   2. Our augmentation approach **TODO: Name? and folder name**
2. Our implementation of E-TSN **TODO: folder name**

The results of the scheduler on our systems can be found in the respective folder under files with this `prefix`:
1. Our approach:
   1. CP-based primary schedule: `cp_out`
   2. Augmented schedule: `libtsndgm_out`
2. E-TSN: `etsn_out`

The following files are provided:
- `[prefix].json`: The schedule (If this file is missing, the scheduler did not complete successfully).
- `[prefix].log`: The output log of the scheduler.
- `[prefix]_meta.json`: Further metadata (such as the runtime and exit code).

## 2. Worst-Case Analysis (Simulation)
**TODO: We only simulated this one scenario, all other scenarios were only used for the schedulability calculation?**

The streamset with 24 isochronous and 24 sporadic streams used for the simulation-based worst-case analysis is provided
in folder `t_3x4/p_24/r_9/et_24`.

### Simulation Generation and Execution
Based on the provided topology and streamset file of the above scenario, an OMNeT++ simulation is generated and then executed using the `simulate_single_scenario_long.py` file.
The generated simulation files (`omnetpp.ini` and `Scenario.ned`) are contained in the `libtsndgm` for our approach and the `etsn` folder for E-TSN.
Futhermore, when generating the simulation scenario an additional `streams_meta.json` file is provided which is used in the next evaluation step.

### Data Extraction From the Simulation Results
**The simulation results are 30GB in total, do we need to publish them or can we omit them?**

Due to the size of the simulation results (`.vec` and `.sca` files), we cannot publish them in the raw format.
However, the provided `single_scenario_long.py` script extracts the important information and stores it in the `results_merged.pkl` file.
This file is provided with our datasets.

### Evaluation
**TOOD: There is also a `results.pkl` but i don't think we need it**

When executing the `single_scenario_long.py` script and the `results.pkl` file is present, it reads the data from this file instead of the raw simulation results.
Based on this data, the metrics provided in the paper are calculated

**TODO: I need to clean up this file, there is a lot of functionality that is not used in the paper at all**
