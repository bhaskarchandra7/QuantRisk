# url's.py of app

from django.contrib import admin
from django.urls import path
from app import views 
urlpatterns = [
    path('',views.index, name='index'),
    path('index/',views.index, name='index'),
    path('get-credentials/', views.get_credentials, name='get_credentials'),
    path('dashboard/',views.dashboard, name='dashboard'),
    
    path('test-binance/', views.test_binance, name='test_binance'),
    # path("binance-data/", views.binance_data, name="binance_data"),
    path('tools/',views.tools, name='tools'),
    path('tools/volatility-heatmap/', views.volatility_heatmap_view, name='volatility_heatmap'),
    path('tools/volatility-heatmap/', views.volatility_heatmap_view, name='volatility_heatmap'),
    path('tools/get-price/', views.get_price, name='get_price'),
    path('reports/',views.reports, name='reports'),
    path('features/',views.features, name='features'),
    path('portfolio/',views.portfolio, name='portfolio'),
    path('alert/',views.alert, name='alert'),
    path('risk_dashboard/',views.risk_dashboard, name='risk_dashboard'),
    path('features/news-sentiment/', views.crypto_news_sentiment, name='crypto_news_sentiment'),

    path('logout/', views.user_logout, name='logout'),

    path('add-symbol/', views.add_symbol, name='add_symbol'),
    path('remove-symbol/', views.remove_symbol, name='remove_symbol'),
    path('get-portfolio-data/', views.get_portfolio_data, name='get_portfolio_data'),


]