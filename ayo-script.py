import os

from ayo import tof
from rich.console import Console

console = Console()

yn = console.input(
    "Install [blue]required packages?[/blue] \\[Yn] "
)

if not tof(yn):
    exit(1)

with console.status("Collecting..."), \
    open(
        "requirements.preview.txt", 
        "r", 
        encoding="utf-8"
    ) as f:
        contents = " ".join(f.read().splitlines())
        os.system(f"pip install {contents} -q -q") # 2 qs for ultra quiet
