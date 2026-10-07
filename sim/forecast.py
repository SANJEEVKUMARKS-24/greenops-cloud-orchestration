"""
Carbon-intensity forecasting with configurable uncertainty.

Real schedulers never see the future carbon intensity - they see a
FORECAST from a grid-intensity API (Carbon Aware SDK, WattTime,
Electricity Maps). This module stands in for that API.

Error model
-----------
For a forecast issued at time `now` for target hour `t`
(horizon h = t - now):

    forecast(now, t) = actual(t) * (1 + sigma(h) * z_r(t))

    sigma(h) = error_level * sqrt(min(h, 24) / 24)

* sigma(0) = 0       -> the current intensity is measured, not forecast.
* sigma(24) = error_level  -> e.g. 0.10 means ~10% error one day ahead.
* z_r(t) is an AR(1) process per region (rho = 0.7), so forecast errors
  are correlated over consecutive hours, as observed in real forecasts.
  Because z_r(t) is fixed per target hour, re-planning closer to t gives
  a forecast that converges to the truth instead of a new random draw.

`error_level = 0` reproduces a perfect-information oracle.

Calibration
-----------
National Grid ESO's published forecasts for Great Britain (Jan and Jul
2024, see data/carbon_traces/historical/*/great_britain.csv) have a
relative RMSE of 0.11-0.15 and lag-1 error autocorrelation of 0.62-0.69.
REALISTIC_ERROR = 0.15 and rho = 0.7 reproduce that behaviour.
"""

import math
import random


REALISTIC_ERROR = 0.15


class CarbonForecaster:

    def __init__(
        self,
        regions,
        error_level=0.0,
        seed=0,
        correlation=0.7
    ):

        self.error_level = error_level

        self.seed = seed

        self.correlation = correlation

        self._noise = {}

        for index, region in enumerate(regions):

            self._noise[region.name] = self._ar1_series(
                region.trace_length,
                random.Random(seed * 1000 + index)
            )

    # ==================================================
    # NOISE PROCESS
    # ==================================================

    def _ar1_series(self, length, rng):

        rho = self.correlation

        innovation = math.sqrt(1 - rho ** 2)

        values = []

        z = rng.gauss(0, 1)

        for _ in range(length):

            values.append(z)

            z = rho * z + innovation * rng.gauss(0, 1)

        return values

    # ==================================================
    # UNCERTAINTY AS A FUNCTION OF HORIZON
    # ==================================================

    def sigma(self, horizon):

        if horizon <= 0 or self.error_level <= 0:
            return 0.0

        return self.error_level * math.sqrt(
            min(horizon, 24.0) / 24.0
        )

    # ==================================================
    # POINT FORECAST
    # ==================================================

    def forecast(self, region, now, target_time):

        actual = region.get_carbon_intensity(target_time)

        if actual is None:
            return None

        horizon = math.floor(target_time) - math.floor(now)

        sigma = self.sigma(horizon)

        if sigma == 0:
            return actual

        noise = self._noise[region.name]

        z = noise[int(math.floor(target_time)) % len(noise)]

        # Intensity can never be negative.
        return max(0.0, actual * (1 + sigma * z))

    # ==================================================
    # FORECAST AVERAGED OVER A RUN WINDOW
    # ==================================================

    def forecast_average(
        self,
        region,
        now,
        start_time,
        duration
    ):

        if duration <= 0:
            return self.forecast(region, now, start_time)

        end_time = start_time + duration

        total = 0.0

        t = start_time

        while t < end_time - 1e-9:

            next_boundary = min(math.floor(t) + 1, end_time)

            value = self.forecast(region, now, t)

            if value is None:
                return None

            total += value * (next_boundary - t)

            t = next_boundary

        return total / duration
