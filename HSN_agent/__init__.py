from . import agent

import pandas as pd
from pathlib import Path


hsn_dict = pd.read_csv('HSN_agent/data.csv')


# Create a dictionary from the HSN dictionary
HSN_DICT = dict(zip(hsn_dict['HSNCode'], hsn_dict['Description']))

