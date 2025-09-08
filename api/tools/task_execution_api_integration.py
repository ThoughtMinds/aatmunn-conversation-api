import requests
from typing import Dict, List, Optional
from api.core.config import settings
from api.core.logging_config import logger
from langchain_core.tools import tool
from api import schema
from api import aatmunn_task_execution_api

__all__ = [
    "get_navigation_points",
    "get_user_by_id",
    "get_roles_by_user_id",
    "get_role_by_id",
    "get_product_models",
    "get_templates_by_module_id",
    "get_form_execution_summary",
    "get_areas_needing_attention",
]

# Shared base API URL for customer4
BASE_API_URL = "https://iiop-customer4-demo.aatmunn.net/io/api/v3"

def get_aatmunn_access_token() -> Optional[Dict[str, str]]:
    """
    Fetches an access token from the Aatmunn authentication API.

    This function sends a POST request with credentials to the Aatmunn login
    endpoint to obtain an access token.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing the access token
                                  and other authentication details if the
                                  request is successful, otherwise None.
    """
    payload = {
        "userName": settings.AATMUNN_USERNAME,
        "password": settings.AATMUNN_PASSWORD,
        "clientId": settings.AATMUNN_CLIENT_ID,
        "clientSecret": settings.AATMUNN_CLIENT_SECRET,
    }

    try:
        response = requests.post(
            f"{BASE_API_URL}/auth/login", json=payload
        )
        response.raise_for_status()
        data = response.json()

        logger.info("Fetched Aatmunn Access Token for customer4")
        return data["accessToken"]
    except requests.RequestException as e:
        print(f"Error during authentication: {e}")
        return None


ACCESS_TOKEN = get_aatmunn_access_token()


def get_auth_header() -> Dict[str, str]:
    """
    Constructs the Authorization header for Aatmunn API requests.

    Returns:
        Dict[str, str]: A dictionary containing the 'Authorization' header
                        with the bearer token.
    """
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


@tool
def get_navigation_points() -> Optional[schema.NavigationResponse]:
    """
    Retrieves all navigation points from the IIOP API (customer4).

    This tool makes a GET request to the navigation-points endpoint to fetch
    a list of available navigation points.

    Returns:
        Optional[schema.NavigationResponse]: A Pydantic model instance containing
                                             the navigation points if the request
                                             is successful, otherwise None.
    """
    headers = get_auth_header()
    try:
        response = requests.get(
            f"{BASE_API_URL}/navigation-points", headers=headers
        )
        response.raise_for_status()
        data = response.json()
        navigation_points = schema.NavigationResponse(**data)
        return navigation_points.model_dump()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_user_string(user_response: schema.SingleUserResponse) -> str:
    """
    Constructs a formatted string from relevant user information using Pydantic models.

    Args:
        user_response (SingleUserResponse): Pydantic model containing user data.

    Returns:
        str: Formatted string with relevant user details.
    """
    user_id = user_response.id
    full_name = f"{user_response.firstName} {user_response.middleName} {user_response.lastName}".strip()
    email = user_response.email or "No Email"
    job_title = user_response.jobTitle or "No Job Title"
    employment_type = user_response.employmentType or "Not Specified"
    status = user_response.status.status
    created_on = user_response.createdOn.strftime("%Y-%m-%d %H:%M")
    reporting_to = user_response.reportingToUserName or "No Supervisor"

    user_string = (
        f"User ID: {user_id}\n"
        f"Name: {full_name}\n"
        f"Email: {email}\n"
        f"Job Title: {job_title}\n"
        f"Employment Type: {employment_type}\n"
        f"Status: {status}\n"
        f"Created On: {created_on}\n"
        f"Reporting To: {reporting_to}\n"
    )
    return user_string


