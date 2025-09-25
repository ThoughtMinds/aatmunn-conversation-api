import requests
from typing import Dict, List, Optional
from api.core.config import settings
from api.core.logging_config import logger
from langchain_core.tools import tool
from api import schema

__all__ = [
    "search_users",
    "get_roles",
    "get_entities",
    "get_modules",
    "get_navigation_points",
    "get_user_by_id",
    "get_roles_by_user_id",
    "get_role_by_id",
    "get_product_models",
    "get_templates_by_module_id",
    "get_form_execution_summary",
    "get_areas_needing_attention",
    "update_user",
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
        response = requests.post(f"{BASE_API_URL}/auth/login", json=payload)
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


# Format function for user list
def format_users_list(users_response: schema.UsersResponse) -> str:
    user_strings = []
    for user in users_response.userData:
        user_id = user.id
        full_name = f"{user.firstName} {user.middleName} {user.lastName}".strip()
        email = user.email or "No Email"
        status = user.status.status
        user_string = (
            f"User ID: {user_id}\n"
            f"Name: {full_name}\n"
            f"Email: {email}\n"
            f"Status: {status}\n"
        )
        user_strings.append(user_string)
    return "\n---\n".join(user_strings) if user_strings else "No users found."


@tool
def search_users(
    size: int = 5,
    # search: str = "",
    # email: str = "",
    # user_name: str = ""
    # search (str, optional): General search string (e.g., name or ID). Defaults to empty string.
    # email (str, optional): Filter by email. Defaults to empty string.
    # user_name (str, optional): Filter by username. Defaults to empty string.
) -> Optional[str]:
    """
    Searches for active users in the organization specified by TASK_EXECUTION_ORG_ID to retrieve their details and IDs. Use this to find user_id for other tools like get_user_by_id or get_roles_by_user_id.

    Args:
        size (int): Number of results per page. Defaults to 5.

    Returns:
        Optional[str]: Formatted string of matching users, or None on error.
    """
    params = {
        "orgId": settings.TASK_EXECUTION_ORG_ID,
        "order": "DESC",
        "status": "ACTIVE",
        "page": 0,
        "size": size,
        # "search": search,
        # "email": email,
        # "userName": user_name
    }
    try:
        headers = get_auth_header()
        response = requests.get(f"{BASE_API_URL}/users", params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        users_response = schema.UsersResponse(**data)
        return format_users_list(users_response)
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


@tool
def update_user(
    user_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    type: Optional[str] = None,
    job_title: Optional[str] = None,
    emp_id: Optional[str] = None,
    supervisor: Optional[bool] = None,
    contractor_company: Optional[str] = None,
    emergency_contact_email: Optional[str] = None,
    emergency_contact_number: Optional[str] = None,
    emergency_contact_relationship: Optional[str] = None,
    user_name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    external_reference_id: Optional[str] = None,
    profile_image_url: Optional[str] = None,
    profile_image_thumbnail_url: Optional[str] = None,
    uuid: Optional[str] = None,
) -> Optional[str]:
    """
    Updates details of a specific user in the IIOP API (customer4).

    This tool updates user details for a given user ID, using the organization ID from TASK_EXECUTION_ORG_ID.
    All fields except user_id are optional, allowing partial updates as supported by the API.

    Args:
        user_id (int): The ID of the user to update.
        first_name (Optional[str]): The user's first name.
        last_name (Optional[str]): The user's last name.
        middle_name (Optional[str]): The user's middle name.
        type (Optional[str]): The user type (e.g., USER or WORKER).
        job_title (Optional[str]): The user's job title.
        emp_id (Optional[str]): The user's employee ID.
        supervisor (Optional[bool]): Whether the user is a supervisor.
        contractor_company (Optional[str]): The contractor company, if applicable.
        emergency_contact_email (Optional[str]): Emergency contact email.
        emergency_contact_number (Optional[str]): Emergency contact number.
        emergency_contact_relationship (Optional[str]): Emergency contact relationship.
        user_name (Optional[str]): The user's username.
        phone (Optional[str]): The user's phone number.
        email (Optional[str]): The user's email address.
        external_reference_id (Optional[str]): External reference ID.
        profile_image_url (Optional[str]): URL of the user's profile image.
        profile_image_thumbnail_url (Optional[str]): URL of the user's profile image thumbnail.
        uuid (Optional[str]): The user's unique identifier.

    Returns:
        Optional[str]: A formatted string confirming the updated user ID, or None on error.
    """
    payload = schema.UserUpdateRequest(
        selectedProducts={"selectedEntities": []},
        selectedAreas={"selectedEntities": []},
        firstName=first_name,
        lastName=last_name,
        middleName=middle_name,
        type=type,
        jobTitle=job_title,
        empId=emp_id,
        supervisor=supervisor if supervisor is not None else False,
        contractorCompany=contractor_company,
        emergencyContactEmail=emergency_contact_email,
        emergencyContactNumber=emergency_contact_number,
        emergencyContactRelationship=emergency_contact_relationship,
        userName=user_name,
        phone=phone,
        email=email,
        externalReferenceId=external_reference_id,
        profileImageUrl=profile_image_url,
        profileImageThumbnailUrl=profile_image_thumbnail_url,
        orgId=settings.TASK_EXECUTION_ORG_ID,
        id=user_id,
        uuid=uuid,
    )
    try:
        headers = get_auth_header()
        response = requests.put(
            f"{BASE_API_URL}/users/{user_id}",
            json=payload.dict(exclude_none=True),
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        return f"Updated user with ID: {data['id']}"
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


# Format function for roles list (similar to format_user_roles_string but for list)
def format_roles_list(roles_response: schema.RolesResponse) -> str:
    role_strings = []
    for role in roles_response.rolesData:
        role_id = role.id
        name = role.name or "No Name"
        description = role.description or "No Description"
        status = role.status
        role_string = (
            f"Role ID: {role_id}\n"
            f"Name: {name}\n"
            f"Description: {description}\n"
            f"Status: {status}\n"
        )
        role_strings.append(role_string)
    return "\n---\n".join(role_strings) if role_strings else "No roles found."


@tool
def get_roles(
    search: str = "", page: int = 0, size: int = 25, sort: str = "updatedOn"
) -> Optional[str]:
    """
    Retrieves a list of roles to find role IDs. Use this to get role_id for get_role_by_id.

    Args:
        search (str): Search string for roles.
        page (int): Page number.
        size (int): Results per page.
        sort (str): Sort by (e.g., "updatedOn").

    Returns:
        Optional[str]: Formatted string of roles, or None on error.
    """
    params = {"search": search, "page": page, "size": size, "sort": sort}
    try:
        headers = get_auth_header()
        response = requests.get(f"{BASE_API_URL}/roles", params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        roles_response = schema.RolesResponse(**data)
        return format_roles_list(roles_response)
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


# Similar for entities (format function omitted for brevity; similar to above)
@tool
def get_entities(
    entity_type: str = "", search: str = "", page: int = 0, size: int = 25
) -> Optional[str]:
    """
    Retrieves a list of entities to find entity_ids for tools like get_form_execution_summary.

    Args:
        entity_type (str): Filter by entity type (e.g., "TAXONOMY").
        search (str): Search string.
        page (int): Page number.
        size (int): Results per page.

    Returns:
        Optional[str]: Formatted string of entities, or None on error.
    """
    params = {"entityType": entity_type, "search": search, "page": page, "size": size}
    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/entities", params=params, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        # Format similarly; assume EntitiesResponse model
        return "Formatted entities list"  # Implement full format
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


# Similar for modules (if needed for module_id)
@tool
def get_modules(search: str = "", page: int = 0, size: int = 25) -> Optional[str]:
    """
    Retrieves a list of modules to find module_id for get_templates_by_module_id.

    Args:
        search (str): Search string.
        page (int): Page number.
        size (int): Results per page.

    Returns:
        Optional[str]: Formatted string of modules, or None on error.
    """
    params = {"search": search, "page": page, "size": size}
    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/modules", params=params, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        # Format similarly; assume ModulesResponse
        return "Formatted modules list"  # Implement full format
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


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
        response = requests.get(f"{BASE_API_URL}/navigation-points", headers=headers)
        response.raise_for_status()
        data = response.json()
        navigation_points = schema.NavigationResponse(**data)
        return navigation_points.model_dump()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def format_user_string(user_response: schema.SingleUserTaskResponse) -> str:
    """
    Constructs a formatted string from relevant user information using Pydantic models.

    Args:
        user_response (SingleUserTaskResponse): Pydantic model containing user data.

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
        user_response = schema.SingleUserTaskResponse(**data)
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
        roles_response = schema.UserRolesResponse(
            rolesData=[schema.UserRoleData(**item) for item in data]
        )
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
        [
            f"  {module.name}: Active={module.active}, HomePage={module.setAsHomePage}"
            for module in role_response.roleAccessPermissions.modules
        ]
    )
    applications = "\n".join(
        [
            f"  {app.name}: Active={app.active}"
            for app in role_response.roleAccessPermissions.applications
        ]
    )
    entities = "\n".join(
        [
            f"  {entity.entityName}: {', '.join([perm.name for perm in entity.permissions if perm.isEnabled])}"
            for entity in role_response.roleAccessPermissions.entities
        ]
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
def get_product_models(org_id: int = 2) -> Optional[str]:
    """
    Retrieves a list of product models from the IIOP API (customer4).

    This tool fetches product models for a given organization with entity type TAXONOMY and product model type DEVICE.

    Args:
        org_id (int): The ID of the organization. Defaults to 2.

    Returns:
        Optional[str]: A formatted string containing the list of product models if the request is
                       successful, otherwise None.
    """
    params = {"entity": "TAXONOMY", "orgId": org_id, "productModelType": "DEVICE"}

    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/product-models/summary",
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


def format_template_string(template_response: schema.TemplateResponse) -> str:
    """
    Constructs a formatted string from relevant template information using Pydantic models.

    Args:
        template_response (TemplateResponse): Pydantic model containing template data.

    Returns:
        str: Formatted string with relevant template details.
    """
    template = template_response.data
    template_id = template.templateId
    name = template.templateName or "No Name"
    description = template.templateDesc or "No Description"
    form_factor = template.templateFormFactor
    template_type = template.templateType
    org_name = template.orgName
    created_on = template.createdOn.strftime("%Y-%m-%d %H:%M")
    widgets = "\n".join(
        [
            f"  Widget: {item.widgetName}, Type: {item.widgetType.name}, Active: {item.widgetIsActive}"
            for content in template.widgets
            for item in content.items
        ]
    )

    template_string = (
        f"Template ID: {template_id}\n"
        f"Name: {name}\n"
        f"Description: {description}\n"
        f"Form Factor: {form_factor}\n"
        f"Type: {template_type}\n"
        f"Organization: {org_name}\n"
        f"Created On: {created_on}\n"
        f"Widgets:\n{widgets}\n"
    )
    return template_string


@tool
def get_templates_by_module_id(
    module_id: int = 1, application_code: str = ""
) -> Optional[str]:
    """
    Retrieves template details by module ID from the IIOP API (customer4).

    This tool fetches templates associated with a given module ID and optional application code.

    Args:
        module_id (int): The ID of the module. Defaults to 1.
        application_code (str): Optional application code to filter templates. Defaults to empty string.

    Returns:
        Optional[str]: A formatted string containing the template details if the request is
                       successful, otherwise None.
    """
    params = {"applicationCode": application_code} if application_code else {}

    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/org-templates/byModuleId/{module_id}",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        template_response = schema.TemplateResponse(**data)
        formatted_template = format_template_string(template_response=template_response)
        return formatted_template
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
    from_date: str = "2025-08-08T18:30:00.000Z",
    to_date: str = "2025-09-08T18:29:59.999Z",
    summary_type: str = "result",
) -> Optional[str]:
    """
    Retrieves form execution summary from the IIOP API (customer4).

    This tool fetches a summary of form executions for specified entities and form types within a date range.

    Args:
        entity_ids (str): Comma-separated list of entity IDs. Defaults to "4,1,3".
        form_types (str): Comma-separated list of form types. Defaults to a predefined list.
        from_date (str): Start date for the summary in ISO format. Defaults to "2025-08-08T18:30:00.000Z".
        to_date (str): End date for the summary in ISO format. Defaults to "2025-09-08T18:29:59.999Z".
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
            f"{BASE_API_URL}/form-execution/summary",
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
    from_date: str = "2025-08-08T18:30:00.000Z",
    to_date: str = "2025-09-08T18:29:59.999Z",
) -> Optional[str]:
    """
    Retrieves areas needing attention from the IIOP API (customer4).

    This tool fetches data on areas requiring attention within a specified date range.

    Args:
        from_date (str): Start date for the data in ISO format. Defaults to "2025-08-08T18:30:00.000Z".
        to_date (str): End date for the data in ISO format. Defaults to "2025-09-08T18:29:59.999Z".

    Returns:
        Optional[str]: A formatted string containing areas needing attention if the request is
                       successful, otherwise None.
    """
    params = {"fromDate": from_date, "toDate": to_date}

    try:
        headers = get_auth_header()
        response = requests.get(
            f"{BASE_API_URL}/widget-data/areas-needing-attention",
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
