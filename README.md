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

	// Connect Pin A8 to the clock output for measurement.
	GpioOutputA8::connect(clockOutput::Id);
	// Enable clock output with the chosen source clock.
	clockOutput::enable();
	// ...
}
```