@tool
def get_user_by_id(user_id: int = 1196) -> Optional[str]:
    """
    Retrieves details of a specific user from the IIOP API (customer4).

    This tool fetches details for a user by their ID.

    Args:
        user_id (int): The ID of the user. Defaults to 1196.

    Returns:
        Optional[str]: A formatted string containing the user details if the request is
                       successful, otherwise None.
    """
    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/users/{user_id}",
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        user_response = schema.SingleUserResponse(**data)
        formatted_user = format_user_string(user_response=user_response)
        return formatted_user
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_user_roles_string(roles_response: schema.UserRolesResponse) -> str:
    """
    Constructs a formatted string from relevant user role information using Pydantic models.

    Args:
        roles_response (UserRolesResponse): Pydantic model containing role data for a user.

    Returns:
        str: Formatted string with relevant role details.
    """
    role_strings = []

    for role in roles_response.rolesData:
        role_id = role.id
        name = role.name or "No Name"
        description = role.description or "No Description"
        status = role.entityStatus.status
        created_by = role.createdBy or "Unknown"
        created_on = role.createdOn.strftime("%Y-%m-%d %H:%M")

        role_string = (
            f"Role ID: {role_id}\n"
            f"Name: {name}\n"
            f"Description: {description}\n"
            f"Status: {status}\n"
            f"Created By: {created_by}\n"
            f"Created On: {created_on}\n"
        )
        role_strings.append(role_string)

    return "\n---\n".join(role_strings)


@tool
def get_roles_by_user_id(user_id: int = 1196) -> Optional[str]:
    """
    Retrieves a list of roles for a specific user from the IIOP API (customer4).

    This tool fetches roles associated with a given user ID.

    Args:
        user_id (int): The ID of the user. Defaults to 1196.

    Returns:
        Optional[str]: A formatted string containing the list of roles if the request is
                       successful, otherwise None.
    """
    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/roles/users/{user_id}",
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        roles_response = schema.UserRolesResponse(rolesData=[schema.UserRoleData(**item) for item in data])
        formatted_roles = format_user_roles_string(roles_response=roles_response)
        return formatted_roles
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_role_string(role_response: schema.SingleRoleResponse) -> str:
    """
    Constructs a formatted string from relevant role information using Pydantic models.

    Args:
        role_response (SingleRoleResponse): Pydantic model containing role data.

    Returns:
        str: Formatted string with relevant role details.
    """
    role_id = role_response.id
    name = role_response.name or "No Name"
    description = role_response.description or "No Description"
    status = role_response.status
    created_by = role_response.createdBy or "Unknown"
    created_on = role_response.createdOn.strftime("%Y-%m-%d %H:%M")

    modules = "\n".join(
        [f"  {module.name}: Active={module.active}, HomePage={module.setAsHomePage}" for module in role_response.roleAccessPermissions.modules]
    )
    applications = "\n".join(
        [f"  {app.name}: Active={app.active}" for app in role_response.roleAccessPermissions.applications]
    )
    entities = "\n".join(
        [f"  {entity.entityName}: {', '.join([perm.name for perm in entity.permissions if perm.isEnabled])}" for entity in role_response.roleAccessPermissions.entities]
    )

    role_string = (
        f"Role ID: {role_id}\n"
        f"Name: {name}\n"
        f"Description: {description}\n"
        f"Status: {status}\n"
        f"Created By: {created_by}\n"
        f"Created On: {created_on}\n"
        f"Modules:\n{modules}\n"
        f"Applications:\n{applications}\n"
        f"Entities:\n{entities}\n"
    )
    return role_string


@tool
def get_role_by_id(role_id: int = 601) -> Optional[str]:
    """
    Retrieves details of a specific role from the IIOP API (customer4).

    This tool fetches details for a role by its ID, including access permissions.

    Args:
        role_id (int): The ID of the role. Defaults to 601.

    Returns:
        Optional[str]: A formatted string containing the role details if the request is
                       successful, otherwise None.
    """
    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/roles/{role_id}",
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        role_response = schema.SingleRoleResponse(**data)
        formatted_role = format_role_string(role_response=role_response)
        return formatted_role
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None