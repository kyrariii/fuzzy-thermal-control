"""
Fuzzy Thermal Control Simulation

Definition of Terms:
- **Skew Rate**: The time delay (in seconds) required to apply a ±3°C change to the environment temperature.
- **Positive**: Indicates that the temperature is higher than the target (positive error) or that the error is increasing (positive error-dot).
- **Zero**: Indicates that the temperature is approximately equal to the target (zero error) or that the error is not changing (zero error-dot).
- **Negative**: Indicates that the temperature is lower than the target (negative error) or that the error is decreasing (negative error-dot).
- **COG (Center of Gravity)**: The defuzzified output representing the weighted average temperature adjustment.
- **Plant**: The simulated physical environment that undergoes temperature change.
"""
import numpy as np
import matplotlib.pyplot as plt
import argparse
import math
from keyboard import is_pressed
import time

class InvalidPoints(Exception):
    """Exception raised for invalid number of points in a membership function."""

    def __init__(self, formula_name):
        self.message = f"{formula_name} does not contain three or four points"
        super().__init__(self.message)


class MembershipFunction:
    """Represents a fuzzy membership function."""

    def __init__(self, name):
        """
        Initializes the membership function.

        Args:
            name (str): Name of the membership function.
        """
        self.__name__ = name
        self.formulas = {}

    def append(self, formula_name, points):
        """
        Adds a new formula to the membership function.

        Args:
            formula_name (str): Name of the formula.
            points (list): List of 3 or 4 points defining the function shape.

        Raises:
            InvalidPoints: If the number of points is not 3 or 4.
        """
        if not 3 <= len(points) <= 4:
            raise InvalidPoints(formula_name)
        self.formulas[formula_name] = points

    def fuzzify_from(self, formula_name, x):
        """
        Computes the degree of membership for a specific formula at input x.

        Args:
            formula_name (str): Name of the formula.
            x (float): Input value.

        Returns:
            float: Degree of membership.
        """
        if len(self.formulas[formula_name]) == 4:
            a, b, c, d = self.formulas[formula_name]
            return max(min((x-a)/(b-a), 1, (d-x)/(d-c)), 0)
        else:
            a, b, c = self.formulas[formula_name]
            return max(min((x-a)/(b-a), (c-x)/(c-b)), 0)

    def fuzzify_all(self, x):
        """
        Computes the degrees of membership for all formulas at input x.

        Args:
            x (float): Input value.

        Returns:
            dict: Mapping of formula names to their degree of membership.
        """
        return {key: self.fuzzify_from(key, x) for key in self.formulas}


class Plant:
    """Represents the physical system affected by the control actions."""

    def __init__(self, skew_rate=2, change_value=3):
        """
        Initializes the plant.

        Args:
            skew_rate (float): Time in seconds to apply the change.
            change_value (float): Temperature change per adjustment.
        """
        self.skew_rate = skew_rate
        self.change_value = change_value

    def apply_change(self, environment_temp, crisp_output):
        # Normalize COG output to a 0 to 1 scale based on maximum temperature considered (here 100°C for example)
        scale = min(abs(crisp_output) / 100, 1)
        applied_change = round(self.change_value * scale, 2)

        if abs(crisp_output) < 1e-2 or applied_change < 0.01:  # If output is near zero, stop adjusting
            action = "no_change"
        elif crisp_output > 0:
            environment_temp += applied_change
            action = "heater"
        elif crisp_output < 0:
            environment_temp -= applied_change
            action = "cooler"

        time.sleep(self.skew_rate)
        return round(environment_temp, 2), action



