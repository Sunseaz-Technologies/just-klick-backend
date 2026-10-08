# config/api.py
from ninja import NinjaAPI
from apps.accounts.api import router as accounts_router
from apps.notifications.api import router as notification_router
from apps.advertisements.api import router as advertisements_router
from apps.categories.api import router as categories_router
from apps.businesses.api import router as businesses_router

from apps.businesses.locations_api import router as locations_router


from apps.vendors.api import router as vendors_router
from apps.dynamic.api import router as dynamic_router

api = NinjaAPI()

api.add_router("/", accounts_router)
api.add_router("/advertisements/", advertisements_router)
api.add_router("/notifications/", notification_router)
api.add_router("/categories/", categories_router)
api.add_router("/businesses/", businesses_router)

api.add_router("/locations/", locations_router)

api.add_router("/vendors/", vendors_router)
api.add_router("/dynamic/", dynamic_router)
