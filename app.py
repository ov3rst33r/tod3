import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import requests
from test import StockDataGenerator

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

ALPHA_VANTAGE_API_KEY = "GG1770RAJGKIDYDC"

def get_stock_data(ticker, days_back=90, test_data = False):
    if not test_data:
        source = "Using Alpha Vantage API"
        limit = "(Max: 25 requests/day)"
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            if "Error Message" in data:
                raise Exception(data["Error Message"])
            
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                raise Exception("API returned no information")
                
            df = pd.DataFrame(time_series).T
            df.columns = [col.split('. ')[1].lower() for col in df.columns]
            
            column_mapping = {
                'open': 'open',
                'high': 'high', 
                'low': 'low', 
                'close': 'close',
                'volume': 'volume'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            df.index.name = 'date'
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['date'])
            
            df = df.sort_values('date')
            if days_back > 0:
                start_date = datetime.now() - timedelta(days=days_back)
                df = df[df['date'] >= start_date]
            
            for col in df.columns:
                if col != 'date':
                    df[col] = pd.to_numeric(df[col])
                    
            df['adj_close'] = df['close']
            
            return (df, source, limit)
            
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            return (pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']), source, limit)
    
    test_generator = StockDataGenerator()
    source = "Using pre-generated data"
    limit = "API limitations not applicable"
    return (test_generator.gen_stock_data(ticker, days_back), source, limit)
        

DEFAULT_TICKER = "GOOGL"
DEFAULT_DAYS = 30

stock_options = [
    {'label': 'Apple (AAPL)', 'value': 'AAPL'},
    {'label': 'Microsoft (MSFT)', 'value': 'MSFT'},
    {'label': 'Google (GOOGL)', 'value': 'GOOGL'},
    {'label': 'Amazon (AMZN)', 'value': 'AMZN'},
    {'label': 'Tesla (TSLA)', 'value': 'TSLA'},
    {'label': 'NVIDIA (NVDA)', 'value': 'NVDA'},
    {'label': 'Meta/Facebook (META)', 'value': 'META'},
    {'label': 'Netflix (NFLX)', 'value': 'NFLX'}
]

app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.H1("Stock prices", className="text-center my-4")
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Stocks options"),
                dbc.CardBody([
                    html.Label("Company:"),
                    dcc.Dropdown(id='ticker-dropdown', options=stock_options, value=DEFAULT_TICKER, clearable=False),

                    html.Br(),

                    html.Label("Days:"),
                    dcc.Slider(
                        id='days-slider',
                        min=30, max=365, step=30, value=DEFAULT_DAYS,
                        marks={30: '30 days', 90: '90 days', 180: '180 days', 365: '365 days'}
                    ),

                    html.Br(),

                    dbc.Button("Update", id="update-button", className="me-2"),
                    dbc.Button("Download data", id="btn-download-csv"),
                    dcc.Download(id="download-dataframe-csv"),

                    dbc.Spinner(html.Div(id="loading-output", className="mt-3")),

                    html.Div([
                        html.P("Using Alpha Vantage API", className="text-muted small mt-3", id="source"),
                        html.P("(Max: 25 requests/day)", className="text-muted small", id="limit")
                    ])
                ])
            ], className="mx-auto", style={"maxWidth": "500px"})
        ], width=12)
    ], className="mb-4 justify-content-center"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Price chart"),
                dbc.CardBody([
                    dcc.Graph(id='stock-price-chart', style={'height': '300px'})
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Volume analysis"),
                dbc.CardBody([
                    dcc.Graph(id='volume-chart', style={'height': '300px'})
                ])
            ])
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Stats"),
                dbc.CardBody([
                    html.Div(id='stats-table')
                ])
            ], className="mx-auto", style={"maxWidth": "600px"})
        ], width=12)
    ], className="mb-4 justify-content-center"),


    html.Footer([
        html.P("Copyright: none", className="text-center")
    ])
], fluid=True)

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    State("ticker-dropdown", "value"),
    State("days-slider", "value"),
    prevent_initial_call=True,
)
def download_csv(n_clicks, ticker, days):
    df = get_stock_data(ticker, days)
    return dcc.send_data_frame(df.to_csv, f"{ticker}_data.csv")

@app.callback(
    [Output('stock-price-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('stats-table', 'children'),
     Output('loading-output', 'children'),
     Output('source', 'children'),
     Output('limit', 'children')],
    [Input('update-button', 'n_clicks')],
    [State('ticker-dropdown', 'value'),
     State('days-slider', 'value')]
)
def update_charts(n_clicks, ticker, days):
    try:
        df, source, limit = get_stock_data(ticker, days)
        
        if df.empty:
            empty_fig = go.Figure().update_layout(title="Data not found")
            return (empty_fig, empty_fig, "Data not found", 
                    "Data was not received", source, limit)
        
        fig_price = go.Figure()
        
        fig_price.add_trace(
            go.Candlestick(
                x=df['date'], open=df['open'], high=df['high'],
                low=df['low'], close=df['close'], name='OHLC'
            )
        )
        
        fig_price.update_layout(
            title=f"Stock price ({ticker})",
            xaxis_title="Date", yaxis_title="Price ($)",
            template="plotly_white", xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig_volume = go.Figure()
        fig_volume.add_trace(
            go.Bar(x=df['date'], y=df['volume'], name='Volume', marker_color='dodgerblue')
        )
        fig_volume.add_trace(
            go.Scatter(x=df['date'], y=df['close'], name='Closing price', 
                      line=dict(color='red', width=1), yaxis="y2")
        )
        fig_volume.update_layout(
            title=f"Sales volume ({ticker})",
            xaxis_title="Date", yaxis_title="Volume",
            yaxis2=dict(title="Price ($)", overlaying="y", side="right", showgrid=False),
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        if len(df) > 0:
            latest = df.iloc[-1]
            oldest = df.iloc[0]
            price_change = latest['close'] - oldest['close']
            pct_change = (price_change / oldest['close']) * 100
            
            stats_table = html.Div([
                html.H5(f"Stats: {ticker}"),
                html.Table([
                    html.Tr([html.Td("Last date:"), html.Td(latest['date'].strftime('%Y-%m-%d'))]),
                    html.Tr([html.Td("Opening price:"), html.Td(f"${latest['open']:.2f}")]),
                    html.Tr([html.Td("Closing price:"), html.Td(f"${latest['close']:.2f}")]),
                    html.Tr([html.Td("Highest price:"), html.Td(f"${latest['high']:.2f}")]),
                    html.Tr([html.Td("Lowest price:"), html.Td(f"${latest['low']:.2f}")]),
                    html.Tr([html.Td("Volume:"), html.Td(f"{latest['volume']:,}")]),
                    html.Tr([html.Td("Changes by period:"), html.Td(f"${price_change:.2f} ({pct_change:.2f}%)")], 
                           style={'color': 'green' if price_change > 0 else 'red'})
                ], className="table table-striped")
            ])
        else:
            stats_table = html.Div("Not enough data to generate stats")
        
        return (fig_price, fig_volume, stats_table, f"Updated data: {ticker}", source, limit)
    
    except Exception as e:
        empty_fig = go.Figure().update_layout(title="Error while fetching data")
        error_message = html.Div([
            html.H5("Error while fetching data"),
            html.P(f"Details: {str(e)}")
        ])
        return (empty_fig, empty_fig, error_message, f"Error: {str(e)}", source, limit)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)
