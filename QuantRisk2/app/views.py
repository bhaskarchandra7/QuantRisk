# app/views.py
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.shortcuts import redirect
import pandas as pd
from .import utils
from django.views.decorators.http import require_POST
import requests
import numpy as np
from textblob import TextBlob

@csrf_exempt
def test_binance(request):
    if request.method == "POST":
        body = json.loads(request.body)
        close_price = body.get("close")
        high_price = body.get("high")
        low_price = body.get("low")
        volume_price = body.get("volume")
        change_percentage = body.get("changePercent")
        symbol = body.get("symbol", "UNKNOWN")

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "binance_group",
            {
                "type": "send_binance_data",
                "data": {
                    "symbol": symbol,
                    "close": close_price,
                    "high": high_price,
                    "low": low_price,
                    "volume": volume_price,
                    "changePercent": change_percentage,
                }
            }
        )
        print(f"📡 Binance data sent for {symbol}:")
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "only POST allowed"}, status=405)

def index(request):
    return render(request, "index.html")

def dashboard(request):
    context = {"user": "Harsh"}
    return render(request, "dashboard.html", context)

def get_credentials(request):
    return JsonResponse({"userid": "1234", "pass": "4321"})

def features(request):
    return render(request, "features.html")

def portfolio(request):
    return render(request, "portfolio.html")

def risk_dashboard(request):
    if 'portfolio_symbols' not in request.session:
        request.session['portfolio_symbols'] = []
    if 'portfolio_name' not in request.session:
        request.session['portfolio_name'] = 'My Portfolio'
    return render(request, "risk_dashboard.html", {
        'portfolio': {
            'name': request.session['portfolio_name'],
            'symbols': request.session['portfolio_symbols']
        }
    })

def tools(request):
    return render(request, "tools.html")

def reports(request):
    return render(request, "reports.html")

def alert(request):
    return render(request, "alert.html")

def user_logout(request):
    logout(request)
    return redirect('index.html')

@csrf_exempt
@require_POST
def add_symbol(request):
    data = json.loads(request.body)
    symbol = data.get('symbol', '').strip().upper()
    if not symbol:
        return JsonResponse({'status': 'error', 'error': 'No symbol provided'}, status=400)
    portfolio = request.session.setdefault('portfolio_symbols', [])
    if symbol in portfolio:
        return JsonResponse({'status': 'error', 'error': 'Symbol already in portfolio'}, status=400)
    portfolio.append(symbol)
    request.session['portfolio_symbols'] = portfolio
    return JsonResponse({'status': 'success', 'symbol': symbol})

@csrf_exempt
@require_POST
def remove_symbol(request):
    data = json.loads(request.body)
    symbol = data.get('symbol', '').strip().upper()
    portfolio = request.session.get('portfolio_symbols', [])
    if symbol in portfolio:
        portfolio.remove(symbol)
        request.session['portfolio_symbols'] = portfolio
        return JsonResponse({'status': 'success', 'symbol': symbol})
    else:
        return JsonResponse({'status': 'error', 'error': 'Symbol not in portfolio'}, status=400)

def get_portfolio_data(request):
    symbols = request.session.get('portfolio_symbols', [])
    if not symbols:
        return JsonResponse({'status': 'error', 'error': 'Portfolio is empty'}, status=400)
    data_frames = {}
    for sym in symbols:
        df = utils.fetch_binance_klines(sym, interval='1d', limit=365)
        data_frames[sym] = df

    price_df = pd.DataFrame()
    for sym, df in data_frames.items():
        price_df[sym] = df['close'].values

    portfolio_value = price_df.sum(axis=1)
    risk_metrics = utils.compute_risk_metrics(portfolio_value)
    tech_indicators = {}
    for sym, df in data_frames.items():
        df_ind = utils.compute_technical_indicators(df.copy())
        tech_indicators[sym] = {
            'last_close': float(df_ind['close'].iloc[-1]),
            'sma_14': float(df_ind['sma_14'].iloc[-1]) if not pd.isna(df_ind['sma_14'].iloc[-1]) else None,
        }

    returns_df = price_df.pct_change().dropna()
    corr_matrix = utils.compute_correlation_matrix(returns_df)
    dates = [d.strftime('%Y-%m-%d') for d in data_frames[symbols[0]]['open_time']]
    response = {
        'status': 'success',
        'symbols': symbols,
        'dates': dates,
        'portfolio_value': portfolio_value.tolist(),
        'risk_metrics': {
            'var_95': risk_metrics['var'],
            'cvar_95': risk_metrics['cvar'],
            'volatility': risk_metrics['volatility'],
            'max_drawdown': risk_metrics['max_drawdown']
        },
        'technical': tech_indicators,
        'correlation_matrix': corr_matrix
    }
    return JsonResponse(response)

