echo "=== Starting eval ==="
source /usr/src/omnetpp/setenv
rm emergency_eval/settings.py
mv emergency_eval/settings_docker.py emergency_eval/settings.py
export PYTHONPATH="${PYTHONPATH}:emergency_eval:."
python3 emergency_eval/simulate_single_scenario_long.py
python3 emergency_eval/eval_single_long.py