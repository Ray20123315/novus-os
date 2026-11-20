import re, sys
path = sys.argv[1] if len(sys.argv) > 1 else "out/smoke.log"
pat = re.compile(r"FONT|M3|panic|assert|NOVUS OS|DEVTAB|font|novusfs|stat|error|fail|dbg", re.I)
ansi_sgr = re.compile(r"\x1b\[[0-9;]*m")
with open(path) as f:
    for i, line in enumerate(f):
        if pat.search(ansi_sgr.sub("", line)):
            print(i, repr(line.rstrip("\n")))
