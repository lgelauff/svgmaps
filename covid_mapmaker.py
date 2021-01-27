import csv
import re
import urllib.request
import os
import pandas as pd
import numpy as np

# Download the csv files with the most recent data for COVID confirmed cases and deaths.

urllib.request.urlretrieve("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv", "data/time_series_covid19_confirmed_US.csv")
urllib.request.urlretrieve("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv", "data/time_series_covid19_deaths_US.csv")

# Function to read the relevant data for a state.
# Input: state name and csv filepath, asof (list keeping track of the most recent dates)
# Output: fipses (list of FIPS codes), covid counts (dict with key FIPS and value most recent count),
#   covid_last14 (dict with key FIPS and value list of the last 14 covid-counts)
#   full_df (pandas DF with FIPS and all rows for that state)
#   asof_list

asof_list = []
def readstate(select_state, filename, asof = asof_list):
    fipses = []
    covid_counts = {}
    covid_last14 = {}
    with open(filename, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        fips_index = header.index("FIPS")
        state_index = header.index("Province_State")
        admin2_index = header.index("Admin2")
        iso2_index = header.index("iso2")
        bannedstates = ["Diamond Princess", "Grand Princess"]

        date = header[-1]
        asof += [date]
        print("As of " + date)
        all_rows = []

        for row in reader:
            state = row[state_index]
            if select_state == 'the United States': #make map of the whole US
                if state in bannedstates:
                    continue
                elif row[iso2_index] == "US":
                    pass
                else:
                    continue #Puerto Rico, Virgin Islands etc. : Not in census data
            elif state != select_state:
                continue
            admin2 = row[admin2_index]
            if re.findall(r"\AOut of [A-Z][A-Z]", admin2):
                continue
            if admin2 == "Unassigned":
                continue
            if row[state_index] == "Massachusetts" and admin2 == "Dukes and Nantucket":
                fips = '25x01' #Dukes and Nantucket are two counties
            elif row[state_index] == "Michigan" and admin2 == "Michigan Department of Corrections (MDOC)":
                fips = '26x01'
            elif row[state_index] == "Michigan" and admin2 == "Federal Correctional Institution (FCI)":
                fips = '26x02'
            elif row[state_index] == "Utah" and admin2 == "Bear River":
                fips = "49x01"
            elif row[state_index] == "Utah" and admin2 == "Central Utah":
                fips = "49x02"
            elif row[state_index] == "Utah" and admin2 == "Southeast Utah":
                fips = "49x03"
            elif row[state_index] == "Utah" and admin2 == "Southwest Utah":
                fips = "49x04"
            elif row[state_index] == "Utah" and admin2 == "TriCounty":
                fips = "49x05"
            elif row[state_index] == "Utah" and admin2 == "Weber-Morgan":
                fips = "49x06"
            elif row[state_index] == "Missouri" and admin2 == "Kansas City":
                fips = "29x01"
            else:
                fips = str(int(float(row[fips_index]))).zfill(5)
            covid_counts[fips] = int(float(row[-1]))
            covid_last14[fips] = [int(float(day)) for day in row[len(row)-14:len(row)]]
            fipses.append(fips)
            all_rows.append([fips] + row)
        full_df = pd.DataFrame(all_rows, columns=["cleanfips"] + header)
    return (fipses, covid_counts, covid_last14, full_df, asof_list)

# Function to read the population data for a state
# Input: state name
# Output: dict with key FIPS and value population for that geography

def readpop(state_name):
    with open("data/census.csv", "r") as f:
        populations = {}
        reader = csv.reader(f)
        header = next(reader)
        state_index = header.index("STATE")
        state_stname = header.index("STNAME")
        county_index = header.index("COUNTY")
        # county_name_index = header.index("CTYNAME")
        population_index =  header.index("POPESTIMATE2019")
        for row in reader:
            state = row[state_stname]
            if state_name == "the United States":
                pass
            elif state != state_name:  # Select only the relevant state
                continue
            county = int(row[county_index])
            if county == 0:
                continue
            population = int(row[population_index])
#             print(state, county, str(county).zfill(3))
            fips = str(row[state_index]) + str(county).zfill(3)
#             print(fips)
            populations[fips] = population
#         if state_name == "Massachusetts":
#             populations['25x01'] = populations['25007'] + populations['25019'] #combined Dukes and Nantucket
    return populations


# Function to read a blank map.
# Input: file path to the map
# Output: the svg as string

def readblankmap(filename):
    with open(filename, "r") as f:
        svg = f.read()
    return svg

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

# Function to fill the map with the colors based on the most recent covid count.

def fillmap_prevalence(fipses, covid_counts, populations, svg,
            thresholds = [0, 0.03, 0.10, 0.30, 1.00, 3.00],
            # colors = ["#CCCCCC", "#FFC0C0", "#EE7070", "#C80200", "#900000", "#510000"],
            colors = ["#CCCCCC", "#fee5d9", "#fcbba1", "#fc9272", "#fb6a4a", "#cb181d", "#99000d"],
            state = "California"):

    skipfips = ['25007', '25019', '25x01', '26x01', '26x02']
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
            svg = svg.replace(
            'id="c' + str(fips),
            'id="c' + str(fips) + '" fill="' + color
            )
            skipfips.append(fips)

    for fips in fipses:
#         print(fips)
        if fips in skipfips: #messed up data, manual fix
            continue
        covid_count = covid_counts[fips]
        population = populations[fips]
        percentage = covid_count * 100 / population

        color = getcolor(covid_count, percentage, thresholds, colors)

        svg = svg.replace(
            'id="c' + str(fips),
            'id="c' + str(fips) + '" fill="' + color
        )
#         svg = re.sub(
#             r'<title id="title' + str(fips) + '">(.*?)</title>',
#             r'<title id="title' + str(fips) + r'">\1 County\nConfirmed infected: ' + format(covid_count, ",d") + '\nPopulation estimate: ' + format(population, ",d") + '\nPercentage infected: ' + format(percentage, ".2f") + '%</title>',
#             svg
#         )

    return svg

# Function to fill the map with the covid count increase over the past 14 days

def fillmap_roll14_prevalence(fipses, covid_counts14, populations, svg,
            thresholds = [0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50],
            #colors = ["#CCCCCC", "#DDB1C3", "#BB70AE", "#853D9A", "#3B1878", "#000357"],
            # These colors come from https://colorbrewer2.org/#type=sequential&scheme=BuPu&n=6
            # With an extra darker color added later from https://colorbrewer2.org/#type=sequential&scheme=BuPu&n=9
            # And black.
            colors = ["#CCCCCC", "#bfd3e6", "#9ebcda", "#8c96c6", "#8856a7", "#810f7c", "#4d004b", "#000000"],
            state = "California"):

    skipfips = ['25007', '25019', '25x01', '26x01', '26x02']
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
#             print(state, fips, covid_count)
        countdiff = (covid_count[-1] - covid_count[0])
        percentage = countdiff * 100 / population
        color = getcolor(countdiff, percentage, thresholds, colors)
        for fips in exception["from"]:
            svg = svg.replace(
            'id="c' + str(fips),
            'id="c' + str(fips) + '" fill="' + color
            )
            skipfips.append(fips)

    for fips in fipses:
        if fips in skipfips: #messed up data, manual fix
            continue
        covid_count = covid_counts14[fips]
        countdiff = (covid_count[-1] - covid_count[0])
        population = populations[fips]
        percentage = countdiff * 100 / population

        color = getcolor(countdiff, percentage, thresholds, colors)

        svg = svg.replace(
            'id="c' + str(fips),
            'id="c' + str(fips) + '" fill="' + color
        )
#         svg = re.sub(
#             r'<title id="title' + str(fips) + '">(.*?)</title>',
#             r'<title id="title' + str(fips) + r'">\1 County\nConfirmed infected: ' + format(covid_count, ",d") + '\nPopulation estimate: ' + format(population, ",d") + '\nPercentage infected: ' + format(percentage, ".2f") + '%</title>',
#             svg
#         )

    return svg

# Function to determine the color based on thresholds and a value

def getcolor (covid_count, percentage, thresholds, colors):
    color = colors[-1]
    if covid_count <= thresholds[0]:
        color = colors[0]
    else:
#         print(np.arange(1, len(thresholds)), thresholds, colors)
        for level in np.arange(1, len(thresholds)):
#             print(level)
            if percentage < thresholds[level]:
                color = colors[level]
                break
#     if covid_count <= thresholds[0]:
#         color = colors[0]
#     elif percentage < thresholds[1]:
#         color = colors[1]
#     elif percentage < thresholds[2]:
#         color = colors[2]
#     elif percentage < thresholds[3]:
#         color = colors[3]
#     elif percentage < thresholds[4]:
#         color = colors[4]
#     else:
#         color = colors[5]
    return color


# Function to write the svg

def writesvg(svg, filename):
    with open(filename, "w") as f:
        f.write(svg)
    print("written: " + filename)


# Collect the census data from the csv, then loop over the states and create their map.
# "the United States" is a special 'state' that contains the entire country.

census = pd.read_csv('data/census.csv')
states = census.groupby('STATE').agg({'STNAME': 'first'})
states_df = pd.DataFrame(states)
asof_list = []
state_names = [states_df.loc[state_id]["STNAME"] for state_id in list(states_df.index)] + ['the United States']

for st_name in state_names:
    print("getting data: ", st_name)
    fipses_state, covid_counts_state, covid_counts14_state, covid_counts_df, asof_list = readstate(st_name, filename="data/time_series_covid19_confirmed_US.csv", asof = asof_list)
    fipses_deaths_state, covid_counts_deaths_state, covid_counts14_deaths_state, covid_deaths_df, asof_list = readstate(st_name, filename="data/time_series_covid19_deaths_US.csv", asof = asof_list)
    populations_state = readpop(st_name)
    if st_name == 'the United States':
        svg_state = readblankmap("Usa_counties_large_whitelines.svg")
    else:
        svg_state = readblankmap("output_states_svg_albers/Blank map subdivisions 2019 Albers " + st_name + ".svg")

    svg_filled_state = fillmap_prevalence(
        fipses = fipses_state,
        covid_counts = covid_counts_state,
        populations = populations_state,
        thresholds = [0, 0.03, 0.10, 0.30, 1.00, 3.00, 10.00],
        colors = ["#CCCCCC", "#fee5d9", "#fcbba1", "#fc9272", "#fb6a4a", "#cb181d", "#99000d", "#510000"],
        svg = svg_state,
        state = st_name
    )
    writesvg(svg_filled_state, "output/COVID-19_Prevalence_in_" + st_name + "_by_county.svg")

    svg_filled_roll14_state = fillmap_roll14_prevalence(
        fipses = fipses_state,
        covid_counts14 = covid_counts14_state,
        populations = populations_state,
        thresholds = [0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.00],
        colors = ["#CCCCCC", "#f7fcfd", "#e0ecf4", "#9ebcda", "#8c96c6", "#8c6bb1", "#88419d", "#6e016b", "#000000"],
        svg = svg_state,
        state = st_name
    )
    writesvg(svg_filled_roll14_state, "output/COVID-19_rolling_14day_Prevalence_in_" + st_name + "_by_county.svg")

    if st_name in ['Nebraska', 'New Hampshire', 'Rhode Island', 'Wyoming', 'the United States']:
        continue # too many unassigned cases
    svg_filled_deaths_state = fillmap_prevalence(
        fipses = fipses_deaths_state,
        covid_counts = covid_counts_deaths_state,
        populations = populations_state,
        svg = svg_state,
        state = st_name,
        thresholds = [0, 0.002, 0.010, 0.050, 0.100],
        colors = ["#CCCCCC", "#fdd49e", "#fdbb84", "#fc8d59", "#e34a33", "#b30000"]
    )
    writesvg(svg_filled_deaths_state, "output/COVID-19_Deaths_Prevalence_in_" + st_name + "_by_county.svg")

    # Disabled for now: the data is too messy. Too many deaths were unassigned to a county.
#     svg_filled_roll14_deaths_state = fillmap_roll14_prevalence(
#         fipses = fipses_deaths_state,
#         covid_counts14 = covid_counts14_deaths_state,
#         populations = populations_state,
#         svg = svg_state,
#         state = st_name,
#         thresholds = [0, 0.001, 0.002, 0.005, 0.010],
#         colors = ["#CCCCCC", "#c7e9b4", "#7fcdbb", "#41b6c4", "#2c7fb8", "#253494"]
#     )
#     writesvg(svg_filled_roll14_deaths_state, "output/COVID-19_rolling_14day_Deaths_Prevalence_in_" + st_name + "_by_county.svg")


# test is the loop worked correctly, and if all dates are identical (to cover edge case where one file is updated, and another not yet)
assert len(set(asof_list)) == 1
