import math
import numpy as np
import numpy.linalg as npl


def in_convex_area(point, points):
    for i in range(-1, len(points) - 1):
        if dis_from_line(points[i], points[i + 1], point) > 0:
            return False
    return True  # make sure its really cw or ccw


def use_normal_refract(previous_point, points_of_rectangle):  #
    return dis_from_line(points_of_rectangle[0], points_of_rectangle[1], previous_point) > -5 or \
            dis_from_line(points_of_rectangle[2], points_of_rectangle[3], previous_point) > -5


def which_angle(checked_loc, points):
    for i in range(0, len(points)):
        if dis_from_line(points[i - 1], points[i], checked_loc) > -5:
            return i


def dis_from_line(p1, p2, point_from_line):
    p2_minus_p1 = np.subtract(p2, p1)
    return np.cross(p2_minus_p1, np.subtract(point_from_line, p1)) / npl.norm(p2_minus_p1)
