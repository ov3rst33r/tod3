import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StockDataGenerator:
    
    def __init__(self):
        self.ticker_params = {
            'AAPL': {'price': 180.0, 'volatility': 0.015, 'trend': 0.0005},
            'MSFT': {'price': 350.0, 'volatility': 0.014, 'trend': 0.0007},
            'GOOGL': {'price': 140.0, 'volatility': 0.018, 'trend': 0.0004},
            'AMZN': {'price': 130.0, 'volatility': 0.022, 'trend': 0.0006},
            'TSLA': {'price': 210.0, 'volatility': 0.040, 'trend': 0.0005},
            'NVDA': {'price': 750.0, 'volatility': 0.035, 'trend': 0.0010},
            'META': {'price': 450.0, 'volatility': 0.025, 'trend': 0.0003},
            'NFLX': {'price': 550.0, 'volatility': 0.030, 'trend': 0.0002}
        }
    
    def gen_stock_data(self, ticker, days_back=90):
        np.random.seed(sum(ord(c) for c in ticker))
        
        params = self.ticker_params.get(ticker, {'price': 100.0, 'volatility': 0.02, 'trend': 0.0004})
        start_price = params['price']
        volatility = params['volatility']
        trend = params['trend']
        
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dates = []
        current_date = end_date - timedelta(days=days_back)
        while current_date <= end_date:
            if current_date.weekday() < 5: 
                dates.append(current_date)
            current_date += timedelta(days=1)
        
        n_days = len(dates)
        close_prices = [start_price]
        
        for i in range(1, n_days):
            daily_return = np.random.normal(trend, volatility)
            
            cycle = 0.02 * start_price * np.sin(2 * np.pi * i / 30)
            
            new_price = max(0.1, close_prices[-1] * (1 + daily_return) + cycle * 0.1)
            close_prices.append(new_price)
        
        df = pd.DataFrame()
        df['date'] = dates
        df['close'] = close_prices
        
        df['open'] = df['close'].shift(1) * (1 + np.random.uniform(-0.01, 0.01, size=n_days))
        df.loc[0, 'open'] = start_price * (1 + np.random.uniform(-0.01, 0.01))
        
        daily_range = df['close'] * np.random.uniform(0.01, 0.03, size=n_days)
        df['high'] = df['close'] + daily_range * 0.6
        df['low'] = df['close'] - daily_range * 0.6

        for i in range(n_days):
            df.loc[i, 'high'] = max(df.loc[i, 'high'], df.loc[i, 'open'], df.loc[i, 'close'])
            df.loc[i, 'low'] = min(df.loc[i, 'low'], df.loc[i, 'open'], df.loc[i, 'close'])
        
        base_volume = sum(ord(c) for c in ticker) * 1000
        df['volume'] = (base_volume * np.random.uniform(0.7, 1.3, size=n_days)).astype(int)
        df['adj_close'] = df['close']
        
        for col in ['open', 'high', 'low', 'close', 'adj_close']:
            df[col] = df[col].round(2)
        
        return df

if __name__ == "__main__":
    generator = StockDataGenerator()
    data = generator.get_stock_data('AAPL', days_back=30)
    print(data.head())