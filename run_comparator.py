#!/usr/bin/env python3

from comparator import *

comparator = Comparator("./input/", "./output/", 0.7, raise_on_critical_error=False)
comparator.use_two_circle_intersection_ratio = False
comparator.run()
comparator.print(sys.stdout, True)