def volatility_heatmap_view(request):
    import requests
    import numpy as np

    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
    vol_data = []
    timeframe = request.GET.get('timeframe', '1h')  # default 1h

    interval_map = {
        '1h': ('1h', 24),
        '4h': ('4h', 24),
        '1d': ('1d', 30)
    }
    interval, limit = interval_map.get(timeframe, ('1h', 24))
    binance_interval = {
        '1h': '1h',
        '4h': '4h',
        '1d': '1d'
    }.get(timeframe, '1h')

    for symbol in symbols:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={binance_interval}&limit={limit}"
            res = requests.get(url)
            candles = res.json()
            closes = [float(c[4]) for c in candles]
            if len(closes) > 1:
                log_returns = np.diff(np.log(closes))
                volatility = np.std(log_returns)
            else:
                volatility = 0
            vol_data.append({'symbol': symbol, 'volatility': round(volatility, 6)})
        except:
            vol_data.append({'symbol': symbol, 'volatility': 0})

    return JsonResponse({'status': 'success', 'timeframe': timeframe, 'data': vol_data})


@csrf_exempt
@require_POST
def calculate_pnl(request):
    try:
        data = json.loads(request.body)
        entry = float(data.get('entry', 0))
        exit = float(data.get('exit', 0))
        qty = float(data.get('qty', 0))
        fees = float(data.get('fees', 0))
        pnl = (exit - entry) * qty - fees
        cost = (entry * qty + fees)
        percent = (pnl / cost) * 100 if cost != 0 else 0
        return JsonResponse({'pnl': round(pnl, 2), 'percent': round(percent, 2)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_price(request):
    symbol = request.GET.get('symbol', 'BTCUSDT').upper()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        price = float(data.get('price', 0))
        return JsonResponse({'symbol': symbol, 'price': price})
    except Exception as e:
        return JsonResponse({'error': 'Fetch failed', 'details': str(e)}, status=500)
    
def crypto_news_sentiment(request):
    try:
        api_key = 'a57ccf287942437f8a137e6793f73670'  # Replace with your real API key
        url = (
            'https://newsapi.org/v2/everything?'
            'q=cryptocurrency OR bitcoin OR ethereum&'
            'language=en&'
            'sortBy=publishedAt&'
            f'apiKey={api_key}'
        )
        
        response = requests.get(url)
        print("NewsAPI response status:", response.status_code)
        print("Response content:", response.text[:300])  # Print first 300 chars

        if response.status_code != 200:
            return JsonResponse({'status': 'error', 'message': f'NewsAPI returned status code {response.status_code}'}, status=500)

        data = response.json()
        articles = data.get('articles', [])
        print(f"Fetched {len(articles)} articles")

        results = []
        for item in articles[:10]:
            title = item.get('title', 'No title')
            content = item.get('description') or title or ''
            sentiment_score = 0.0

            try:
                sentiment_score = TextBlob(content).sentiment.polarity
            except Exception as e:
                print(f"Sentiment analysis failed for: {content}\nError: {e}")
                sentiment_score = 0.0

            if sentiment_score > 0.2:
                sentiment = 'positive'
            elif sentiment_score < -0.2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            results.append({
                'title': title,
                'url': item.get('url', '#'),
                'published': item.get('publishedAt', ''),
                'sentiment': sentiment,
                'score': round(sentiment_score, 3)
            })

        return JsonResponse({'status': 'success', 'data': results})

    except Exception as e:
        print("Error occurred in crypto_news_sentiment view:")
        # traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)