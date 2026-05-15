"""
Trading Agent - Main orchestrator for crypto trading
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from src.exchange.binance_client import BinanceExchange
from src.strategies.strategy_manager import StrategyManager
from src.risk_management.risk_manager import RiskManager
from src.portfolio.portfolio_manager import PortfolioManager


logger = logging.getLogger(__name__)


class TradingAgent:
    """Main trading agent orchestrator"""
    
    def __init__(self, exchange: BinanceExchange, config: Dict[str, Any] = None):
        """
        Initialize trading agent
        
        Args:
            exchange: Exchange client (Binance)
            config: Configuration dictionary
        """
        self.exchange = exchange
        self.config = config or {}
        self.strategy_manager = StrategyManager()
        self.risk_manager = RiskManager(config)
        self.portfolio_manager = PortfolioManager(exchange)
        self.running = False
        self.trades = []
    
    async def start(self):
        """Start the trading agent"""
        self.running = True
        logger.info("Trading agent started")
        
        try:
            while self.running:
                await self._trading_cycle()
                
                # Wait before next cycle
                await asyncio.sleep(self.config.get('interval', 300))
        
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
        
        finally:
            self.running = False
            logger.info("Trading agent stopped")
    
    async def _trading_cycle(self):
        """Execute one trading cycle"""
        try:
            pairs = self.config.get('pairs', ['BTCUSDT'])
            
            for pair in pairs:
                # Get market data
                market_data = await self.exchange.get_24h_stats(pair)
                
                # Analyze signals
                signals = await self.strategy_manager.analyze(pair, market_data)
                
                if signals['action'] == 'BUY':
                    await self._execute_buy(pair, signals)
                
                elif signals['action'] == 'SELL':
                    await self._execute_sell(pair, signals)
        
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
    
    async def _execute_buy(self, pair: str, signals: Dict[str, Any]):
        """Execute a buy order"""
        try:
            # Validate risk
            is_valid = self.risk_manager.validate_trade(
                pair,
                'BUY',
                self.portfolio_manager.get_balance()
            )
            
            if not is_valid:
                logger.warning(f"Buy trade rejected for {pair} due to risk limits")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                pair,
                signals['stop_loss'],
                self.portfolio_manager.get_balance()
            )
            
            # Place order
            order = await self.exchange.place_limit_order(
                pair,
                'BUY',
                position_size,
                signals.get('entry_price', 0)
            )
            
            # Record trade
            self.trades.append({
                'pair': pair,
                'action': 'BUY',
                'order_id': order.get('orderId'),
                'price': order.get('price'),
                'quantity': order.get('executedQty'),
                'stop_loss': signals['stop_loss'],
                'take_profit': signals['take_profit']
            })
            
            logger.info(f"Buy order placed for {pair}: {order}")
        
        except Exception as e:
            logger.error(f"Error executing buy for {pair}: {str(e)}")
    
    async def _execute_sell(self, pair: str, signals: Dict[str, Any]):
        """Execute a sell order"""
        try:
            # Get current position
            position = self.portfolio_manager.get_position(pair)
            
            if not position or position['quantity'] == 0:
                logger.warning(f"No position to sell for {pair}")
                return
            
            # Place order
            order = await self.exchange.place_limit_order(
                pair,
                'SELL',
                position['quantity'],
                signals.get('exit_price', 0)
            )
            
            # Record trade
            self.trades.append({
                'pair': pair,
                'action': 'SELL',
                'order_id': order.get('orderId'),
                'price': order.get('price'),
                'quantity': order.get('executedQty')
            })
            
            logger.info(f"Sell order placed for {pair}: {order}")
        
        except Exception as e:
            logger.error(f"Error executing sell for {pair}: {str(e)}")
    
    def stop(self):
        """Stop the trading agent"""
        self.running = False
        logger.info("Stopping trading agent")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'running': self.running,
            'total_trades': len(self.trades),
            'portfolio_value': self.portfolio_manager.get_portfolio_value(),
            'positions': self.portfolio_manager.get_positions()
        }
    
    def get_trades(self) -> list:
        """Get trade history"""
        return self.trades
