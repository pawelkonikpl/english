from english_app.core.modules import AppModule
from english_app.modules.conversation.router import router

module = AppModule(
    key="conversation",
    title="Rozmowa",
    router=router,
    depends_on=("profile", "review", "phrases"),
    nav_order=30,
    icon="messages-square",
)
