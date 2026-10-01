from fastapi import APIRouter
from app.api.v1.endpoints_dashboard import router as dashboard_router
from app.api.v1.endpoints_fundamental import router as fundamental_router
from app.api.v1.endpoints_geopolitical import router as geopolitical_router
from app.api.v1.endpoints_technical import router as technical_router
from app.api.v1.endpoints_analysis import router as analysis_router
from app.api.v1.endpoints_news_intelligence import router as news_intelligence_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(fundamental_router, prefix="/fundamental", tags=["Fundamental Module"])
api_router.include_router(geopolitical_router, prefix="/geopolitical", tags=["Geopolitical Module"])
api_router.include_router(technical_router, prefix="/technical", tags=["Technical Module"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["AI Analysis Engine"])
api_router.include_router(news_intelligence_router, prefix="/news-intelligence", tags=["News Intelligence Scenario Planning"])
