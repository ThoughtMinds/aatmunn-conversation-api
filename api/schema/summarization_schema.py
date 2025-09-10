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
    "SingleUserResponse",
    "UserStatusResponse",
    "UserUpdateRequest"
]

# Navigation Options


class NavigationPoint(BaseModel):
    id: int
    name: Optional[str] = None
    displayName: Optional[str] = None
    channelType: Optional[str] = None
    description: Optional[str] = None
    modules: List[int]


class NavigationResponse(BaseModel):
    totalCount: int
    message: Optional[str] = None
    navigationPointData: List[NavigationPoint]


# Issue


class PriorityInfo(BaseModel):
    priority: Optional[str] = None


class StatusInfo(BaseModel):
    status: Optional[str] = None


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
    id: Optional[str] = None
    issueName: Optional[str] = None
    description: Optional[str] = None
    issueType: Optional[str] = None
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
    createdBy: Optional[str] = None
    updatedBy: Optional[str] = None


class IssueResponse(BaseModel):
    totalCount: int
    message: Optional[str] = None
    allIssueDto: List[IssueDto]


# Users


class Status(BaseModel):
    id: int
    statusName: Optional[str] = None
    status: Optional[str] = None


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
    reportingUserId: Optional[int] = None
    updatedOn: datetime
    userName: Optional[str] = None
    firstName: Optional[str] = None
    phone: Optional[str] = None
    createdBy: Optional[str] = None
    middleName: Optional[str] = None
    supervisor: bool
    status: Status


class UserResponse(BaseModel):
    totalCount: int
    message: Optional[str] = None
    userData: List[UserData]


# Roles


class RoleData(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    orgId: int
    createdBy: Optional[str] = None
    createdOn: datetime
    updatedOn: datetime
    updatedBy: Optional[str] = None
    noOfUsers: int
    status: Optional[str] = None


class RoleResponse(BaseModel):
    totalCount: int
    message: Optional[str] = None
    rolesData: List[RoleData]


# Organization


class OrgStatus(BaseModel):
    id: int
    statusName: Optional[str] = None
    status: Optional[str] = None


class Organization(BaseModel):
    id: int
    name: Optional[str] = None
    legalName: Optional[str] = None
    orgType: Optional[str] = None
    isPartner: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    createdBy: Optional[str] = None
    createdOn: datetime
    updatedBy: Optional[str] = None
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
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
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
    message: Optional[str] = None
    data: List[Any]


# Form Execution Summary


class FormStatus(BaseModel):
    status: Optional[str] = None
    displayName: Optional[str] = None
    count: int


class EntitySummary(BaseModel):
    entityId: int
    entityName: Optional[str] = None
    totalCount: int
    statuses: List[FormStatus]


class AdditionalInfo(BaseModel):
    name: Optional[str] = None
    value: List[str]


class FormExecutionData(BaseModel):
    id: int
    name: Optional[str] = None
    entitySummary: List[EntitySummary]
    additionalInfo: List[AdditionalInfo]


class FormExecutionSummaryResponse(BaseModel):
    message: Optional[str] = None
    data: FormExecutionData


# Areas Needing Attention


class AreaData(BaseModel):
    areaName: Optional[str] = None
    areaId: Optional[str] = None
    noOfCompletedForms: int
    noOfLateForms: int
    noOfIssues: int
    noOfUnassignedIssues: int


class AreasNeedingAttentionResponse(BaseModel):
    totalCount: int
    message: Optional[str] = None
    data: List[AreaData]


# User Status


class UserStatus(BaseModel):
    id: int
    statusName: Optional[str] = None
    status: Optional[str] = None


class UserStatusResponse(BaseModel):
    userStatuses: List[UserStatus]


class OrgsEntityStatus(BaseModel):
    entityStatus: Status
    orgId: int
    statusName: Optional[str] = None
    id: int
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None


class SingleUserResponse(BaseModel):
    userName: Optional[str] = None
    orgId: int
    orgsEntityStatus: OrgsEntityStatus
    ssoProviderName: Optional[str] = None
    workerState: Optional[str] = None
    id: int
    createdOn: datetime
    createdBy: Optional[str] = None
    updatedOn: datetime
    updatedBy: Optional[str] = None
    empId: Optional[str] = None
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
    status: Status
    reportingUserId: Optional[int] = None
    reportingToUserName: Optional[str] = None


# ... (other existing classes unchanged)


# New model for user update request
class UserUpdateRequest(BaseModel):
    selectedProducts: dict = {"selectedEntities": []}
    selectedAreas: dict = {"selectedEntities": []}
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    type: Optional[str] = None
    jobTitle: Optional[str] = None
    empId: Optional[str] = None
    supervisor: bool = False
    contractorCompany: Optional[str] = None
    emergencyContactEmail: Optional[str] = None
    emergencyContactNumber: Optional[str] = None
    emergencyContactRelationship: Optional[str] = None
    userName: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    externalReferenceId: Optional[str] = None
    profileImageUrl: Optional[str] = None
    profileImageThumbnailUrl: Optional[str] = None
    orgId: int
    id: int
    uuid: Optional[str] = None
