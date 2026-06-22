"""
occupancy_grid.py

Stores and manipulates the occupancy grid.

Uses NumPy for fast updates.
"""

import numpy as np

from .constants import MappingConstants


class OccupancyGrid:

    def __init__(
        self,
        width=MappingConstants.GRID_WIDTH,
        height=MappingConstants.GRID_LENGTH,
        cell_size=MappingConstants.CELL_SIZE
    ):

        self.width = width
        self.height = height
        self.cell_size = cell_size

        self.grid = np.full(
            (height, width),
            MappingConstants.UNKNOWN,
            dtype=np.float32
        )

        self.labels = {}

    ######################################################

    def reset(self):

        self.grid.fill(MappingConstants.UNKNOWN)

        self.labels.clear()

    ######################################################

    def world_to_grid(self, x, y):

        row = int(y / self.cell_size)
        col = int(x / self.cell_size)

        return row, col

    ######################################################

    def grid_to_world(self, row, col):

        x = col * self.cell_size

        y = row * self.cell_size

        return x, y

    ######################################################

    def in_bounds(self, row, col):

        return (

            0 <= row < self.height

            and

            0 <= col < self.width

        )

    ######################################################

    def occupancy(self, row, col):

        if not self.in_bounds(row, col):

            return None

        return self.grid[row, col]

    ######################################################

    def increase(self, row, col):

        if not self.in_bounds(row, col):
            return

        self.grid[row, col] = min(

            MappingConstants.MAX_OCCUPANCY,

            self.grid[row, col]
            +
            MappingConstants.OCCUPANCY_INCREMENT

        )

    ######################################################

    def decrease(self, row, col):

        if not self.in_bounds(row, col):
            return

        self.grid[row, col] = max(

            MappingConstants.MIN_OCCUPANCY,

            self.grid[row, col]
            -
            MappingConstants.OCCUPANCY_DECREMENT

        )

    ######################################################

    def add_label(

        self,

        row,

        col,

        label

    ):

        self.labels[(row, col)] = label

    ######################################################

    def get_label(

        self,

        row,

        col

    ):

        return self.labels.get(

            (row, col),

            None

        )