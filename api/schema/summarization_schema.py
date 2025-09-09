from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

__all__ = [
    "NavigationPoint",
    "NavigationResponse",
    "PriorityInfo",
    "StatusInfo",
    "AssignedUserInfo",
    "EntityInfo",
    "SourceEntityInfo",
    "ParentSourceEntityInfo",
    "IssueDto",
    "IssueResponse",
    "Status",
    "UserData",
    "UserResponse",
    "RoleData",
    "RoleResponse",
    "OrgStatus",
    "Organization",
    "ProductCounts",
    "ProductModel",
    "HistoricalDataResponse",
    "FormStatus",
    "EntitySummary",
    "AdditionalInfo",
    "FormExecutionData",
    "FormExecutionSummaryResponse",
    "AreaData",
    "AreasNeedingAttentionResponse",
    "UserStatus",
    "SingleUserResponse"
    "UserStatusResponse",
    "UserUpdateRequest"
]

# Navigation Options


class NavigationPoint(BaseModel):
    id: int
    name: str
    displayName: str
    channelType: str
    description: str
    modules: List[int]


class NavigationResponse(BaseModel):
    totalCount: int
    message: str
    navigationPointData: List[NavigationPoint]


# Issue


class PriorityInfo(BaseModel):
    priority: str


class StatusInfo(BaseModel):
    status: str


class AssignedUserInfo(BaseModel):
    assignedUserId: Optional[int] = None
    userFirstName: Optional[str] = None
    userLastName: Optional[str] = None
    userProfileUrl: Optional[str] = None
    userProfileThumbnailUrl: Optional[str] = None


class EntityInfo(BaseModel):
    id: Optional[int] = None
    entityName: Optional[str] = None
    instanceName: Optional[str] = None
    instanceId: Optional[str] = None


class SourceEntityInfo(BaseModel):
    id: Optional[int] = None
    entityName: Optional[str] = None
    instanceName: Optional[str] = None
    instanceId: Optional[str] = None


class ParentSourceEntityInfo(BaseModel):
    id: Optional[int] = None
    entityName: Optional[str] = None
    instanceName: Optional[str] = None
    instanceId: Optional[str] = None


class IssueDto(BaseModel):
    id: str
    issueName: str
    description: str
    issueType: str
    orgId: int
    priorityInfo: PriorityInfo
    statusInfo: StatusInfo
    assignedUserInfo: AssignedUserInfo
    entityInfo: EntityInfo
    sourceEntityInfo: SourceEntityInfo
    parentSourceEntityInfo: ParentSourceEntityInfo
    dueDate: Optional[datetime] = None
    createdOn: datetime
    updatedOn: datetime
    createdBy: str
    updatedBy: str


class IssueResponse(BaseModel):
    totalCount: int
    message: str
    allIssueDto: List[IssueDto]


# Users


class Status(BaseModel):
    id: int
    statusName: str
    status: str


class UserData(BaseModel):
    empId: Optional[str] = None
    lastName: str
    jobTitle: str
    emergencyContactRelationship: Optional[str] = None
    locale: Optional[str] = None
    type: str
    uuid: str
    createdOn: datetime
    orgId: int
    externalReferenceId: str
    profileImageThumbnailUrl: Optional[str] = None
    emergencyContactEmail: str
    id: int
    ssoProviderName: Optional[str] = None
    reportingToUserName: Optional[str] = None
    profileImageUrl: str
    email: str
    contractorCompany: Optional[str] = None
    updatedBy: str
    employmentType: Optional[str] = None
    emergencyContactNumber: str
    reportingUserId: Optional[int] = None
    updatedOn: datetime
    userName: Optional[str] = None
    firstName: str
    phone: str
    createdBy: str
    middleName: str
    supervisor: bool
    status: Status


class UserResponse(BaseModel):
    totalCount: int
    message: str
    userData: List[UserData]


# Roles


class RoleData(BaseModel):
    id: int
    name: str
    description: str
    orgId: int
    createdBy: str
    createdOn: datetime
    updatedOn: datetime
    updatedBy: str
    noOfUsers: int
    status: str


class RoleResponse(BaseModel):
    totalCount: int
    message: str
    rolesData: List[RoleData]


# Organization


class OrgStatus(BaseModel):
    id: int
    statusName: str
    status: str


class Organization(BaseModel):
    id: int
    name: str
    legalName: str
    orgType: str
    isPartner: bool
    email: str
    phone: str
    timezone: str
    language: str
    createdBy: str
    createdOn: datetime
    updatedBy: str
    updatedOn: datetime
    imageUrl: Optional[str] = None
    imageThumbnailUrl: Optional[str] = None
    faviconUrl: Optional[str] = None
    externalReferenceId: Optional[str] = None
    contactName: Optional[str] = None
    industryDomain: Optional[str] = None
    status: OrgStatus


# Product Models


class ProductCounts(BaseModel):
    countOfProductModels: int
    countOfProducts: int
    countOfCapabilities: int


class ProductModel(BaseModel):
    id: str
    name: str
    description: str
    status: str
    guid: Optional[str] = None
    profileImage: Optional[str] = None
    profileImageThumbnail: Optional[str] = None
    exportToSCCFlag: bool
    counts: ProductCounts
    createdByOrgId: Optional[int] = None
    isPublic: Optional[bool] = None


# Historical Data


class HistoricalDataResponse(BaseModel):
    totalEventCount: int
    criticalEventCount: int
    message: str
    data: List[Any]


# Form Execution Summary


class FormStatus(BaseModel):
    status: str
    displayName: str
    count: int


class EntitySummary(BaseModel):
    entityId: int
    entityName: str
    totalCount: int
    statuses: List[FormStatus]


class AdditionalInfo(BaseModel):
    name: str
    value: List[str]


class FormExecutionData(BaseModel):
    id: int
    name: str
    entitySummary: List[EntitySummary]
    additionalInfo: List[AdditionalInfo]


class FormExecutionSummaryResponse(BaseModel):
    message: str
    data: FormExecutionData


# Areas Needing Attention


class AreaData(BaseModel):
    areaName: str
    areaId: str
    noOfCompletedForms: int
    noOfLateForms: int
    noOfIssues: int
    noOfUnassignedIssues: int


class AreasNeedingAttentionResponse(BaseModel):
    totalCount: int
    message: str
    data: List[AreaData]


# User Status


class UserStatus(BaseModel):
    id: int
    statusName: str
    status: str


class UserStatusResponse(BaseModel):
    userStatuses: List[UserStatus]


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
    status: Status
    reportingUserId: Optional[int] = None
    reportingToUserName: Optional[str] = None


# ... (other existing classes unchanged)


# New model for user update request
class UserUpdateRequest(BaseModel):
    selectedProducts: dict = {"selectedEntities": []}
    selectedAreas: dict = {"selectedEntities": []}
    firstName: str
    lastName: str
    middleName: str = ""
    type: str = "USER"
    jobTitle: str = ""
    empId: str = ""
    supervisor: bool = False
    contractorCompany: Optional[str] = None
    emergencyContactEmail: str = ""
    emergencyContactNumber: str = ""
    emergencyContactRelationship: Optional[str] = None
    userName: str
    phone: str = ""
    email: str
    externalReferenceId: str = ""
    profileImageUrl: str = ""
    profileImageThumbnailUrl: str = ""
    orgId: int
    id: int
    uuid: str
