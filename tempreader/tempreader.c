#include <stdint.h>

// Define memory addresses as constants
#define PERIPH_BASE 0x40000000UL
#define AHB1_BASE   (PERIPH_BASE + 0x00020000UL)
#define APB1_BASE   (PERIPH_BASE + 0x00000000UL)
#define APB2_BASE   (PERIPH_BASE + 0x00010000UL)

#define RCC_BASE    (AHB1_BASE + 0x3800UL)
#define GPIOA_BASE  (AHB1_BASE + 0x0000UL)
#define TIM1_BASE   (APB2_BASE + 0x0000UL)
#define USART2_BASE (APB1_BASE + 0x4400UL)

#define RCC_AHB1ENR  (*((volatile uint32_t *)(RCC_BASE + 0x30)))
#define RCC_APB1ENR  (*((volatile uint32_t *)(RCC_BASE + 0x40)))
#define RCC_APB2ENR  (*((volatile uint32_t *)(RCC_BASE + 0x44)))

#define GPIOA_MODER  (*((volatile uint32_t *)(GPIOA_BASE + 0x00)))
#define GPIOA_OTYPER (*((volatile uint32_t *)(GPIOA_BASE + 0x04)))
#define GPIOA_PUPDR  (*((volatile uint32_t *)(GPIOA_BASE + 0x0C)))
#define GPIOA_IDR    (*((volatile uint32_t *)(GPIOA_BASE + 0x10)))
#define GPIOA_ODR    (*((volatile uint32_t *)(GPIOA_BASE + 0x14)))
#define GPIOA_AFRL   (*((volatile uint32_t *)(GPIOA_BASE + 0x20)))

#define TIM1_CR1     (*((volatile uint32_t *)(TIM1_BASE + 0x00)))
#define TIM1_CNT     (*((volatile uint32_t *)(TIM1_BASE + 0x24)))
#define TIM1_PSC     (*((volatile uint32_t *)(TIM1_BASE + 0x28)))
#define TIM1_ARR     (*((volatile uint32_t *)(TIM1_BASE + 0x2C)))

#define USART2_SR    (*((volatile uint32_t *)(USART2_BASE + 0x00)))
#define USART2_DR    (*((volatile uint32_t *)(USART2_BASE + 0x04)))
#define USART2_BRR   (*((volatile uint32_t *)(USART2_BASE + 0x08)))
#define USART2_CR1   (*((volatile uint32_t *)(USART2_BASE + 0x0C)))

// Define DHT PIN as 1 (PA1)
#define DHT_PIN 1

void SystemInit(void) {}

// Delays a given amount of microseconds.
// Runs an empty loop for `us` microseconds, creating this delay.
void delay_us(uint16_t us) {
    TIM1_CNT = 0;
    while (TIM1_CNT < us);
}

// Delays a given amount of milliseconds.
// Runs delay_us `1000 x ms` times, creating this delay.
void delay_ms(uint32_t ms) {
    for(uint32_t i = 0; i < ms; i++) delay_us(1000);
}

// Sends a character to the data register
// Listens for the status register to be empty, (USART2_SR == 1)
// then sends the character (as an 8bit integer)
void uart_char(char c) {
    while(!(USART2_SR & (1 << 7)));
    USART2_DR = (uint8_t)c;
}

// Sends a string to the data register
// Runs uart_char, character by character.
// C strings end in a null character, automatically ending the loop.
void uart_str(const char *s) {
    while (*s) uart_char(*s++);
}

// Streams an integer.
// It does so one digit at a time (as chars with uart_char) -
// because we're dealing with 8bit integers (0-255)
// it accounts for integers up to 3 digits.
void uart_int(uint8_t val) {
    if (val == 0) {
        uart_char('0');
        return;
    }
    if (val >= 100) {
        uart_char('0' + (val / 100));
        val %= 100;
        uart_char('0' + (val / 10));
        val %= 10;
    } else if (val >= 10) {
        uart_char('0' + (val / 10));
        val %= 10;
    }
    uart_char('0' + val);
}

