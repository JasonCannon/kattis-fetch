# Kattis Fetch
A Python 3 script to automatically download a user's Kattis statistics and solved problems.

## Installation
You can use `git clone https://github.com/JasonCannon/kattis-fetch` to clone the repository. Make sure you have installed the Python 3 package Beautiful Soup, see **Requirements** below for installation instructions.

## Kattis configuration file
Before running the fetcher, you need to [download a configuration file](https://open.kattis.com/download/kattisrc). This file includes a secret personal token that allows you to log in. It should be placed in your home directory, or in the same directory as `fetch.py`, and be called `.kattisrc`.

## Usage
To run the fetcher, first make sure you have downloaded your Kattis configuration file. You can then `cd` into the `kattis-fetch` directory and run `python3 fetch.py <kattis_email>`. The script make take some time to run and will the write the results to a json file called `kattis.json` in the same directory. **Do not spam or overuse this script as it requires live fetching from the Kattis servers.**

### Preview
This script will produce a file called `kattis.json` in the same directory. The layout of the file will look like:
```json5
{
    "stats": {
        "Rank": "<Kattis rank>",
        "Score": "<Kattis score>",
        "Solved": "<number of problems solved>"
    },
    "solved": [
        {
            "ID": "sequences",
            "Name": "0-1 Sequences",
            "Total": "1488",
            "Acc.": "739",
            "Ratio": "50%",
            "Fastest": "0.00",
            "Difficulty": "7.0"
        },
        // ... and so on ...
```

## Requirements
This Python script requires the library [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) to be able to fetch the data. The easiest way to install this library would be to use a library / package manager (e.g. `pip3 install beautifulsoup4` or `apt-get install python3-bs4`).

## TODOs
- Improve the script overall _(it's currently just hacked together)_.
- Add the ability to download all source files (e.g. all .cpp, .py files) for a user's solved Kattis problems _(could put some strain on the Kattis servers so I would have to thoroughly test this out first to avoid any potential issues)_.
