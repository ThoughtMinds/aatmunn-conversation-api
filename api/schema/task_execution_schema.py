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
    "WidgetDataUrlResponse",
    "WidgetType",
    "WidgetItem",
    "WidgetContent",
    "TemplateData",
    "TemplateResponse",
    "UsersResponse",
    "RolesResponse",
    "EntitiesResponse",
    "ModulesResponse",
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


class WidgetDataUrlResponse(BaseModel):
    name: str
    url: str
    protocol: str
    method: str


class WidgetType(BaseModel):
    id: int
    name: str
    desc: str
    formFactor: str
    metaData: Optional[str] = None
    isActive: bool


class WidgetItem(BaseModel):
    sequence: int
    widgetId: int
    widgetName: str
    widgetDesc: str
    widgetSpecs: str
    widgetDataUrl: str
    widgetDataUrlResponses: List[WidgetDataUrlResponse]
    widgetMetaData: Optional[Any] = None
    widgetType: WidgetType
    widgetIsActive: bool


class WidgetContent(BaseModel):
    contentType: str
    isParent: Optional[bool] = None
    items: List[WidgetItem]


class TemplateData(BaseModel):
    templateId: int
    templateName: str
    templateDesc: str
    templateFormFactor: str
    templateType: str
    parentWidgetId: int
    parentWidgetName: str
    templateIsActive: bool
    orgName: str
    orgId: int
    defaultTemplateId: int
    widgets: List[WidgetContent]
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None
    moduleId: Optional[int] = None


class TemplateResponse(BaseModel):
    data: TemplateData
    message: str = "SUCCESS"


class UsersResponse(BaseModel):
    data: List[SingleUserResponse]
    total: int
    page: int
    size: int


class RolesResponse(BaseModel):
    rolesData: List[UserRoleData]
    total: int
    page: int
    size: int


class EntityData(BaseModel):
    entityId: int
    entityName: str
    entityType: str
    status: schema.Status
    createdOn: datetime
    createdBy: str
    updatedOn: datetime
    updatedBy: str


class EntitiesResponse(BaseModel):
    data: List[EntityData]
    total: int
    page: int
    size: int


class ModuleData(BaseModel):
    id: int
    name: str
    description: str
    active: bool
    createdOn: datetime
    createdBy: str
    updatedOn: datetime
    updatedBy: str


class ModulesResponse(BaseModel):
    data: List[ModuleData]
    total: int
    page: int
    size: int