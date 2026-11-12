from english_app.core.modules import AppModule
from english_app.modules.profile.router import router

module = AppModule(key="profile", title="Profil", router=router, nav_order=90, icon="user")
