# Bus Tech Accessibility Kiosk

Accessibility transport kiosk prototype for a 7-inch LCD interface and physical bus-selection clickers.

## Current project goal

Build the kiosk in small, testable stages. The LCD is the visual interface; users select bus services using physical tactile/Braille-labelled clickers.

### Planned interaction

1. User taps an NFC card.
2. Raspberry Pi identifies the user profile.
3. LCD displays available bus services.
4. User presses a physical bus clicker once.
5. LCD asks for confirmation of that bus.
6. Pressing the same bus clicker again confirms it.
7. Pressing a different bus clicker changes the selection and asks for confirmation again.
8. After confirmation, the LCD displays bus arrival details and the system can provide assistance/audio feedback.

## Development stages

- [x] Repository and project structure
- [x] Initial LCD UI scaffold
- [x] Bus selection/confirmation state-machine scaffold
- [ ] Test on Raspberry Pi + 7-inch LCD
- [ ] Connect physical bus clickers through GPIO
- [ ] Add SQLite user database
- [ ] Add PN532 NFC reader
- [ ] Add audio output
- [ ] Add real bus arrival data/simulation
- [ ] Add Arduino communication if required

## Project structure

```text
bus-tech-accessibility-kiosk/
├── kiosk/
│   ├── main.py
│   ├── display.py
│   ├── buttons.py
│   └── kiosk_logic.py
├── database/
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

## Important design decision

The 7-inch LCD is an **output/display interface**, not the primary user input. Bus selection is performed using physical tactile/Braille-labelled clickers.
