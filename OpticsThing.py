import pygame.gfxdraw
import math
import numpy as np
import utility


class Line(object):

    def __init__(self, loc, angle, n=1, c=-1):
        self.color = c
        self.angle = angle
        self.dl = 5
        self.dxy = np.multiply((math.cos(angle), -math.sin(angle)), self.dl)
        self.next_loc = loc
        self.previous_loc = loc
        self.current_n = n
        self.points = [loc]
        self.current_medium = None

    def refresh_angle(self):
        self.dxy = np.multiply((math.cos(self.angle), -math.sin(self.angle)), self.dl)

    def extend(self):
        self.previous_loc = self.next_loc
        self.next_loc = np.add(self.next_loc, self.dxy)

    def extend_until_hit(self, objects):
        while on_screen(self.next_loc):
            self.extend()
            self.interact_with_objects(objects)
        self.points.append(self.next_loc)

    def interact_with_objects(self, objects):
        for obj in objects:
            if obj.in_area(self.next_loc):
                obj.bend(self)
                return
        if self.current_medium is not None:
            self.bend_line_snells(None)

    def get_points(self):
        return self.points

    def bend_line_snells(self, medium):
        if medium is None:
            n2 = 1
            medium = self.current_medium
            self.current_medium = None
            checked_loc = self.previous_loc
        else:
            n2 = medium.get_n(self.color)
            self.current_medium = medium
            checked_loc = self.next_loc
        if self.current_n == n2:
            return
        self.points.append(self.previous_loc)
        angle2 = medium.get_angle(checked_loc)  # basically return angle of exit edge
        angle_diff = self.angle - angle2
        normal = angle2 + math.pi / 2 if angle_diff > 0 else angle2 - math.pi / 2
        if angle_diff > math.pi:
            normal -= math.pi
        elif angle_diff < -math.pi:
            normal += math.pi
        angle1 = (self.angle - normal)
        s = (self.current_n / n2) * math.sin(angle1)
        if abs(s) > 1:
            print('tir')
            self.angle += 2*angle1  # reflection
            return
        self.angle = normal + math.asin(s)
        self.refresh_angle()
        self.current_n = n2

    def reflect(self, angle2):
        return

    def draw(self, scr):
        points = self.points
        points.append(self.next_loc)
        for i in range(len(points) - 1):
            pygame.draw.line(scr, (255, 255, 255), points[i], points[i + 1], 3)


class LightLine(object):

    def __init__(self, loc, angle, col, n):
        self.current_n = n
        self.width = 10
        self.angle = angle
        self.color = col
        dis_from_center = np.multiply((-math.sin(angle), math.cos(angle)), self.width)
        self.lines = [Line(np.add(loc, dis_from_center), angle, n),
                      Line(np.subtract(loc, dis_from_center), angle, n)]

    # turn into extend until hit
    def extend(self, objects):
        new_lines = []
        for line in self.lines:
            line.extend_until_hit(objects)

    def draw(self, scr):
        pygame.draw.polygon(scr, self.color, self.lines[0].get_points() + list(reversed(self.lines[1].get_points())))


class RefractArea(object):  # Rectangles only

    def __init__(self, p1, p2, third_click, n):  # p1 and p2 are one length, 3rd click determines width
        w = utility.dis_from_line(p1, p2, third_click)
        dx, dy = np.subtract(p1, p2)
        self.length = math.sqrt(dx * dx + dy * dy)
        self.n = n
        self.angle = math.atan2(* np.subtract(p2, p1))
        self.normal = self.angle + math.pi/2 if self.angle < 0 else self.angle - math.pi/2
        p3, p4 = np.add((p2, p1), np.multiply((dy, -dx), w / self.length))
        self.points = [p1, p2, tuple(p3), tuple(p4)]
        if w > 0:
            self.points.reverse()

    def draw(self, scr):
        pygame.gfxdraw.filled_polygon(scr, self.points, (50, 255, 255, 100))

    def in_area(self, point):
        return utility.in_convex_area(point, self.points)

    def get_n(self, c):
        return self.n

    def get_angle(self, checked_loc):
        return self.angle if utility.which_angle(checked_loc, self.points) % 2 == 0 else self.normal

    def bend(self, line):
        line.bend_line_snells(self)


class Prism(object):

    ns_red_to_violet = [1.513, 1.516, 1.519, 1.5225, 1.526, 1.528, 1.532]

    def __init__(self, p1, p2, p3):
        self.points = [p1, p2, p3]
        if np.cross(np.subtract(p3, p2), np.subtract(p2, p1)) < 0:
            self.points.reverse()
        self.angles = []  # starting with p3 to p1, p1 to p2, etc
        for i in range(-1, 2):
            self.angles.append(math.atan2(* reversed(np.subtract(self.points[i+1], self.points[i]))))

    def in_area(self, point):
        return utility.in_convex_area(point, self.points)

    def get_n(self, color):
        return Prism.ns_red_to_violet[color]

    def get_angle(self, checked_loc):  # assumed already in area
        return self.angles[utility.which_angle(checked_loc, self.points)]

    def bend(self, line):
        line.bend_line_snells(self)


width = 800
height = 800


def on_screen(point):
    x = point[0]
    y = point[1]
    return 0 <= x <= width and 0 <= y <= height


pygame.init()
Black = (0, 0, 0)
White = (255, 255, 255)
Red = (255, 0, 0)
Orange = (255, 127, 0)
Yellow = (255, 255, 0)
Green = (0, 255, 0)
Blue = (0, 0, 255)
Indigo = (75, 0, 130)
Violet = (148, 0, 211)
colors = [Red, Orange, Yellow, Green, Blue, Indigo, Violet]

screen = pygame.display.set_mode((width, height))
screen.fill(Black)

light_surface = pygame.Surface((800, 800))
light_surface.fill(Black)
light_surface.set_colorkey(Black)

surfaces = []
for color in colors:
    surfaces.append([pygame.Surface((300, 300)), color])

flag = pygame.BLEND_RGBA_ADD

# for surface, color in surfaces:
#     pygame.draw.circle(surface, color, (150, 150), 150)
#     light_surface.blit(surface, (0, 0), special_flags=flag)

# TEST AREA FOR LIGHT BEAMS
#
# light1 = LightLine((500, 100), -math.pi/2, Blue, 1)
#
#
# refract = RefractArea((100, 300), (800, 100), (800, 500), 2)
#
# light1.extend([refract])
# light1.draw(light_surface)

prism = Prism((0, 0),  (10, 0), (5, 8.66))

print(prism.in_area((5, 3)))
print(prism.angles)
# refract.draw(light_surface)

# END TEST AREA

light_surface.set_alpha(160)

screen.blit(light_surface, (0, 0))

pygame.display.update()

print('done')

running = True

while running:

    # while drawing, reverse the list with reversed(objects)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
