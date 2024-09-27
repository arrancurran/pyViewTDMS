# Python Tools For Handling TDMS Files

This repository contains Python tools for handling TDMS (Technical Data Management Streaming) files. These tools allow you to read, process, and view TDMS files efficiently.

## Features

- Read TDMS files
- Extract data from TDMS files
- View TDMS data

## Installation

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## Usage

To view the contents of a TDMS file run,

```bash
python pyViewTDMS.py
```

Select the experimental XML file (needs to be in the same directory as the TDMS). All the necessary information to read the TDMS will be pulled from the XML.

Use the sliders to change time and piezo position. Zoom the image with mouse wheel/trackpad.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
