from app.schemas.auth import LoginRequest, OtpChallenge, OtpResendRequest, OtpVerifyRequest, Token
from app.schemas.annotation import AnnotationCreate, AnnotationOut, AnnotationUpdate
from app.schemas.audit import ActivityEventOut, AuditEventOut
from app.schemas.draft import DraftOut
from app.schemas.draft_lock import DraftLockOut
from app.schemas.invite import InviteAction, InviteCreate, InviteOut
from app.schemas.plagiarism import (
    PaymentDetailsOut,
    PaymentReferenceCreate,
    PaymentUpdate,
    PlagiarismJobOut,
    PublicPlagiarismJobOut,
    PublicPlagiarismStatusOut,
    RazorpayOrderOut,
    RazorpayVerifyIn,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberOut,
    ProjectMemberRoleUpdate,
    ProjectMemberStatusUpdate,
    ProjectOut,
    ProjectPermissionsOut,
    ProjectVisibilityUpdate,
)
from app.schemas.review import ReviewAssign, ReviewOut, ReviewSubmit
from app.schemas.user import UserCreate, UserOut, UserRoleUpdate
from app.schemas.workspace import (
    WorkspaceDocumentCreate,
    WorkspaceDocumentOut,
    WorkspaceLatexUpdate,
    WorkspaceLockOut,
    WorkspaceRevisionOut,
)

__all__ = [
    "LoginRequest",
    "OtpChallenge",
    "OtpResendRequest",
    "OtpVerifyRequest",
    "Token",
    "AnnotationCreate",
    "AnnotationOut",
    "AnnotationUpdate",
    "ActivityEventOut",
    "AuditEventOut",
    "DraftOut",
    "DraftLockOut",
    "InviteAction",
    "InviteCreate",
    "InviteOut",
    "PlagiarismJobOut",
    "PublicPlagiarismJobOut",
    "PublicPlagiarismStatusOut",
    "PaymentDetailsOut",
    "PaymentReferenceCreate",
    "PaymentUpdate",
    "RazorpayOrderOut",
    "RazorpayVerifyIn",
    "ProjectCreate",
    "ProjectMemberOut",
    "ProjectMemberRoleUpdate",
    "ProjectMemberStatusUpdate",
    "ProjectOut",
    "ProjectPermissionsOut",
    "ProjectVisibilityUpdate",
    "ReviewAssign",
    "ReviewOut",
    "ReviewSubmit",
    "UserCreate",
    "UserOut",
    "UserRoleUpdate",
    "WorkspaceDocumentCreate",
    "WorkspaceDocumentOut",
    "WorkspaceLatexUpdate",
    "WorkspaceLockOut",
    "WorkspaceRevisionOut",
]
