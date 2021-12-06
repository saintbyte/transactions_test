from rest_framework.routers import SimpleRouter
from transactions.api_views import TransactionViewSet

router = SimpleRouter()
router.register(
    r"api/transaction",
    TransactionViewSet,
    basename="transaction",
)

urlpatterns = router.urls
