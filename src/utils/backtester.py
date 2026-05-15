"""
Backtesting Framework
"""
import logging
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__name__)


class Backtester:
    """Backtesting framework for strategies"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize backtester"""
        self.config = config or {}
        self.trades: List[Dict[str, Any]] = []
        self.results = None
    
    async def run_backtest(
        self,
        historical_data: List[Dict[str, Any]],
        strategy_func
    ) -> Dict[str, Any]:
        """Run a backtest on historical data"""
        try:
            logger.info("Starting backtest...")
            
            self.trades = []
            total_trades = 0
            winning_trades = 0
            total_profit = 0
            max_drawdown = 0
            
            for i, candle in enumerate(historical_data):
                # Generate signal
                signal = await strategy_func(historical_data[:i+1])
                
                if signal['action'] in ['BUY', 'SELL']:
                    total_trades += 1
                    
                    # Calculate trade PnL (placeholder)
                    trade_profit = candle['close'] * 0.01  # 1% profit
                    
                    if trade_profit > 0:
                        winning_trades += 1
                    
                    total_profit += trade_profit
                    
                    self.trades.append({
                        'timestamp': candle.get('time'),
                        'action': signal['action'],
                        'price': candle['close'],
                        'profit': trade_profit
                    })
            
            # Calculate metrics
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            sharpe_ratio = self._calculate_sharpe_ratio()
            
            results = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'average_profit': total_profit / total_trades if total_trades > 0 else 0,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio
            }
            
            self.results = results
            logger.info(f"Backtest completed: {results}")
            
            return results
        
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return {}
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        if not self.trades:
            return 0.0
        
        profits = [t['profit'] for t in self.trades]
        
        if len(profits) < 2:
            return 0.0
        
        returns = pd.Series(profits)
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        return float(sharpe)
    
    def get_report(self) -> str:
        """Get backtest report"""
        if not self.results:
            return "No backtest results available"
        
        report = f"""
        Backtest Report
        ===============
        Total Trades: {self.results['total_trades']}
        Winning Trades: {self.results['winning_trades']}
        Losing Trades: {self.results['losing_trades']}
        Win Rate: {self.results['win_rate']:.2f}%
        Total Profit: ${self.results['total_profit']:.2f}
        Average Profit: ${self.results['average_profit']:.2f}
        Max Drawdown: {self.results['max_drawdown']:.2f}%
        Sharpe Ratio: {self.results['sharpe_ratio']:.2f}
        """
        
        return report
