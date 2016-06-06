# How to cut down a Clock Tree

This is an experiment to understand the dependencies and interconnections in System Clock Trees at the example of the STM32F100 microcontroller.

Areas of interest include:

- automatic parsing and clock tree generation,
- perhaps a graphical viewer or editor,
- stating frequency requirements and resolving them (at compile time) (in Python, C++),
- compact description as XML for multiple device clock trees,
- scalability to other device clock trees (AVR, STM32).

The raw information is provided by ST's XML files (from microexplorer). Parsing is done using XQuery from lxml. Perhaps something usable will fall out of it.


## Project state

Disclaimer: The code quality is "proof-of-concept". Especially the Python code is terrible and very hacked together.

A complete implementation of the STM32F100 clock tree exists, with generated sources, sinks and PLLs as well as compile time PLL value computation and validation.

The user facing API looks like this:
```cpp
// Choose a clock source.
// Note: The internal clock does not have a user provided frequency,
//       since its frequency is fixed!
//using pllSource = InternalClock;
using pllSource = ExternalCrystal<MHz8>;
// Choose the PLL output frequency.
// The pll values are automatically computed.
using pll = Pll< pllSource, 22000000 >;

// Choose clock input for system clock.
//using systemSource = InternalClock;
using systemSource = pll;
// Choose AHB prescalers, all resulting frequencies are automatically computed.
using systemClock = SystemClock< systemSource, AhbPrescaler::Div8 >;
// System clock configuration can be asserted at compile time.
static_assert(systemClock::Fcpu == 2750000,
	"CPU Frequency is not 22/8 MHz!");
static_assert(systemClock::Fcpu == pll::OutputFrequency / 8,
	"CPU Frequency is not 1/8 of PLL output frequency!");

// Choose the low speed clock source.
// using lsSource = LowSpeedInternalClock;
using lsSource = LowSpeedExternalCrystal;
// Choose clock input for RTC.
using rtcClock = RealTimeClock< lsSource >;
// Low speed clock configuration can also be asserted at compile time
static_assert(rtcClock::Rtc == 32768,
	"RTC frequency is not 32.768kHz!");

// Choose clock output source.
using clockOutput = ClockOutput< systemSource >;


int main()
{
	// Enable the clocks and PLL.
	systemClock::enable();
	// Initialize the SysTickTimer with the chosen AHB frequency.
	xpcc::cortex::SysTickTimer::initialize<systemClock>();

	// Enable the low speed clocks.
	rtcClock::enable();

	// Connect Pin A8 to the clock output for measurement.
	GpioOutputA8::connect(clockOutput::Id);
	// Enable clock output with the chosen source clock.
	clockOutput::enable();
	// ...
}
```

