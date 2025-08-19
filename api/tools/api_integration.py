import os
import requests
from api.core.config import settings
from api.core.logging_config import logger


def get_aatmunn_access_token():

    payload = {
        "userName": settings.AATMUNN_USERNAME,
        "password": settings.AATMUNN_PASSWORD,
        "clientId": settings.AATMUNN_CLIENT_ID,
        "clientSecret": settings.AATMUNN_CLIENT_SECRET,
    }

    # Make GET request to the authentication endpoint
    try:
        response = requests.post(
            "https://iiop-demo.aatmunn.net/io/api/v3/auth/login", json=payload
        )
        response.raise_for_status()  # Raise an exception for bad status codes

        data = response.json()

        os.environ["AATMUNN_CLIENT_API_TOKEN"] = data["accessToken"]

        logger.info("Fetched Aatmunn Access Token")
        return {
            "accessToken": data["accessToken"],
            "expiresIn": data["expiresIn"],
            "refreshToken": data["refreshToken"],
            "refreshExpiresIn": data["refreshExpiresIn"],
            "userId": data["userId"],
        }

    except requests.RequestException as e:
        print(f"Error during authentication: {e}")
        return None
