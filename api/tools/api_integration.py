import requests
from typing import Dict, List, Optional, Any
from api.core.config import settings
from api.core.logging_config import logger
from api import schema
from langchain_core.tools import tool

__all__ = [
    "get_navigation_points",
    "get_issues",
    "get_users",
    "get_roles",
    "get_organization",
    "get_product_models",
    "get_historical_data",
    "get_form_execution_summary",
    "get_areas_needing_attention",
    "get_user_statuses",
]


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
            if issue.assignedUserInfo.userFirstName
            and issue.assignedUserInfo.userLastName
            else "Unassigned"
        )

        due_date = (
            issue.dueDate.strftime("%Y-%m-%d %H:%M") if issue.dueDate else "No Due Date"
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
def get_issues(size: int = 1) -> Optional[str]:
    """
    Perform GET request to retrieve issues from the IIOP API.

    This tool fetches a paginated list of issues for a given organization.

    Args:
        size (int): The number of issues per page. Defaults to 1.

    Returns:
        Optional[str]: A formatted string containing the list of issues if the request is
                       successful, otherwise None.
    """
    params = {"orgId": settings.AATMUNN_ORG_ID, "size": int(size)}

    try:
        headers = get_auth_header()
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
def get_users(size: int = 1, status: str = "ACTIVE") -> Optional[str]:
    """
    Retrieves a list of users from the IIOP API.

    This tool fetches a paginated and filterable list of users for a given
    organization.

    Args:
        size (int): The number of users per page. Defaults to 1.
        status (str): The status of the users to filter by. Defaults to "ACTIVE".

    Returns:
        Optional[str]: A formatted string containing the list of users if the request is
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


def format_role_string(role_response: schema.RoleResponse) -> str:
    """
    Constructs a formatted string from relevant role information using Pydantic models.

    Args:
        role_response (RoleResponse): Pydantic model containing role data.

    Returns:
        str: Formatted string with relevant role details.
    """
    role_strings = []

    for role in role_response.rolesData:
        role_id = role.id
        name = role.name or "No Name"
        description = role.description or "No Description"
        status = role.status
        no_of_users = role.noOfUsers
        created_by = role.createdBy or "Unknown"
        created_on = role.createdOn.strftime("%Y-%m-%d %H:%M")

        role_string = (
            f"Role ID: {role_id}\n"
            f"Name: {name}\n"
            f"Description: {description}\n"
            f"Status: {status}\n"
            f"Number of Users: {no_of_users}\n"
            f"Created By: {created_by}\n"
            f"Created On: {created_on}\n"
        )
        role_strings.append(role_string)

    return "\n---\n".join(role_strings)


@tool
def get_roles(size: int = 3) -> Optional[str]:
    """
    Retrieves a list of roles from the IIOP API.

    This tool fetches a paginated list of roles for a given organization.

    Args:
        size (int): The number of roles per page. Defaults to 3.

    Returns:
        Optional[str]: A formatted string containing the list of roles if the request is
                       successful, otherwise None.
    """
    params = {"orgId": settings.AATMUNN_ORG_ID, "size": int(size)}

    try:
        headers = get_auth_header()
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/roles",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        role_response = schema.RoleResponse(**data)
        formatted_roles = format_role_string(role_response=role_response)
        return formatted_roles
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


@tool
def get_organization(org_id: int = 4) -> Optional[schema.Organization]:
    """
    Retrieves organization details from the IIOP API.

    This tool fetches details for a specific organization by its ID.

    Args:
        org_id (int): The ID of the organization. Defaults to 4.

    Returns:
        Optional[schema.Organization]: A Pydantic model instance containing the organization
                                      details if the request is successful, otherwise None.
    """
    try:
        headers = get_auth_header()
        response = requests.get(
            f"https://iiop-demo.aatmunn.net/io/api/v3/orgs/{org_id}",
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        organization = schema.Organization(**data)
        return organization.model_dump()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_product_model_string(product_models: List[schema.ProductModel]) -> str:
    """
    Constructs a formatted string from relevant product model information using Pydantic models.

    Args:
        product_models (List[ProductModel]): List of Pydantic models containing product model data.

    Returns:
        str: Formatted string with relevant product model details.
    """
    product_strings = []

    for product in product_models:
        product_id = product.id
        name = product.name or "No Name"
        description = product.description or "No Description"
        status = product.status
        counts = product.counts

        product_string = (
            f"Product Model ID: {product_id}\n"
            f"Name: {name}\n"
            f"Description: {description}\n"
            f"Status: {status}\n"
            f"Counts: Product Models: {counts.countOfProductModels}, "
            f"Products: {counts.countOfProducts}, Capabilities: {counts.countOfCapabilities}\n"
        )
        product_strings.append(product_string)

    return "\n---\n".join(product_strings)


@tool
def get_product_models(org_id: int = 4) -> Optional[str]:
    """
    Retrieves a list of product models from the IIOP API.

    This tool fetches product models for a given organization with entity type TAXONOMY and product model type DEVICE.

    Args:
        org_id (int): The ID of the organization. Defaults to 4.

    Returns:
        Optional[str]: A formatted string containing the list of product models if the request is
                       successful, otherwise None.
    """
    params = {"entity": "TAXONOMY", "orgId": org_id, "productModelType": "DEVICE"}

    try:
        headers = get_auth_header()
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/product-models/summary",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        product_models = [schema.ProductModel(**item) for item in data]
        formatted_products = format_product_model_string(product_models=product_models)
        return formatted_products
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


@tool
def get_historical_data(
    time_period_in_days: int = 2, page: int = 0, size: int = 3000
) -> Optional[schema.HistoricalDataResponse]:
    """
    Retrieves historical data for alerts from the IIOP API.

    This tool fetches historical data for alerts within a specified time period.

    Args:
        time_period_in_days (int): The time period in days for which to fetch data. Defaults to 2.
        page (int): The page number for pagination. Defaults to 0.
        size (int): The number of records per page. Defaults to 3000.

    Returns:
        Optional[schema.HistoricalDataResponse]: A Pydantic model instance containing the historical
                                                data if the request is successful, otherwise None.
    """
    params = {
        "capability": "alerts",
        "timePeriodInDays": time_period_in_days,
        "page": page,
        "size": size,
    }

    try:
        headers = get_auth_header()
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/widget-data/historical-data",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        historical_data = schema.HistoricalDataResponse(**data)
        return historical_data.model_dump()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_form_execution_summary(
    form_execution_response: schema.FormExecutionSummaryResponse,
) -> str:
    """
    Constructs a formatted string from form execution summary information using Pydantic models.

    Args:
        form_execution_response (FormExecutionSummaryResponse): Pydantic model containing form execution data.

    Returns:
        str: Formatted string with relevant form execution details.
    """
    entity_strings = []

    for entity in form_execution_response.data.entitySummary:
        entity_id = entity.entityId
        entity_name = entity.entityName
        total_count = entity.totalCount
        statuses = "\n".join(
            [f"  {status.displayName}: {status.count}" for status in entity.statuses]
        )

        entity_string = (
            f"Entity ID: {entity_id}\n"
            f"Entity Name: {entity_name}\n"
            f"Total Count: {total_count}\n"
            f"Statuses:\n{statuses}\n"
        )
        entity_strings.append(entity_string)

    return "\n---\n".join(entity_strings)


@tool
def get_form_execution_summary(
    entity_ids: str = "4,1,3",
    form_types: str = "PRODUCT_TEST,PRODUCT_MAINTENANCE,PRODUCT_CLEANING,PRODUCT_INSPECTION,AREA_INSPECTION,WORKER_OBSERVATION,WORKER_FIT_TEST,WORKER_TRAINING",
    from_date: str = "2025-08-02T18:30:00.000Z",
    to_date: str = "2025-09-02T18:29:59.999Z",
    summary_type: str = "result",
) -> Optional[str]:
    """
    Retrieves form execution summary from the IIOP API.

    This tool fetches a summary of form executions for specified entities and form types within a date range.

    Args:
        entity_ids (str): Comma-separated list of entity IDs. Defaults to "4,1,3".
        form_types (str): Comma-separated list of form types. Defaults to a predefined list.
        from_date (str): Start date for the summary in ISO format. Defaults to "2025-08-02T18:30:00.000Z".
        to_date (str): End date for the summary in ISO format. Defaults to "2025-09-02T18:29:59.999Z".
        summary_type (str): Type of summary to retrieve. Defaults to "result".

    Returns:
        Optional[str]: A formatted string containing the form execution summary if the request is
                       successful, otherwise None.
    """
    params = {
        "entityIds": entity_ids,
        "formType": form_types,
        "fromDate": from_date,
        "toDate": to_date,
        "summaryType": summary_type,
    }

    try:
        headers = get_auth_header()
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/form-execution/summary",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        form_execution_response = schema.FormExecutionSummaryResponse(**data)
        formatted_summary = format_form_execution_summary(
            form_execution_response=form_execution_response
        )
        return formatted_summary
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_areas_needing_attention(
    areas_response: schema.AreasNeedingAttentionResponse,
) -> str:
    """
    Constructs a formatted string from areas needing attention information using Pydantic models.

    Args:
        areas_response (AreasNeedingAttentionResponse): Pydantic model containing areas data.

    Returns:
        str: Formatted string with relevant areas needing attention details.
    """
    area_strings = []

    for area in areas_response.data:
        area_string = (
            f"Area Name: {area.areaName}\n"
            f"Area ID: {area.areaId}\n"
            f"Completed Forms: {area.noOfCompletedForms}\n"
            f"Late Forms: {area.noOfLateForms}\n"
            f"Issues: {area.noOfIssues}\n"
            f"Unassigned Issues: {area.noOfUnassignedIssues}\n"
        )
        area_strings.append(area_string)

    return "\n---\n".join(area_strings)


@tool
def get_areas_needing_attention(
    from_date: str = "2025-08-02T18:30:00.000Z",
    to_date: str = "2025-09-02T18:29:59.999Z",
) -> Optional[str]:
    """
    Retrieves areas needing attention from the IIOP API.

    This tool fetches data on areas requiring attention within a specified date range.

    Args:
        from_date (str): Start date for the data in ISO format. Defaults to "2025-08-02T18:30:00.000Z".
        to_date (str): End date for the data in ISO format. Defaults to "2025-09-02T18:29:59.999Z".

    Returns:
        Optional[str]: A formatted string containing areas needing attention if the request is
                       successful, otherwise None.
    """
    params = {"fromDate": from_date, "toDate": to_date}

    try:
        headers = get_auth_header()
        response = requests.get(
            "https://iiop-demo.aatmunn.net/io/api/v3/widget-data/areas-needing-attention",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        areas_response = schema.AreasNeedingAttentionResponse(**data)
        formatted_areas = format_areas_needing_attention(areas_response=areas_response)
        return formatted_areas
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


@tool
def get_user_statuses(org_id: int = 4) -> Optional[schema.UserStatusResponse]:
    """
    Retrieves user status options for an organization from the IIOP API.

    This tool fetches the available user statuses for a given organization.

    Args:
        org_id (int): The ID of the organization. Defaults to 4.

    Returns:
        Optional[schema.UserStatusResponse]: A Pydantic model instance containing the user statuses
                                            if the request is successful, otherwise None.
    """
    try:
        headers = get_auth_header()
        response = requests.get(
            f"https://iiop-demo.aatmunn.net/io/api/v3/orgs/{org_id}/status/USER",
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        user_statuses = schema.UserStatusResponse(
            userStatuses=[schema.UserStatus(**item) for item in data]
        )
        return user_statuses.model_dump()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
