# Fuzzy Thermal Control Simulation

This project simulates a fuzzy logic-based temperature control system. It dynamically adjusts the environment temperature toward a target value using fuzzy decision-making rules.

## Definition of Terms

- **Skew Rate**: The time delay (in seconds) required to apply a ±3°C change to the environment temperature.
- **Positive**: Indicates that the temperature is higher than the target (positive error) or that the error is increasing (positive error-dot).
- **Zero**: Indicates that the temperature is approximately equal to the target (zero error) or that the error is not changing (zero error-dot).
- **Negative**: Indicates that the temperature is lower than the target (negative error) or that the error is decreasing (negative error-dot).
- **COG (Center of Gravity)**: The defuzzified output representing the weighted average temperature adjustment.
- **Plant**: The simulated physical environment that undergoes temperature change.

## Requirements

- Python 3.x
- Required Python libraries:

```bash
pip install numpy matplotlib keyboard
```

## How to Run

Run the program using the command below:

```bash
python <filename>.py --temp TARGET_TEMP [--init INITIAL_TEMP] [--skew SKEW_RATE]
```

### Arguments

| Argument | Type  | Default  | Description                            |
| -------- | ----- | -------- | -------------------------------------- |
| `--temp` | float | Required | Target temperature to achieve          |
| `--init` | float | 0        | Initial environment temperature        |
| `--skew` | float | 2        | Time (in seconds) to apply ±3°C change |

### Example

```bash
python thermal.py --temp 30 --init 20 --skew 2
```

## Controls

- Press `c` to change the target temperature interactively during simulation.
- Press `q` to quit the simulation.

## Outputs

- **Graph 1 (Top)**: Displays the membership functions (cooler, no change, heater), fuzzy aggregation, and the Center of Gravity (COG) marker.
- **Graph 2 (Bottom)**: Displays the temperature history over time with a dashed line indicating the target temperature.
- **Terminal Display**:

```
Target: <value>°C | Current: <value>°C | Error: <value> | Error-dot: <value> | Action: <heater/cooler/no_change>
```

## Rule Matrix

| **Error-dot (ΔE)** / **Error (E)** | **Negative** | **Zero**  | **Positive** |
|------------------------------------|--------------|-----------|--------------|
| **Negative**                       | cooler       | cooler    | cooler       |
| **Zero**                           | heater       | no_change | cooler       |
| **Positive**                       | heater       | heater    | heater       |

## Notes

- The skew rate controls how fast the fixed ±3°C change is applied to the environment temperature.
- This simulation demonstrates the integration of fuzzy control with a modeled "plant" representing the environment.
- Suitable for educational demonstrations of fuzzy control concepts.

---
