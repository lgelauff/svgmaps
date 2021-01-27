# An optimized version of covid_mapmaker.ipynb

import csv
import re
import urllib.request
import os
import pandas as pd
import numpy as np

# Download the csv files with the most recent data for COVID confirmed cases and deaths.

urllib.request.urlretrieve("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv", "data/time_series_covid19_confirmed_US.csv")
urllib.request.urlretrieve("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv", "data/time_series_covid19_deaths_US.csv")


# Collect the census data from the csv.
# "the United States" is a special 'state' that contains the entire country.

census = pd.read_csv('data/census.csv')
states = census.groupby('STATE').agg({'STNAME': 'first'})
states_df = pd.DataFrame(states)
state_names = [states_df.loc[state_id]["STNAME"] for state_id in list(states_df.index)] + ['the United States']


# Function to read the relevant data for states.
# Input: csv filepath, asof (list keeping track of the most recent dates)
# Output: fipses (list of FIPS codes), covid counts (dict with key FIPS and value most recent count),
#   covid_last14 (dict with key FIPS and value list of the last 14 covid-counts)

asof_list = []
def read_data(filename):
    fipses_by_state = {state: [] for state in state_names}
    covid_counts_by_state = {state: {} for state in state_names}
    covid_last14_by_state = {state: {} for state in state_names}

    with open(filename, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        fips_index = header.index("FIPS")
        state_index = header.index("Province_State")
        admin2_index = header.index("Admin2")

        date = header[-1]
        asof_list.append(date)
        print("As of " + date)

        state_name_set = set(state_names)

        for row in reader:
            state = row[state_index]
            if state not in state_name_set:
                continue

            admin2 = row[admin2_index]
            if re.findall(r"\AOut of [A-Z][A-Z]", admin2):
                continue
            if admin2 == "Unassigned":
                continue
            if state == "Massachusetts" and admin2 == "Dukes and Nantucket":
                fips = '25x01' #Dukes and Nantucket are two counties
            elif state == "Michigan" and admin2 == "Michigan Department of Corrections (MDOC)":
                fips = '26x01'
            elif state == "Michigan" and admin2 == "Federal Correctional Institution (FCI)":
                fips = '26x02'
            elif state == "Utah" and admin2 == "Bear River":
                fips = "49x01"
            elif state == "Utah" and admin2 == "Central Utah":
                fips = "49x02"
            elif state == "Utah" and admin2 == "Southeast Utah":
                fips = "49x03"
            elif state == "Utah" and admin2 == "Southwest Utah":
                fips = "49x04"
            elif state == "Utah" and admin2 == "TriCounty":
                fips = "49x05"
            elif state == "Utah" and admin2 == "Weber-Morgan":
                fips = "49x06"
            elif state == "Missouri" and admin2 == "Kansas City":
                fips = "29x01"
            else:
                fips = str(int(float(row[fips_index]))).zfill(5)

            covid_counts_by_state[state][fips] = int(row[-1])
            covid_last14_by_state[state][fips] = [int(day) for day in row[len(row)-14:len(row)]]
            fipses_by_state[state].append(fips)

            covid_counts_by_state["the United States"][fips] = int(row[-1])
            covid_last14_by_state["the United States"][fips] = [int(day) for day in row[len(row)-14:len(row)]]
            fipses_by_state["the United States"].append(fips)

    return fipses_by_state, covid_counts_by_state, covid_last14_by_state


# Read the population data for states
# Output: dict with key FIPS and value population for that geography

populations_by_state = {state: {} for state in state_names}
with open("data/census.csv", "r") as f:
    populations = {}
    reader = csv.reader(f)
    header = next(reader)
    state_index = header.index("STATE")
    state_stname = header.index("STNAME")
    county_index = header.index("COUNTY")
    # county_name_index = header.index("CTYNAME")
    population_index = header.index("POPESTIMATE2019")
    for row in reader:
        state = row[state_stname]
        county = int(row[county_index])
        if county == 0:
            continue
        population = int(row[population_index])
        fips = str(row[state_index]) + str(county).zfill(3)
        populations[fips] = population

        assert state != "the United States"

        populations_by_state[state][fips] = population
        populations_by_state["the United States"][fips] = population
        # if state_name == "Massachusetts":
        #     populations['25x01'] = populations['25007'] + populations['25019'] #combined Dukes and Nantucket



# mergefips keeps track of all districts that need to be treated as one, because of how the data is collected.

mergefips = [
    # Massachusetts
    {"state": "Massachusetts", "from": ["25x01", "25007", "25019"]}, # Dukes and Nantucket
    # New York
    {"state": "New York", "from": ["36005", "36081", "36047", "36061", "36085"]}, #New York City
    # Utah: https://ibis.health.utah.gov/ibisph-view/about/LocalHealth.html
    {"state": "Utah", "from": ["49x01", "49003", "49005", "49033"]}, # Bear River: Box Elder, Cache, Rich
    {"state": "Utah", "from": ["49x02", "49023", "49027", "49031", "49041", "49055", "49039"]}, # Central Utah: Juab, Millard, Piute, Sevier, Wayne, Sanpete
    {"state": "Utah", "from": ["49x03", "49007", "49015", "49019"]}, # Southeast Utah: Carbon, Emery, Grand
    {"state": "Utah", "from": ["49x04", "49017", "49021", "49025", "49053", "49001"]}, # Southwest Utah: Garfield, Iron, Kane, Washington, Beaver
    {"state": "Utah", "from": ["49x05", "49009", "49013", "49047"]}, # TriCounty: Daggett, Duchesne, Uintah
    {"state": "Utah", "from": ["49x06", "49057", "49029"]}, # Weber-Morgan
    {"state": "Missouri", "from": ["29x01", "29095", "29047", "29165", "29037"]} #Kansas City, Jackson, Clay, Platte, Cass
]


# Function to replace 'id="c[fips]"' in the SVG with 'id="c[fips]" fill="[color]"'.

def fill_map(svg, fips_colors):
    def replace(m):
        fips = m.group(1)
        color = fips_colors[fips]
        return 'id="c' + fips + '" fill="' + color + '"'
    return re.sub(r'id="c(.{5})"', replace, svg)


# Function to fill the map with the colors based on the most recent covid count.

def fillmap_prevalence(fipses, covid_counts, populations, svg,
            thresholds,
            colors,
            state):

    fips_colors = {}

    skipfips = set(['25007', '25019', '25x01', '26x01', '26x02'])
    for exception in mergefips:
        if state == 'the United States':
            pass
        elif exception["state"] != state:
            continue
        covid_count = 0
        population = 0
        for fips in exception["from"]:
            covid_count += covid_counts[fips]
            if fips in populations:
                population += populations[fips]
        percentage = covid_count * 100 / population
        color = getcolor(covid_count, percentage, thresholds, colors)
        for fips in exception["from"]:
            fips_colors[fips] = color
            skipfips.add(fips)

    for fips in fipses:
        if fips in skipfips: #messed up data, manual fix
            continue
        covid_count = covid_counts[fips]
        population = populations[fips]
        percentage = covid_count * 100 / population

        color = getcolor(covid_count, percentage, thresholds, colors)

        fips_colors[fips] = color
#         svg = re.sub(
#             r'<title id="title' + str(fips) + '">(.*?)</title>',
#             r'<title id="title' + str(fips) + r'">\1 County\nConfirmed infected: ' + format(covid_count, ",d") + '\nPopulation estimate: ' + format(population, ",d") + '\nPercentage infected: ' + format(percentage, ".2f") + '%</title>',
#             svg
#         )

    return fill_map(svg, fips_colors)

# Function to fill the map with the covid count increase over the past 14 days

def fillmap_roll14_prevalence(fipses, covid_counts14, populations, svg,
            thresholds,
            #colors = ["#CCCCCC", "#DDB1C3", "#BB70AE", "#853D9A", "#3B1878", "#000357"],
            # These colors come from https://colorbrewer2.org/#type=sequential&scheme=BuPu&n=6
            # With an extra darker color added later from https://colorbrewer2.org/#type=sequential&scheme=BuPu&n=9
            # And black.
            colors,
            state):

    fips_colors = {}

    skipfips = set(['25007', '25019', '25x01', '26x01', '26x02'])
    for exception in mergefips:
        if state == 'the United States':
            pass
        elif exception["state"] != state:
            continue
        covid_count = [0] * 14
        population = 0
        for fips in exception["from"]:
            covid_count = list(np.add(covid_count, covid_counts14[fips]))
            if fips in populations:
                population += populations[fips]
        countdiff = (covid_count[-1] - covid_count[0])
        percentage = countdiff * 100 / population
        color = getcolor(countdiff, percentage, thresholds, colors)
        for fips in exception["from"]:
            fips_colors[fips] = color
            skipfips.add(fips)

    for fips in fipses:
        if fips in skipfips: #messed up data, manual fix
            continue
        covid_count = covid_counts14[fips]
        countdiff = (covid_count[-1] - covid_count[0])
        population = populations[fips]
        percentage = countdiff * 100 / population

        color = getcolor(countdiff, percentage, thresholds, colors)

        fips_colors[fips] = color
#         svg = re.sub(
#             r'<title id="title' + str(fips) + '">(.*?)</title>',
#             r'<title id="title' + str(fips) + r'">\1 County\nConfirmed infected: ' + format(covid_count, ",d") + '\nPopulation estimate: ' + format(population, ",d") + '\nPercentage infected: ' + format(percentage, ".2f") + '%</title>',
#             svg
#         )

    return fill_map(svg, fips_colors)

# Function to determine the color based on thresholds and a value

def getcolor(covid_count, percentage, thresholds, colors):
    if covid_count <= thresholds[0]:
        return colors[0]
    for level in range(1, len(thresholds)):
        if percentage < thresholds[level]:
            return colors[level]
    return colors[-1]


# Function to read a blank map.
# Input: file path to the map
# Output: the svg as string

def readblankmap(filename):
    with open(filename, "r") as f:
        svg = f.read()
    return svg

# Function to write the svg

def writesvg(svg, filename):
    with open(filename, "w") as f:
        f.write(svg)
    print("written: " + filename)


fipses_by_state, covid_counts_by_state, covid_counts14_by_state = read_data(filename="data/time_series_covid19_confirmed_US.csv")
fipses_deaths_by_state, covid_counts_deaths_by_state, covid_counts14_deaths_by_state = read_data(filename="data/time_series_covid19_deaths_US.csv")

# Loop over the states and create their map.
for st_name in state_names:
    print("getting data:", st_name)

    populations_state = populations_by_state[st_name]

    if st_name == 'the United States':
        svg_state = readblankmap("Usa_counties_large_whitelines.svg")
    else:
        svg_state = readblankmap("output_states_svg_albers/Blank map subdivisions 2019 Albers " + st_name + ".svg")

    svg_filled_state = fillmap_prevalence(
        fipses = fipses_by_state[st_name],
        covid_counts = covid_counts_by_state[st_name],
        populations = populations_state,
        thresholds = (0, 0.03, 0.10, 0.30, 1.00, 3.00, 10.00),
        colors = ("#CCCCCC", "#fee5d9", "#fcbba1", "#fc9272", "#fb6a4a", "#cb181d", "#99000d", "#510000"),
        svg = svg_state,
        state = st_name
    )
    writesvg(svg_filled_state, "output/COVID-19_Prevalence_in_" + st_name + "_by_county.svg")

    svg_filled_roll14_state = fillmap_roll14_prevalence(
        fipses = fipses_by_state[st_name],
        covid_counts14 = covid_counts14_by_state[st_name],
        populations = populations_state,
        thresholds = (0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.00),
        colors = ("#CCCCCC", "#f7fcfd", "#e0ecf4", "#9ebcda", "#8c96c6", "#8c6bb1", "#88419d", "#6e016b", "#000000"),
        svg = svg_state,
        state = st_name
    )
    writesvg(svg_filled_roll14_state, "output/COVID-19_rolling_14day_Prevalence_in_" + st_name + "_by_county.svg")

    if st_name in ('Nebraska', 'New Hampshire', 'Rhode Island', 'Wyoming', 'the United States'):
        continue # too many unassigned cases
    svg_filled_deaths_state = fillmap_prevalence(
        fipses = fipses_deaths_by_state[st_name],
        covid_counts = covid_counts_deaths_by_state[st_name],
        populations = populations_state,
        svg = svg_state,
        state = st_name,
        thresholds = (0, 0.002, 0.010, 0.050, 0.100),
        colors = ("#CCCCCC", "#fdd49e", "#fdbb84", "#fc8d59", "#e34a33", "#b30000")
    )
    writesvg(svg_filled_deaths_state, "output/COVID-19_Deaths_Prevalence_in_" + st_name + "_by_county.svg")

    # Disabled for now: the data is too messy. Too many deaths were unassigned to a county.
    # svg_filled_roll14_deaths_state = fillmap_roll14_prevalence(
    #     fipses = fipses_deaths_by_state[st_name],
    #     covid_counts14 = covid_counts14_deaths_by_state[st_name],
    #     populations = populations_state,
    #     svg = svg_state,
    #     state = st_name,
    #     thresholds = (0, 0.001, 0.002, 0.005, 0.010),
    #     colors = ("#CCCCCC", "#c7e9b4", "#7fcdbb", "#41b6c4", "#2c7fb8", "#253494")
    # )
    # writesvg(svg_filled_roll14_deaths_state, "output/COVID-19_rolling_14day_Deaths_Prevalence_in_" + st_name + "_by_county.svg")


# test if all dates are identical (to cover edge case where one file is updated, and another not yet)
assert len(set(asof_list)) == 1