// Sets mode register / output type register for output.
// The current contents of MODER (mode register) for PA1
// Are ANDed with NOT 0x3 (00 in binary).
// They are then ORed with 0x1 (01 in binary).
// This sets them to 01.
// For the mode register, 01 represents output mode.
// OType (output type) register is ANDed with NOT 1.
// This marks push-pull mode.
void dht_set_output(void) {
    GPIOA_MODER &= ~(0x3 << (DHT_PIN * 2));
    GPIOA_MODER |= (0x1 << (DHT_PIN * 2));
    GPIOA_OTYPER &= ~(1 << DHT_PIN);
}

// Sets mode register / pull up - pull down register for input.
// The current contents of MODER (mode register) for PA1
// Are ANDed with NOT 0x3 (00 in binary).
// This sets them to 00.
// For the mode register, 00 represents input mode.
// PUPDR (Pull-up pull-down register) is ANDed with NOT 0x3 (00),
// setting it to 00.
void dht_set_input(void) {
    GPIOA_MODER &= ~(0x3 << (DHT_PIN * 2));
    GPIOA_PUPDR &= ~(0x3 << (DHT_PIN * 2));
}

int main(void) {
    // Enable Peripheral Clocks
	// This sets the enable bits on the relevant clocks
    RCC_AHB1ENR |= (1 << 0);
    RCC_APB1ENR |= (1 << 17);
    RCC_APB2ENR |= (1 << 0);

    // Wait - ensures clocks are stabilized\
    // Volatile integer so the compiler doesn't optimize this loop away
    for (volatile int i = 0; i < 5000; i++);

    // Configure PA5 Built-In Green LED
    // Sets the mode register for the Green LED to 01
    // As mentioned before, 01 means output.
    GPIOA_MODER &= ~(0x3 << (5 * 2));
    GPIOA_MODER |= (0x1 << (5 * 2));

    // Configure TIM1 for standard 2-second interval pacing

    // Resets the control register - stops timer before configuring
    TIM1_CR1 = 0;
    // Sets counter to 0.
    TIM1_CNT = 0;
    // Prescaler - this divides the rate at which the clock ticks.
    // It would normally run at 16MHz - 16 / (15 + 1) = 1
    // So it now runs at 1MHz. (1 tick per microsecond)
    TIM1_PSC = 15;
    // Auto-reload register is set to the max value -
    // prevents it from looping
    TIM1_ARR = 0xFFFF;
    // Now that all of these operations are finished, set control register to 1 (enable)
    TIM1_CR1 |= (1 << 0);

    // Configure PA2 as USART2_TX (9600 Baud)
    // Sets mode register to alternate mode (10)
    // Alternate mode - removes standard i/o function,
    // has the device control a peripheral
    GPIOA_MODER &= ~(0x3 << 4);
    GPIOA_MODER |= (0x2 << 4);
    // Sets alternate function register to (0111)
    // This selects USART2 as the targeted peripheral.
    GPIOA_AFRL &= ~(0xF << 8);
    GPIOA_AFRL |= (0x7 << 8);
    // Sets the baud (bits per second) rate for USART2
    // This results in 9600 baud.
    USART2_BRR = (104 << 4) | 3;
    // Sets USART enable and Transmit enable signals to 1.
    // Allows USART and data transmit.
    USART2_CR1 |= (1 << 13) | (1 << 3);

    // Initializes a 5 byte payload.
    uint8_t bytes[5];

    while(1) {
        // Toggle the Green LED
    	// Acts as a visual indicator that everything is powered on/running
    	// Toggles bit 5 of the output data register (green LED)
        GPIOA_ODR ^= (1 << 5);

        // This is how we tell the DHT that we are ready to receive data!

        // Sets it to output mode (We are outputting to DHT)
        dht_set_output();
        // Sets output data register to 0 -
        // This sets voltage to 0
        GPIOA_ODR &= ~(1 << DHT_PIN);
        // Hold voltage at 0 for 20 ms
        // this is how the DHT "knows" it is being queried
        delay_ms(20);
        // Set output data register to 1 -
        // Sends voltage to the register
        // Initial pulse is over, DHT response can be read
        GPIOA_ODR |= (1 << DHT_PIN);
        // Brief delay
        delay_us(30);
        // Set DHT to input mode (We are inputting from DHT)
        dht_set_input();

        // Waits for the DHT to return this handshake
        // This is how the DHT lets us know it's ready to send over input!

        // Safety exists to time out any of the given operations... in case of failure.
        uint32_t safety = 0;

        // First we wait for the DHT to pull the line low... first signal.
        while (((GPIOA_IDR >> DHT_PIN) & 1) && ++safety < 10000);

        // Then we wait for the DHT to pull the line high... ends first signal.
        safety = 0;
        while (!((GPIOA_IDR >> DHT_PIN) & 1) && ++safety < 10000);

        // Then we wait for the DHT to pull the line low again... second and final signal.
        safety = 0;
        while (((GPIOA_IDR >> DHT_PIN) & 1) && ++safety < 10000);

        // Data (40 bits / 5 bytes) is streaming from the DHT, capture it

        // Failure flag for safety.
        uint8_t failed = 0;

        // Initialize 5 bytes to 0
        bytes[0] = bytes[1] = bytes[2] = bytes[3] = bytes[4] = 0;
        // Byte 0: Humidity, integer portion
        // Byte 1: Humidity, decimal portion
        // Byte 2: Temperature, integer portion
        // Byte 3: Temperature, decimal portion
        // Byte 4: Checksum!

        // Stream all 40 bits from the DHT:
        for (int i = 0; i < 40; i++) {
        	// Re-establishes safety mechanism
            safety = 0;
            // Waits for the DHT to flash a signal, sends failure if it times out
            while (!((GPIOA_IDR >> DHT_PIN) & 1) && ++safety < 10000);
            if (safety >= 10000) { failed = 1; break; }

            // Waits for the DHT to go back low, tracks how long it was high
            uint32_t high_cycles = 0;
            while (((GPIOA_IDR >> DHT_PIN) & 1) && ++high_cycles < 10000);
            if (high_cycles >= 10000) { failed = 1; break; }

            // Tracks byte index in groups of 8 using integer division.
            uint8_t bit_idx = i / 8;
            // Shift to the next bit
            bytes[bit_idx] <<= 1;

            // If it was high for more than 25 cycles, it indicates the specific bit
            // was meant to be a 1. Otherwise, remains 0.
            if (high_cycles > 25) {
                bytes[bit_idx] |= 1;
            }
        }

        // Validate output
        // First, checks for failure
        // Byte 4 is a checksum - it is sent as the sum of 0-3 to check
        // whether the data is correct.
        if (!failed && (bytes[4] == ((bytes[0] + bytes[1] + bytes[2] + bytes[3]) & 0xFF))) {

        	// Now the data is validated so we can assemble it as intended to be read by Python.

            // --- TEMPERATURE SERIAL ASSEMBLY ---

        	// Begin assembling temperature as a JSON output
            uart_str("{\"t\":");
            // Byte 2 represents the integer portion of temperature.
            uart_int(bytes[2]);
            uart_char('.');

            // Account for the decimal portion of temperature:
            uint8_t t_dec = bytes[3];
            if (t_dec < 10) {
                // Keep it clean if it's a raw single digit fraction
                uart_int(t_dec);
            } else {
                // If it passes an integer byte value over 10 (e.g. 23.65), process both digits
                uart_int(t_dec / 10);
                uart_int(t_dec % 10);
            }

            // --- HUMIDITY SERIAL ASSEMBLY ---

            // Begin assembling humidity as a JSON output
            uart_str(",\"h\":");
            // Byte 0 is the integer portion of humidity
            uart_int(bytes[0]);
            uart_char('.');

            // Handle the decimal portion of humidity:
            uint8_t h_dec = bytes[1];
            if (h_dec < 10) {
            	// If one digit, account for the one decimal place.
                uart_int(h_dec);
            } else {
            	// If two digits, account for both:
                uart_int(h_dec / 10);
                uart_int(h_dec % 10);
            }

            // Maintain dummy fields for dew point and heat index...
            // Python worker expects these fields but now handles them on its end.
            uart_str(",\"dp\":0.0,\"hi\":0.0}\r\n");

        } else {
        	// If any failure occurred (failed checksum / timeout) display failure
            uart_str("{\"error\":true}\r\n");
        }

        // Polls DHT every 2 seconds.

        delay_ms(2000);
    }
}
