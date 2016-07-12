import sys
import os
from drlutils.dublincore.mods2dc import transform

transform(sys.argv[1], sys.argv[2])
