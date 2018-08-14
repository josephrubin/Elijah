@echo off

set PYTHONOPTIMIZE=2

pyinstaller gui.py -F --name Elijah.exe --hidden-import pandas._libs.tslibs.np_datetime --hidden-import pandas._libs.tslibs.nattype --hidden-import pandas._libs.skiplist --hidden-import matplotlib.backends.backend_tkagg --noconsole --icon=../image/icon.ico

echo.

pause

@echo on