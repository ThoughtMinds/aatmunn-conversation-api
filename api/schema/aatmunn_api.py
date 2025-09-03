from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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