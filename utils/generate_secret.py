#!/usr/bin/env python

import random

charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+{}[]|<>?"
output = ""
r = random.Random()
for i in range(48):
	output += charset[r.randint(0, len(charset)-1)]
print output
