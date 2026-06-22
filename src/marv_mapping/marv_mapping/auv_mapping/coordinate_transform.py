"""
coordinate_transform.py

Coordinate transforms for mapping.
"""

import math


def polar_to_cartesian(

    x,

    y,

    heading_deg,

    distance

):

    heading = math.radians(

        heading_deg

    )

    world_x = x + distance * math.cos(heading)

    world_y = y + distance * math.sin(heading)

    return world_x, world_y


########################################################


def world_to_grid(

    x,

    y,

    cell_size

):

    row = int(y / cell_size)

    col = int(x / cell_size)

    return row, col


########################################################


def grid_to_world(

    row,

    col,

    cell_size

):

    x = col * cell_size

    y = row * cell_size

    return x, y


########################################################


def pixel_to_angle(

    pixel,

    image_width,

    horizontal_fov

):

    normalized = (

        pixel / image_width

    ) - 0.5

    return normalized * horizontal_fov


########################################################


def distance(

    x1,

    y1,

    x2,

    y2

):

    return math.sqrt(

        (x2 - x1) ** 2

        +

        (y2 - y1) ** 2

    )