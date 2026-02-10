import enum


class RoleEnum(str, enum.Enum):
    student = "student"
    reviewer = "reviewer"
    faculty = "faculty"


class ProjectVisibility(str, enum.Enum):
    private = "private"
    public = "public"


class MembershipRole(str, enum.Enum):
    owner = "owner"
    coauthor = "coauthor"


class MemberStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class InviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    revoked = "revoked"
    expired = "expired"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"


class PlagiarismStatus(str, enum.Enum):
    queued = "queued"
    in_review = "in_review"
    completed = "completed"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    waived = "waived"


class DraftLockStatus(str, enum.Enum):
    active = "active"
    released = "released"
    expired = "expired"


class AnnotationStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class WorkspaceFormat(str, enum.Enum):
    word = "word"
    latex = "latex"
