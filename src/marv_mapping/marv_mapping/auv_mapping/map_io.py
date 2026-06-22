"""
map_io.py

Load and save occupancy grids and landmark databases.
"""

import json
import numpy as np


class MapIO:

    @staticmethod
    def save_grid(grid, filename):

        np.save(filename, grid.grid)

    ###################################################

    @staticmethod
    def load_grid(grid, filename):

        grid.grid = np.load(filename)

    ###################################################

    @staticmethod
    def save_labels(grid, filename):

        data = []

        for (row, col), label in grid.labels.items():

            data.append({

                "row": row,

                "col": col,

                "label": label

            })

        with open(filename, "w") as f:

            json.dump(data, f, indent=4)

    ###################################################

    @staticmethod
    def load_labels(grid, filename):

        with open(filename) as f:

            data = json.load(f)

        grid.labels.clear()

        for item in data:

            grid.labels[(item["row"], item["col"])] = item["label"]

    ###################################################

    @staticmethod
    def save_landmarks(database, filename):

        output = []

        for landmark in database.landmarks:

            output.append({

                "label": landmark.label,

                "x": landmark.x,

                "y": landmark.y,

                "z": landmark.z,

                "confidence": landmark.confidence,

                "observations": landmark.observations

            })

        with open(filename, "w") as f:

            json.dump(output, f, indent=4)

    ###################################################

    @staticmethod
    def load_landmarks(database, filename):

        from .types import Landmark

        database.landmarks.clear()

        with open(filename) as f:

            data = json.load(f)

        for item in data:

            database.landmarks.append(

                Landmark(

                    label=item["label"],

                    x=item["x"],

                    y=item["y"],

                    z=item["z"],

                    confidence=item["confidence"],

                    observations=item["observations"]

                )

            )