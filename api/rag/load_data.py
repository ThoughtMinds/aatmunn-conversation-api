from json import load
from typing import List, Dict
from api.core.config import settings
from os import path


def load_sample_navigation_data() -> List[Dict]:
    """
    Load sample navigation intents from a JSON file.

    This function loads a list of sample navigation intents from the JSON file
    specified in the `DATABASE_INIT_DATA` setting. This data is used for
    database initialization.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents a
                    navigation intent.
    """
    if not path.isfile(settings.DATABASE_NAVIGATION_DATA):
        return []

    try:
        with open(settings.DATABASE_NAVIGATION_DATA) as f:
            sample_navigation_intents = load(f)
    except Exception as e:
        print(f"Failed to load navigation intents due to: {e}")
        sample_navigation_intents = []

    return sample_navigation_intents
