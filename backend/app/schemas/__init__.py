# Schemas package — export all Pydantic contracts from one place
from app.schemas.common import (             # noqa: F401
    SuccessResponse, ErrorResponse, ErrorDetail,
    PaginationMeta, PaginatedResponse,
)
from app.schemas.user import (               # noqa: F401
    UserCreate, UserUpdate, UserRead, UserResponse,
)
from app.schemas.profile import (            # noqa: F401
    ProfileCreate, ProfileUpdate, ProfileRead, ProfileResponse,
)
from app.schemas.scheme import (             # noqa: F401
    SchemeCreate, SchemeUpdate, SchemeRead, SchemeResponse,
)
from app.schemas.eligibility_rule import (   # noqa: F401
    EligibilityRuleCreate, EligibilityRuleUpdate,
    EligibilityRuleRead, EligibilityRuleResponse,
)
from app.schemas.chat_history import (       # noqa: F401
    ChatHistoryCreate, ChatHistoryRead, ChatHistoryResponse,
)
