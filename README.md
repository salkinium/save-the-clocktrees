# How to cut down a Clock Tree

This is an experiment to understand the dependencies and interconnections in System Clock Trees at the example of the STM32F100 microcontroller.

Areas of interest include:

- automatic parsing and clock tree generation,
- perhaps a graphical viewer or editor,
- stating frequency requirements and resolving them (at compile time) (in Python, C++),
- compact description as XML for multiple device clock trees,
- scalability to other device clock trees (AVR, STM32).

The raw information is provided by ST's XML files (from microexplorer). Parsing is done using XQuery from lxml. Perhaps something usable will fall out of it.