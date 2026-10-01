# Great Scott Gadgets HackRF One

The HackRF One is a popular, open-source software-defined radio transceiver covering 1 MHz to 6 GHz with up to 20 MS/s bandwidth.

## Capabilities inside SDRmon

- **Frequency Range**: 1 MHz to 6 GHz
- **Bandwidth/Sample Rate**: 2 MS/s to 20 MS/s (Integer rates recommended)
- **ADC Resolution**: 8-bit
- **Receive Modes**: RX Supported
- **Transmit Modes**: TX Not Supported (SDRmon is receive-only)

## Hardware Considerations

### RF Safety

The HackRF One has a sensitive RF front end. The maximum RX input power is relatively low compared to some dedicated receivers. 
**Do not** overdrive the antenna input with high-power transmitters nearby. The SDRmon backend purposefully keeps the hardware front-end RF amplifier (AMP) disabled by default to minimize the risk of front-end damage.

### USB Connection

The HackRF requires a USB 2.0 High Speed connection. When operating at higher sample rates (e.g., 20 MS/s), ensure you are using a high-quality USB cable connected directly to your computer's root hub, avoiding unpowered external hubs that could drop packets or starve power.

### Clones

Because the HackRF One is open hardware, numerous clones (often with metal cases or added TXCOs) exist on the market. While SDRmon generally supports any device that works with standard `libhackrf`, device behavior, tuning stability, and RF performance may vary significantly depending on the manufacturer.
