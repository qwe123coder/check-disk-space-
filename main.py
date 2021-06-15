import subprocess
import sys
import json
import pathlib
import re
import math
import operator

TMPL = "{:<30} {:<30} {:<10} {:>9}"


def humanize(size):
    "Convert size in bytes to human readable output."
    try:
        units = ['B', 'KB', 'MB', 'GB']
        i = math.floor(math.log(size) / math.log(1024))
        hsize = f"{round(size / 1024**i)}{units[i]}"
    except ValueError:
        hsize = '0B'
    return hsize


def topN(packages, n=10):
    "Display N biggest packages."
    get_size = operator.itemgetter('size')
    print(f"\nTOP {n}:")
    for i, pkg in enumerate(sorted(packages, key=get_size, reverse=True)[:n], 1):
        print(f"{i:>2}. {pkg['name']} ({humanize(pkg['size'])})")


# python -m pip list --format --json --verbose
pip_list = subprocess.run([sys.executable, "-m", "pip", "list",
                           "--format", "json", "--verbose"],
                          capture_output=True)

if pip_list.returncode == 0:
    # Headers
    print(TMPL.format("Package", "Version", "Installer", "Size"))
    print(TMPL.format("-"*30, "-"*30, "-"*10, "-"*9))

    packages = json.loads(pip_list.stdout)
    for pkg in packages:
        # python -m pip show --files <package>
        pip_show = subprocess.run([sys.executable, "-m", "pip", "show",
                                   "--files", f"{pkg['name']}"],
                                  capture_output=True)

        if pip_show.returncode == 0:
            # No json format...
            sre = re.search(r"\nFiles:\n(?P<files>(?:\s+.*\n)+)",
                            pip_show.stdout.decode('utf8'),
                            re.MULTILINE)
            size = 0
            if sre:
                location = pathlib.Path(pkg['location'])
                for f in sre['files'].split():
                    fullpath = location / f.strip()
                    size += fullpath.stat().st_size if fullpath.is_file() else 0
            pkg['size'] = size
            print(TMPL.format(pkg['name'], pkg['version'],
                              pkg['installer'], humanize(pkg['size'])))
