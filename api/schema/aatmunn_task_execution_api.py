from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from api import schema

__all__ = [
    "OrgsEntityStatus",
    "SingleUserResponse",
    "ModulePermission",
    "ApplicationPermission",
    "EntityPermission",
    "EntityAccess",
    "RoleAccessPermissions",
    "UserRoleData",
    "UserRolesResponse",
]

class OrgsEntityStatus(BaseModel):
    entityStatus: schema.Status
    orgId: int
    statusName: str
    id: int
    createdOn: datetime
    createdBy: str
    updatedOn: datetime
    updatedBy: str


class SingleUserResponse(BaseModel):
    userName: str
    orgId: int
    orgsEntityStatus: OrgsEntityStatus
    ssoProviderName: str
    workerState: str
    id: int
    createdOn: datetime
    createdBy: str
    updatedOn: datetime
    updatedBy: str
    empId: str
    firstName: str
    middleName: str
    lastName: str
    jobTitle: str
    uuid: str
    phone: str
    email: str
    externalReferenceId: str
    profileImageUrl: str
    profileImageThumbnailUrl: str
    locale: Optional[str] = None
    emergencyContactNumber: str
    emergencyContactEmail: str
    emergencyContactRelationship: Optional[str] = None
    type: str
    employmentType: Optional[str] = None
    contractorCompany: Optional[str] = None
    supervisor: bool
    status: schema.Status
    reportingUserId: Optional[int] = None
    reportingToUserName: Optional[str] = None


class ModulePermission(BaseModel):
    id: int
    name: str
    description: str
    active: bool
    setAsHomePage: bool


class ApplicationPermission(BaseModel):
    id: int
    name: str
    active: bool


class EntityPermission(BaseModel):
    name: str
    isEnabled: bool
    excludedAttributes: List[str]


class EntityAccess(BaseModel):
    entityId: int
    entityName: str
    permissions: List[EntityPermission]


class RoleAccessPermissions(BaseModel):
    modules: List[ModulePermission]
    applications: List[ApplicationPermission]
    entities: List[EntityAccess]
    partners: List[Any]


class UserRoleData(BaseModel):
    orgId: int
    name: str
    description: str
    entityStatus: schema.Status
    id: int
    createdOn: datetime
    createdBy: str
    updatedOn: datetime
    updatedBy: str


class UserRolesResponse(BaseModel):
    rolesData: List[UserRoleData]