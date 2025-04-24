from .property_views import (
    PropertyListView,
    PropertyDetailView,
    PropertyCreateView,
    PropertyUpdateView,
    PropertyDeleteView,
    PropertyImageDeleteView,
    ContactOwnerView,
)

from .user_views import (
    register,
    profile,
    create_linked_account,
    switch_account,
    manage_accounts,
)

from .api_views import (
    PropertyAPIView,
    PropertyDetailAPIView,
)

from .dashboard_views import (
    dashboard,
    inquiry_detail_view,
)

from .index_views import index 