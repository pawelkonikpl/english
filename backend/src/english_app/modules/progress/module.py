from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.events import EventBus, LearningActivity
from english_app.core.modules import AppModule, ModuleContext
from english_app.modules.progress.router import router
from english_app.modules.progress.service import ProgressService


def register_events(bus: EventBus, context: ModuleContext) -> None:
    async def on_activity(activity: LearningActivity, session: AsyncSession) -> None:
        await ProgressService(session, context.clock).record(activity)

    bus.subscribe(LearningActivity, on_activity)


module = AppModule(
    key="progress",
    title="Postępy",
    router=router,
    depends_on=("profile", "review"),
    register_events=register_events,
    nav_order=0,
    icon="layout-dashboard",
)