The code for this can be found in [this Pull Request](https://github.com/roboterclubaachen/xpcc/pull/39).

## Details

There currently are three classes that can be generated:
- clock sources,
- clock sinks, and
- simple PLLs (`Output = Input * Multiplier / Divisor`).

All classes conform to the following naming scheme of static member variables and methods:

```cpp
static const TypeId::TypeIdName Id;
static constexpr ClockName Name;
static constexpr uint32_t InputFrequency;
static constexpr uint32_t OutputFrequency;
static StartupError enable(const uint32_t waitCycles = 1500);
```

The `ClockName` is a substitute for a type system, which enforces the allowed clock inputs for any tree node at compile time using static asserts.
This makes it possible to check this without template specializations, and therefore make it possible to use the same class regardless of tree length without duplicate code.

`ClockControl` has the following naming scheme:
- `static bool enable{{SourceName}}Clock(uint32_t waitCycles);` for clock sources
- `static bool enable{{SinkName}}Clock({{SinkName}}ClockSource src, uint32_t waitCycles);` for clock sinks
- `static bool enablePll(PllSource source, ..., uint32_t waitCycles);`, different for every PLL

Typical usage of the SystemClock:
```cpp
using systemClock = SystemClock< Pll< ExternalCrystal<MHz8>, MHz24 > >;
StartupError error = systemClock::enable();
```

The following examples are from the STM32F100 clock tree, but similar properties can be found on other STM32 devices.

#### Sources
```xml
<!-- High speed clocks -->
<source name="InternalClock" type="clock" location="internal" speed="high" fixed="8000000"/>
<source name="ExternalClock" type="clock" location="external" speed="high" min="1000000" max="24000000"/>
<source name="ExternalCrystal" type="crystal" location="external" speed="high" min="4000000" max="24000000"/>
<!-- Low speed clocks -->
<source name="LowSpeedInternalClock" type="clock" location="internal" speed="low" fixed="40000"/>
<source name="LowSpeedExternalClock" type="clock" location="external" speed="low" min="1" max="1000000"/>
<source name="LowSpeedExternalCrystal" type="crystal" location="external" speed="low" fixed="32768"/>
```
Internal clocks (`InternalClock`) have a fixed output frequency.
External clocks (`ExternalCrystal<MHz8>`) can have a custom output frequency which is asserted by maximum and minimum frequencies.

#### Simple PLLs
```xml
<pll name="Pll" multiplier="2:16" max="24000000">
  <input name="InternalClock" divisor="2"/>
  <input name="ExternalClock" divisor="1:16" min="1000000"/>
  <input name="ExternalCrystal" divisor="1:16" min="1000000"/>
</pll>
```

The `PllSource` is automatically chosen and configured using the `ClockName Name` variable of the clock tree input.
The PLL class can at the moment only compute the divisor and multiplier settings at compile time given an input clock tree and an output frequency.
If no valid configuration is found, a failed assertion is raised.
Again, minimum and maximum frequencies on input and output paths are asserted.


#### Sinks
```xml
<sink name="RealTimeClock">
  <input name="ExternalClock" divisor="128"/>
  <input name="ExternalCrystal" divisor="128"/>
  <input name="LowSpeedExternalClock"/>
  <input name="LowSpeedExternalCrystal"/>
  <input name="LowSpeedInternalClock"/>
  <output name="Rtc"/>
</sink>
```

Sinks receive a valid input node and generate the appropriate output frequency.
`output` elements are aliased to `OutputFrequency` with the appropriate prescaler if necessary, especially when traversing the sink tree downwards to the output leaves.
```xml
<sink name="SystemClock" max="24000000">
  <input name="InternalClock"/>
  <input name="ExternalClock"/>
  <input name="ExternalCrystal"/>
  <input name="Pll"/>
  <tree name="Ahb" divisor="1,2,4,8,16,64,128,256,512" max="12000000">
    <output name="Hclk"/>
    <output name="SystemTimer"/>
    <output name="Fclk" alias="Fcpu"/>
    <!-- APB1 Prescaler -->
    <tree name="Apb1" divisor="1,2,4,8,16">
      <output name="Usart2"/>
      ...
      <output name="I2c2"/>
      <!-- if(APB1 prescaler == 1) x1 else x2 -->
      <tree name="Apb1Timer" depends="Apb1" multiplier="1,2,2,2,2">
        <output name="Timer2"/>
        ...
        <output name="Timer14"/>
      </tree>
    </tree>
    <!-- APB2 Prescaler -->
    <tree name="Apb2" divisor="1,2,4,8,16">
      <output name="Usart1"/>
      <output name="Spi1"/>
      <output name="Adc1"/>
      <!-- if(APB2 prescaler == 1) x1 else x2 -->
      <tree name="Apb2Timer" depends="Apb2" multiplier="1,2,2,2,2">
        <output name="Timer1"/>
        ...
        <output name="Timer17"/>
      </tree>
    </tree>
  </tree>
</sink>
```

## Unsolved issues

1. The data for this implementation is manually translated from the datasheet.
Ideally the clock graph data is generated from ST's XML data directly.
2. Since the computation has to happen at compile time, it has to be a C++11 `constexpr` function.
Currently only a simple PLL computation is implemented.
3. The user facing API for input and output connections is not terrible, but adding additional parameters like the AHB prescalers does not scale well.
4. The "Clock Tree" is actually a graph.

#### 1. Data generation

ST's raw data is not consistent. I guess, because it's "internal" data, it's ok to a degree, but it does make for some annoying parsing of the clock tree.
<!-- Furthermore ST is a French company and the XML comments and tags are named accordingly, by which I mean, half English, half French. Enjoy such gems as "devisor" and "diviseur de HSE pour RTC". -->

The `stm_clock_nx.py` is a hacked together parser for the F100 clock tree.
It pushes the graph into the NetworkX library and exports it into the dot language, which is visualized by graphviz (see [`graph.pdf`](graph.pdf))
