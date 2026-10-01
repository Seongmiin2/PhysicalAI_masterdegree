from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_config

FAULTS = ("cooling_loss", "feed_stuck", "pressure_leak", "agitator_loss")
ACTIONS = ("increase_cooling", "reduce_feed", "close_purge", "restart_agitator")
CORRECT = dict(zip(FAULTS, ACTIONS, strict=True))


def generate(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(int(config["seed"]))
    rows, episodes = [], []
    count, steps = int(config["episodes"]), int(config["steps_per_episode"])
    for episode_index in range(count):
        episode_id = f"tep-{episode_index:07d}"
        mode = f"mode_{episode_index % 6 + 1}"
        fault = FAULTS[episode_index % len(FAULTS)]
        action = ACTIONS[int(rng.integers(0, len(ACTIONS)))]
        onset = int(rng.integers(steps // 4, steps // 2))
        action_step = onset + int(rng.integers(2, 9))
        severity = float(rng.uniform(0.5, 1.5))
        applicable = action == CORRECT[fault]
        pressure, temperature, reactor_level, separator_level = 2800.0, 120.0, 65.0, 50.0
        recovered_at, unsafe = None, False
        for step in range(steps):
            fault_active = step >= onset
            action_active = step >= action_step
            feed, purge, cooling, agitator = 50.0, 22.0, 48.0, 100.0
            if action_active:
                if action == "increase_cooling": cooling += 28
                elif action == "reduce_feed": feed -= 20
                elif action == "close_purge": purge -= 15
                else: agitator += 25
            drift_p = drift_t = drift_l = 0.0
            if fault_active:
                if fault == "cooling_loss": drift_t = 2.0 * severity
                elif fault == "feed_stuck": drift_l = 1.2 * severity
                elif fault == "pressure_leak": drift_p = -18.0 * severity
                else: drift_t, drift_p = 0.8 * severity, 8.0 * severity
            mitigation = 0.78 if applicable and action_active else 0.0
            pressure += drift_p * (1 - mitigation) + 0.05 * (feed - 50) - 0.04 * (purge - 22) + rng.normal(0, 2)
            temperature += drift_t * (1 - mitigation) - 0.06 * (cooling - 48) + rng.normal(0, 0.15)
            reactor_level += drift_l * (1 - mitigation) + 0.02 * (feed - 50) + rng.normal(0, 0.1)
            separator_level += 0.03 * (reactor_level - 65) + rng.normal(0, 0.1)
            unsafe = unsafe or pressure > config["unsafe_pressure"] or temperature > config["unsafe_temperature"] or reactor_level > 95
            if applicable and action_active and recovered_at is None and step >= action_step + 6 and not unsafe:
                recovered_at = step
            rows.append({"episode_id": episode_id, "step": step, "operating_mode": mode, "fault_type": fault, "fault_active": int(fault_active), "candidate_action": action, "action_active": int(action_active), "reactor_pressure": pressure, "reactor_temperature": temperature, "reactor_level": reactor_level, "separator_level": separator_level, "feed_valve": feed, "purge_valve": purge, "cooling_water": cooling, "agitator_speed": agitator})
        success = recovered_at is not None and not unsafe
        episodes.append({"external_id": episode_id, "operating_mode": mode, "fault_type": fault, "current_state": {"pressure": rows[-1]["reactor_pressure"], "temperature": rows[-1]["reactor_temperature"], "level": rows[-1]["reactor_level"]}, "candidate_action": action, "action_sequence": [{"step": action_step, "action": action}], "recovery_success": success, "recovery_time": None if recovered_at is None else (recovered_at - action_step) * config["sample_seconds"], "constraint_violation": unsafe, "unsafe_state": unsafe, "applicability_label": "applicable" if applicable else "not_applicable", "fault_onset": onset, "action_step": action_step, "severity": severity})
    episode_frame = pd.DataFrame(episodes)
    outcome_map = episode_frame.set_index("external_id")["recovery_success"]
    telemetry = pd.DataFrame(rows)
    telemetry["recovery_success"] = telemetry["episode_id"].map(outcome_map).astype(int)
    return telemetry, episode_frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    telemetry, episodes = generate(config)
    output = Path(config["paths"]["raw"])
    output.mkdir(parents=True, exist_ok=True)
    telemetry.to_parquet(output / "synthetic_episodes.parquet", index=False)
    episodes.to_json(output / "episodes.jsonl", orient="records", lines=True, force_ascii=False)
    print({"episodes": len(episodes), "telemetry_rows": len(telemetry), "output": str(output)})


if __name__ == "__main__":
    main()
