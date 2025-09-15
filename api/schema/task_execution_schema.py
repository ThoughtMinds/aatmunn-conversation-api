from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from api import schema

__all__ = [
    "OrgsEntityStatus",
    "SingleUserTaskResponse",
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
    "SingleRoleResponse",
]


class OrgsEntityStatus(BaseModel):
    entityStatus: schema.Status
    orgId: int
    statusName: Optional[str] = None
    id: int
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None


class SingleUserTaskResponse(BaseModel):
    userName: Optional[str] = None
    orgId: int
    ssoProviderName: Optional[str] = None
    workerState: Optional[str] = None
    id: int
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    jobTitle: Optional[str] = None
    uuid: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    externalReferenceId: Optional[str] = None
    profileImageUrl: Optional[str] = None
    profileImageThumbnailUrl: Optional[str] = None
    locale: Optional[str] = None
    emergencyContactNumber: Optional[str] = None
    emergencyContactEmail: Optional[str] = None
    emergencyContactRelationship: Optional[str] = None
    type: Optional[str] = None
    employmentType: Optional[str] = None
    contractorCompany: Optional[str] = None
    supervisor: bool
    status: schema.Status
    reportingUserId: Optional[int] = None
    reportingToUserName: Optional[str] = None


class ModulePermission(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    active: bool
    setAsHomePage: bool


class ApplicationPermission(BaseModel):
    id: int
    name: Optional[str] = None
    active: bool


class EntityPermission(BaseModel):
    name: Optional[str] = None
    isEnabled: bool
    excludedAttributes: List[str]


class EntityAccess(BaseModel):
    entityId: int
    entityName: Optional[str] = None
    permissions: List[EntityPermission]


class RoleAccessPermissions(BaseModel):
    modules: List[ModulePermission]
    applications: List[ApplicationPermission]
    entities: List[EntityAccess]
    partners: List[Any]


class UserRoleData(BaseModel):
    orgId: int
    name: Optional[str] = None
    description: Optional[str] = None
    entityStatus: schema.Status
    id: int
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None


class UserRolesResponse(BaseModel):
    rolesData: List[UserRoleData]


class WidgetDataUrlResponse(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    protocol: Optional[str] = None
    method: Optional[str] = None


class WidgetType(BaseModel):
    id: int
    name: Optional[str] = None
    desc: Optional[str] = None
    formFactor: Optional[str] = None
    metaData: Optional[str] = None
    isActive: bool


class WidgetItem(BaseModel):
    sequence: int
    widgetId: int
    widgetName: Optional[str] = None
    widgetDesc: Optional[str] = None
    widgetSpecs: Optional[str] = None
    widgetDataUrl: Optional[str] = None
    widgetDataUrlResponses: List[WidgetDataUrlResponse]
    widgetMetaData: Optional[Any] = None
    widgetType: WidgetType
    widgetIsActive: bool


class WidgetContent(BaseModel):
    contentType: Optional[str] = None
    isParent: Optional[bool] = None
    items: List[WidgetItem]


class TemplateData(BaseModel):
    templateId: int
    templateName: Optional[str] = None
    templateDesc: Optional[str] = None
    templateFormFactor: Optional[str] = None
    templateType: Optional[str] = None
    parentWidgetId: int
    parentWidgetName: Optional[str] = None
    templateIsActive: bool
    orgName: Optional[str] = None
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
    message: Optional[str] = None


class UserData(BaseModel):
    empId: Optional[str] = None
    lastName: Optional[str] = None
    jobTitle: Optional[str] = None
    emergencyContactRelationship: Optional[str] = None
    locale: Optional[str] = None
    type: Optional[str] = None
    uuid: Optional[str] = None
    createdOn: datetime
    orgId: int
    externalReferenceId: Optional[str] = None
    profileImageThumbnailUrl: Optional[str] = None
    emergencyContactEmail: Optional[str] = None
    id: int
    ssoProviderName: Optional[str] = None
    reportingToUserName: Optional[str] = None
    profileImageUrl: Optional[str] = None
    email: Optional[str] = None
    contractorCompany: Optional[str] = None
    updatedBy: Optional[str] = None
    employmentType: Optional[str] = None
    emergencyContactNumber: Optional[str] = None
    reportingUserId: Optional[int]
    updatedOn: datetime
    userName: Optional[str] = None
    firstName: Optional[str] = None
    phone: Optional[str] = None
    createdBy: Optional[str] = None
    middleName: Optional[str] = None
    supervisor: bool
    status: schema.Status


class UsersResponse(BaseModel):
    totalCount: int
    message: Optional[str] = None
    userData: List[UserData]


class RolesResponse(BaseModel):
    rolesData: List[UserRoleData]
    total: int
    page: int
    size: int


class EntityData(BaseModel):
    entityId: int
    entityName: Optional[str] = None
    entityType: Optional[str] = None
    status: schema.Status
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None


class EntitiesResponse(BaseModel):
    data: List[EntityData]
    total: int
    page: int
    size: int


class ModuleData(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    active: bool
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None


class ModulesResponse(BaseModel):
    data: List[ModuleData]
    total: int
    page: int
    size: int


class SingleRoleResponse(BaseModel):
    id: int
    orgId: int
    name: Optional[str] = None
    description: Optional[str] = None
    status: schema.Status
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None
    roleAccessPermissions: RoleAccessPermissions
