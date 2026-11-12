from english_app.core.modules import AppModule
from english_app.modules.review.router import router

module = AppModule(
    key="review",
    title="Powtórki",
    router=router,
    depends_on=("profile",),
    nav_order=20,
    icon="repeat",
)
