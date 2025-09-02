import requests
from typing import Dict, Optional, Any
from api.core.config import settings
from api.core.logging_config import logger
from api import schema
from langchain_core.tools import tool


def get_aatmunn_access_token() -> Optional[Dict[str, Any]]:
    """
    Fetches an access token from the Aatmunn authentication API.

    This function sends a POST request with credentials to the Aatmunn login
    endpoint to obtain an access token. If successful, it stores the token
    in an environment variable and returns the token details.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the access token
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
            "https://iiop-demo.aatmunn.net/io/api/v3/auth/login", json=payload
        )
        response.raise_for_status()
        data = response.json()

        logger.info("Fetched Aatmunn Access Token")
        return data["accessToken"]
    except requests.RequestException as e:
        print(f"Error during authentication: {e}")
        return None


ACCESS_TOKEN = get_aatmunn_access_token()


def get_auth_header() -> Dict[str, str]:
    """
    Constructs the Authorization header for Aatmunn API requests.

    This function retrieves the Aatmunn client API token from the environment
    variables and formats it into a dictionary suitable for use as an
    HTTP header.

    Returns:
        Dict[str, str]: A dictionary containing the 'Authorization' header
                        with the bearer token.
    """
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


@tool
def get_navigation_points() -> Optional[schema.NavigationResponse]:
    """
    Retrieves all navigation points from the IIOP API.

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
            "https://iiop-demo.aatmunn.net/io/api/v3/navigation-points", headers=headers
        )
        response.raise_for_status()
        data = response.json()
        navigation_points = schema.NavigationResponse(**data)
        return navigation_points.model_dump()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def format_issue_string(issue_response: schema.IssueResponse) -> str:
    """
    Constructs a formatted string from relevant issue information using Pydantic models.
    
    Args:
        issue_response (IssueResponse): Pydantic model containing issue data.
        
    Returns:
        str: Formatted string with relevant issue details.
    """
    issue_strings = []
    
    for issue in issue_response.allIssueDto:

        issue_id = issue.id
        issue_name = issue.issueName or "No Name"
        description = issue.description or "No Description"
        priority = issue.priorityInfo.priority
        status = issue.statusInfo.status
        

        assigned_user = (
            f"{issue.assignedUserInfo.userFirstName} {issue.assignedUserInfo.userLastName}".strip()
            if issue.assignedUserInfo.userFirstName and issue.assignedUserInfo.userLastName
            else "Unassigned"
        )
        

        due_date = (
            issue.dueDate.strftime("%Y-%m-%d %H:%M")
            if issue.dueDate
            else "No Due Date"
        )
        
        created_by = issue.createdBy or "Unknown"
        

        issue_string = (
            f"Issue ID: {issue_id}\n"
            f"Name: {issue_name}\n"
            f"Description: {description}\n"
            f"Priority: {priority}\n"
            f"Status: {status}\n"
            f"Assigned To: {assigned_user}\n"
            f"Due Date: {due_date}\n"
            f"Created By: {created_by}\n"
        )
        issue_strings.append(issue_string)
    
    return "\n---\n".join(issue_strings)

@tool
def get_issues(size: int = 1) -> Optional[schema.IssueResponse]:
    """
    Perform GET request to retrieve issues from the IIOP API.

    This tool fetches a paginated list of issues for a given organization.

    Args:
        size (int): The number of issues per page. Defaults to 1.

    Returns:
        Optional[schema.IssueResponse]: A Pydantic model instance containing
                                        the list of issues if the request is
                                        successful, otherwise None.
    """

    params = {"orgId": settings.AATMUNN_ORG_ID, "size": int(size)}

    try:
        headers = get_auth_header()
        logger.error
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/issues",
            params=params,
            headers=headers,
        )

        response.raise_for_status()

        data = response.json()
        issue_response = schema.IssueResponse(**data)
        formatted_issues = format_issue_string(issue_response=issue_response)
        return formatted_issues

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def format_user_string(user_response: schema.UserResponse) -> str:
    """
    Constructs a formatted string from relevant user information using Pydantic models.
    
    Args:
        user_response (UserResponse): Pydantic model containing user data.
        
    Returns:
        str: Formatted string with relevant user details.
    """
    user_strings = []
    
    for user in user_response.userData:
        user_id = user.id
        full_name = f"{user.firstName} {user.middleName} {user.lastName}".strip()
        email = user.email or "No Email"
        job_title = user.jobTitle or "No Job Title"
        employment_type = user.employmentType or "Not Specified"
        status = user.status.status
        created_on = user.createdOn.strftime("%Y-%m-%d %H:%M")
        reporting_to = user.reportingToUserName or "No Supervisor"
        
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
        user_strings.append(user_string)
    
    return "\n---\n".join(user_strings)

@tool
def get_users(
    size: int = 1,
    status: str = "ACTIVE",
) -> Optional[schema.UserResponse]:
    """
    Retrieves a list of users from the IIOP API.

    This tool fetches a paginated and filterable list of users for a given
    organization.

    Args:
        size (int): The number of users per page. Defaults to 1.
        status (str): The status of the users to filter by. Defaults to "ACTIVE".

    Returns:
        Optional[schema.UserResponse]: A Pydantic model instance containing
                                       the list of users if the request is
                                       successful, otherwise None.
    """
    params = {
        "orgId": settings.AATMUNN_ORG_ID,
        "size": size,
        "status": status,
    }

    try:
        headers = get_auth_header()
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/users",
            params=params,
            headers=headers,
        )

        response.raise_for_status()

        data = response.json()
        user_response = schema.UserResponse(**data)
        formatted_users = format_user_string(user_response=user_response)
        return formatted_users

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