class ThermalControl:
    """Implements the fuzzy thermal control logic."""

    def __init__(self, command, initial_temp, temp_function, error_function, error_dot_function, plant):
        """
        Initializes the thermal control system.

        Args:
            command (float): Target temperature.
            initial_temp (float): Initial environment temperature.
            temp_function (MembershipFunction): Output membership function.
            error_function (MembershipFunction): Error membership function.
            error_dot_function (MembershipFunction): Change of error membership function.
            plant (Plant): Plant representing the physical system.
        """
        self.target_temp = command
        self.environment_temp = initial_temp
        self.current_error = self.target_temp - self.environment_temp
        self.previous_error = 0
        self.change_error = self.previous_error - self.current_error

        self.temp_function = temp_function
        self.error_function = error_function
        self.error_dot_function = error_dot_function
        self.plant = plant

        self.number_of_temps = 200
        self.temperature = np.linspace(-100, 100, 200)
        self.aggregation = []

        self.orig_cool = [self.temp_function.fuzzify_from('cooler', x) for x in self.temperature]
        self.orig_hot = [self.temp_function.fuzzify_from('heater', x) for x in self.temperature]
        self.orig_zero = [self.temp_function.fuzzify_from('no_change', x) for x in self.temperature]

        self.temperature_history = [self.environment_temp] * 50
        self.COG = 0

    def calculate_change(self):
        """
        Calculates the change in temperature based on fuzzy logic.

        Returns:
            str: Action taken ("heater", "cooler", or "no_change").
        """
        error_degree = self.error_function.fuzzify_all(self.current_error)
        error_dot_degree = self.error_dot_function.fuzzify_all(self.change_error)

        # Fuzzy rule matrix
        table = {
            "positive": {
                "positive": [min(self.temp_function.fuzzify_from("heater", x), min(error_degree["positive"], error_dot_degree["positive"])) for x in self.temperature],
                "zero": [min(self.temp_function.fuzzify_from("heater", x), min(error_degree["positive"], error_dot_degree["zero"])) for x in self.temperature],
                "negative": [min(self.temp_function.fuzzify_from("heater", x), min(error_degree["positive"], error_dot_degree["negative"])) for x in self.temperature]
            },
            "negative": {
                "positive": [min(self.temp_function.fuzzify_from("cooler", x), min(error_degree["negative"], error_dot_degree["positive"])) for x in self.temperature],
                "zero": [min(self.temp_function.fuzzify_from("cooler", x), min(error_degree["negative"], error_dot_degree["zero"])) for x in self.temperature],
                "negative": [min(self.temp_function.fuzzify_from("cooler", x), min(error_degree["negative"], error_dot_degree["negative"])) for x in self.temperature]
            },
            "zero": {
                "positive": [min(self.temp_function.fuzzify_from("cooler", x), min(error_degree["zero"], error_dot_degree["positive"])) for x in self.temperature],
                "zero": [min(self.temp_function.fuzzify_from("no_change", x), min(error_degree["zero"], error_dot_degree["zero"])) for x in self.temperature],
                "negative": [min(self.temp_function.fuzzify_from("heater", x), min(error_degree["zero"], error_dot_degree["negative"])) for x in self.temperature]
            }
        }

        self.aggregation = [max(i) for i in zip(
            table["positive"]["positive"], table["positive"]["zero"], table["positive"]["negative"],
            table["negative"]["positive"], table["negative"]["zero"], table["negative"]["negative"],
            table["zero"]["positive"], table["zero"]["zero"], table["zero"]["negative"]
        )]

        numerator = np.sum(self.aggregation * self.temperature)
        denominator = np.sum(self.aggregation)

        if denominator == 0:
            return "no_change"

        self.COG = round(numerator / denominator, 2)

        self.environment_temp, action = self.plant.apply_change(self.environment_temp, self.COG)
        return action

    def record_history(self):
        """Updates the temperature history with the latest value."""
        self.temperature_history.pop(0)
        self.temperature_history.append(self.environment_temp)

    def calculate_error(self):
        """Updates the current and previous error values."""
        self.previous_error = self.current_error
        self.current_error = self.target_temp - self.environment_temp
        self.change_error = self.previous_error - self.current_error

    def check_key(self):
        """
        Checks for keyboard input to change target temperature or quit.
        """
        if is_pressed('c'):
            try:
                self.target_temp = float(input("What temperature to change? -> "))
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
        if is_pressed('q'):
            exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fuzzy Thermal Controller with Plant")
    parser.add_argument("--temp", type=float, required=True, help="Target temperature")
    parser.add_argument("--init", type=float, default=0, help="Initial environment temperature")
    parser.add_argument("--skew", type=float, default=2, help="Skew rate: time to apply ±3°C change")
    args = parser.parse_args()

    # Initialize fuzzy membership functions for error, error_dot, and output
    error = MembershipFunction("error")
    error.append("negative", [-1000, -999, -2, 0])
    error.append("zero", [-2, 0, 2])
    error.append("positive", [0, 2, 999, 1000])

    error_dot = MembershipFunction("error_dot")
    error_dot.append("negative", [-1000, -999, -5, 0])
    error_dot.append("zero", [-50, 0, 5])
    error_dot.append("positive", [0, 5, 999, 1000])

    temp_output = MembershipFunction("temp_output")
    temp_output.append("cooler", [-1000, -999, -50, 0])
    temp_output.append("no_change", [-50, 0, 50])
    temp_output.append("heater", [0, 50, 999, 1000])

    plant = Plant(skew_rate=args.skew, change_value=3)

    thermal = ThermalControl(args.temp, args.init, temp_output, error, error_dot, plant)

    plt.rcParams['toolbar'] = 'None'
    figs, axes = plt.subplots(2)

    # Main simulation loop
    while True:
        action = thermal.calculate_change()
        thermal.calculate_error()
        thermal.check_key()
        thermal.record_history()

        print(f"Target: {thermal.target_temp}°C | Current: {thermal.environment_temp}°C | Error: {thermal.current_error:.2f} | Error-dot: {thermal.change_error:.2f} | Action: {action}")

        axes[0].cla()
        axes[1].cla()
        axes[0].plot(thermal.temperature, thermal.orig_cool, linestyle='dashed', color="blue", label='Cooler')
        axes[0].plot(thermal.temperature, thermal.orig_zero, linestyle='dashed', color="gray", label='No Change')
        axes[0].plot(thermal.temperature, thermal.orig_hot, linestyle='dashed', color="red", label='Heater')
        axes[0].plot(thermal.temperature, thermal.aggregation, color="black", label='Aggregation')
        axes[0].fill_between(thermal.temperature, thermal.aggregation, alpha=0.5, color='gray')
        index = math.ceil(thermal.number_of_temps/2 + thermal.COG)
        if 0 <= index < len(thermal.aggregation):
            axes[0].plot(thermal.COG, thermal.aggregation[index]/2, 'ro')
        axes[0].legend()
        axes[0].axis([-100, 100, 0, 1.2])
        axes[0].set_xlabel("Output Temperature (°C)")
        axes[0].set_ylabel("Membership Degree")
        axes[0].set_title(f"Target Temp: {thermal.target_temp}°C | Current Temp: {thermal.environment_temp}°C")

        axes[1].plot(thermal.temperature_history, color="blue")
        axes[1].axhline(y=thermal.target_temp, linestyle='dashed')
        axes[1].set_xlabel("Time Steps")
        axes[1].set_ylabel("Environment Temperature (°C)")

        plt.pause(0.01)
