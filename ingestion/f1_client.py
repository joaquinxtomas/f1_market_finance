import httpx
import json
from datetime import datetime

BASE_URL = 'https://api.jolpi.ca/ergast/f1'

def get_data_api(year, endpoint, race_round = None):
    endpoint = endpoint.lower()
    if (endpoint != 'constructors') and (endpoint != 'results') and (endpoint != 'races'):
        raise ValueError("Opciones válidas: 'constructors', 'results', 'races'")

    actual_year = datetime.now().year
    if(year <= actual_year):
        try:
            if race_round is None:
                r = httpx.get(f'{BASE_URL}/{year}/{endpoint}/')
            else:
                r = httpx.get(f'{BASE_URL}/{year}/{race_round}/{endpoint}/')
            r.raise_for_status()
            req = r.json()
            if(endpoint == 'constructors'):
                data = req["MRData"]["ConstructorTable"]["Constructors"]
            elif(endpoint in ('results', 'races')):
                data = req["MRData"]["RaceTable"]["Races"]
            return data
        except httpx.HTTPError as e:
            print(f"Error al consultar la API: {e}")
            raise
    else:
        raise ValueError("El año no puede ser mayor al actual.")
