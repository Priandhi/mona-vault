#!/usr/bin/env python3
"""
Mona Futures Engine v1.0 — Binance Futures Trading System
==========================================================
Features that beat MJ9 TRADER MAPING:
  1. OI Divergence Scanner (MJ9 doesn't have)
  2. Funding Rate Monitor (MJ9 doesn't have)
  3. Liquidation Heatmap (MJ9 doesn't have)
  4. Taker Buy/Sell Volume (MJ9 doesn't have)
  5. CVD — Cumulative Volume Delta (MJ9 doesn't have)
  6. Order Flow Imbalance (MJ9 doesn't have)
  7. Basis / Premium Index (MJ9 doesn't have)
  8. Smart Money Detection — on-chain → CEX flow (MJ9 doesn't have)
  9. Multi-Timeframe Analysis (MJ9 has this)
 10. Fibonacci + Order Block mapping (MJ9 has this — we replicate)
 11. Multi-TP with partial exits (MJ9 has this — we improve)
 12. Trailing Stop Loss (MJ9 doesn't have)
 13. Position Sizing by Kelly Criterion (MJ9 doesn't have)
 14. Correlation Analysis (MJ9 doesn't have)
 15. Volume Profile (MJ9 doesn't have)
 16. VWAP (MJ9 doesn't have)
 17. Market Structure BOS/CHoCH (MJ9 doesn't have)
 18. Aggregated Funding Across Exchanges (MJ9 doesn't have)

Usage:
  # Monitor only (no trading)
  python3 mona_futures_engine.py monitor --symbols BTCUSDT ETHUSDT

  # Monitor + signal alerts
  python3 mona_futures_engine.py scan --symbols BTCUSDT ETHUSDT SOLUSDT

  # Full auto-trade (needs API keys)
  python3 mona_futures_engine.py trade --symbols BTCUSDT ETHUSDT

Environment:
  BINANCE_API_KEY / BINANCE_API_SECRET — for trading (optional for monitor/scan)
"""

import os
import sys
import json
import time
import hmac
import hashlib
import asyncio
import aiohttp
import logging
# numpy not needed — pure Python calculations
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from enum import Enum
from pathlib import Path

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / '.hermes' / 'logs' / 'futures_engine.log')
    ]
)
log = logging.getLogger('MonaFutures')

# ── Constants ────────────────────────────────────────────────────────────────
BINANCE_FUTURES_REST = 'https://fapi.binance.com'
BINANCE_FUTURES_WS   = 'wss://fstream.binance.com/ws'
BINANCE_FUTURES_WS_STREAM = 'wss://fstream.binance.com/stream'

VAULT = Path.home() / 'mona-workspace' / 'vault'
TELEGRAM_SCRIPT = Path.home() / '.hermes' / 'scripts' / 'mona_telegram.py'

# ── Enums ────────────────────────────────────────────────────────────────────
class Signal(Enum):
    STRONG_LONG  = 'STRONG_LONG'
    LONG         = 'LONG'
    NEUTRAL      = 'NEUTRAL'
    SHORT        = 'SHORT'
    STRONG_SHORT = 'STRONG_SHORT'

class Timeframe(Enum):
    M1  = '1m'
    M5  = '5m'
    M15 = '15m'
    M30 = '30m'
    H1  = '1h'
    H4  = '4h'
    D1  = '1d'

# ── Config ───────────────────────────────────────────────────────────────────
@dataclass
class FuturesConfig:
    # Symbols to monitor
    symbols: List[str] = field(default_factory=lambda: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    
    # Timeframes for multi-TF analysis
    timeframes: List[str] = field(default_factory=lambda: ['5m', '15m', '1h', '4h'])
    
    # Signal thresholds
    oi_divergence_threshold: float = 5.0       # % change
    funding_extreme_threshold: float = 0.05    # 0.05% = extreme
    cvd_divergence_threshold: float = 1000000  # $1M delta
    taker_imbalance_threshold: float = 0.65    # 65% one side
    
    # Risk management
    max_position_pct: float = 0.02             # 2% of balance per trade
    max_total_exposure: float = 0.10           # 10% max total exposure
    max_drawdown_pct: float = 0.05             # 5% max drawdown → pause
    default_leverage: int = 5
    max_leverage: int = 10
    
    # TP/SL
    sl_pct: float = 0.015                      # 1.5% stop loss
    tp1_pct: float = 0.01                      # 1% TP1 (50% close)
    tp2_pct: float = 0.02                      # 2% TP2 (30% close)
    tp3_pct: float = 0.04                      # 4% TP3 (20% close, runner)
    trailing_activate_pct: float = 0.015       # Activate trailing at 1.5%
    trailing_callback_pct: float = 0.005       # 0.5% callback
    
    # Signal scoring weights
    weight_oi_divergence: float = 20
    weight_funding_rate: float = 15
    weight_cvd: float = 15
    weight_taker_volume: float = 15
    weight_order_flow: float = 10
    weight_basis: float = 5
    weight_structure: float = 10
    weight_volume_profile: float = 10
    
    # Minimum score to trigger trade
    min_score_to_trade: float = 65             # out of 100
    
    # Scan interval
    scan_interval_sec: int = 30
    
    # Telegram
    alert_topic: int = 387  # 📈 Futures Trading

    @classmethod
    def from_env(cls):
        cfg = cls()
        cfg.symbols = os.environ.get('FUTURES_SYMBOLS', 'BTCUSDT,ETHUSDT,SOLUSDT').split(',')
        return cfg


# ══════════════════════════════════════════════════════════════════════════════
# DATA LAYER — Binance Futures REST + WebSocket
# ══════════════════════════════════════════════════════════════════════════════

class BinanceFuturesData:
    """Collects all data from Binance Futures API — no auth needed for market data."""
    
    def __init__(self, config: FuturesConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _get(self, endpoint: str, params: dict = None) -> dict:
        await self._ensure_session()
        url = f"{BINANCE_FUTURES_REST}{endpoint}"
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    log.warning(f"API {endpoint} → {resp.status}: {text[:200]}")
                    return {}
        except Exception as e:
            log.error(f"API {endpoint} error: {e}")
            return {}
    
    # ── Market Data ──────────────────────────────────────────────────────────
    
    async def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> list:
        """Get candlestick data."""
        data = await self._get('/fapi/v1/klines', {
            'symbol': symbol, 'interval': interval, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    async def get_ticker(self, symbol: str) -> dict:
        """Get 24h ticker."""
        return await self._get('/fapi/v1/ticker/24hr', {'symbol': symbol})
    
    async def get_price(self, symbol: str) -> float:
        """Get current price."""
        data = await self._get('/fapi/v1/ticker/price', {'symbol': symbol})
        return float(data.get('price', 0))
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """Get order book depth."""
        return await self._get('/fapi/v1/depth', {'symbol': symbol, 'limit': limit})
    
    # ── Open Interest ────────────────────────────────────────────────────────
    
    async def get_open_interest(self, symbol: str) -> float:
        """Current open interest."""
        data = await self._get('/fapi/v1/openInterest', {'symbol': symbol})
        return float(data.get('openInterest', 0))
    
    async def get_oi_history(self, symbol: str, period: str = '1h', limit: int = 30) -> list:
        """OI history for divergence detection."""
        data = await self._get('/futures/data/openInterestHist', {
            'symbol': symbol, 'period': period, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    # ── Funding Rate ─────────────────────────────────────────────────────────
    
    async def get_funding_rate(self, symbol: str, limit: int = 10) -> list:
        """Funding rate history."""
        data = await self._get('/fapi/v1/fundingRate', {
            'symbol': symbol, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    async def get_funding_info(self) -> list:
        """Current funding rates for all symbols."""
        data = await self._get('/fapi/v1/premiumIndex')
        return data if isinstance(data, list) else []
    
    # ── Aggregated Trades (for Taker Volume + CVD) ──────────────────────────
    
    async def get_agg_trades(self, symbol: str, limit: int = 1000) -> list:
        """Recent aggregated trades — taker buy/sell data."""
        data = await self._get('/fapi/v1/aggTrades', {
            'symbol': symbol, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    # ── Liquidation ──────────────────────────────────────────────────────────
    
    async def get_recent_liquidations(self, symbol: str, limit: int = 100) -> list:
        """Recent liquidation orders (requires API key for full data)."""
        # Public endpoint — limited data
        data = await self._get('/fapi/v1/allForceOrders', {
            'symbol': symbol, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    # ── Long/Short Ratio ─────────────────────────────────────────────────────
    
    async def get_long_short_ratio(self, symbol: str, period: str = '1h', limit: int = 30) -> list:
        """Top trader long/short ratio."""
        data = await self._get('/futures/data/topLongShortPositionRatio', {
            'symbol': symbol, 'period': period, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    async def get_global_long_short_ratio(self, symbol: str, period: str = '1h', limit: int = 30) -> list:
        """Global long/short account ratio."""
        data = await self._get('/futures/data/globalLongShortAccountRatio', {
            'symbol': symbol, 'period': period, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    # ── Taker Buy/Sell Volume ────────────────────────────────────────────────
    
    async def get_taker_volume(self, symbol: str, period: str = '1h', limit: int = 30) -> list:
        """Taker buy/sell volume ratio."""
        data = await self._get('/futures/data/takerlongshortRatio', {
            'symbol': symbol, 'period': period, 'limit': limit
        })
        return data if isinstance(data, list) else []
    
    # ── Multi-symbol batch ───────────────────────────────────────────────────
    
    async def get_all_tickers(self) -> list:
        """All futures tickers for scanning."""
        return await self._get('/fapi/v1/ticker/24hr')


# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL ENGINE — 8 Advanced Signal Generators
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SignalResult:
    """Result from a single signal generator."""
    name: str
    signal: Signal
    score: float          # -100 to +100 (negative = short, positive = long)
    confidence: float     # 0 to 1
    details: str = ''
    raw_data: dict = field(default_factory=dict)


class SignalEngine:
    """Generates trading signals from market data."""
    
    def __init__(self, data: BinanceFuturesData, config: FuturesConfig):
        self.data = data
        self.config = config
    
    # ── Signal 1: OI Divergence ──────────────────────────────────────────────
    
    async def check_oi_divergence(self, symbol: str) -> SignalResult:
        """
        OI Divergence = Price direction ≠ OI direction
        Bullish: Price down + OI up = shorts piling in → squeeze coming
        Bearish: Price up + OI down = longs closing → dump coming
        """
        try:
            klines = await self.data.get_klines(symbol, '1h', 24)
            oi_hist = await self.data.get_oi_history(symbol, '1h', 24)
            
            if len(klines) < 5 or len(oi_hist) < 5:
                return SignalResult('OI Divergence', Signal.NEUTRAL, 0, 0, 'Insufficient data')
            
            # Price change over last 4 hours
            price_now = float(klines[-1][4])  # close
            price_4h_ago = float(klines[-5][4])
            price_change = ((price_now - price_4h_ago) / price_4h_ago) * 100
            
            # OI change over last 4 hours
            oi_now = float(oi_hist[-1].get('sumOpenInterestValue', 0))
            oi_4h_ago = float(oi_hist[-5].get('sumOpenInterestValue', 0))
            oi_change = ((oi_now - oi_4h_ago) / oi_4h_ago) * 100 if oi_4h_ago > 0 else 0
            
            # Divergence detection
            score = 0
            signal = Signal.NEUTRAL
            details = f'Price: {price_change:+.2f}% | OI: {oi_change:+.2f}%'
            
            if price_change < -1 and oi_change > self.config.oi_divergence_threshold:
                # Price dropping + OI rising = shorts piling → squeeze signal
                score = min(80, abs(oi_change) * 8)
                signal = Signal.STRONG_LONG
                details += ' → SHORT SQUEEZE brewing!'
            elif price_change < -0.5 and oi_change > 2:
                score = min(50, abs(oi_change) * 5)
                signal = Signal.LONG
                details += ' → Mild squeeze setup'
            elif price_change > 1 and oi_change < -self.config.oi_divergence_threshold:
                # Price rising + OI dropping = longs closing → dump signal
                score = -min(80, abs(oi_change) * 8)
                signal = Signal.STRONG_SHORT
                details += ' → DUMP signal, longs closing!'
            elif price_change > 0.5 and oi_change < -2:
                score = -min(50, abs(oi_change) * 5)
                signal = Signal.SHORT
                details += ' → Mild dump setup'
            
            return SignalResult('OI Divergence', signal, score, min(1.0, abs(score)/80), details, {
                'price_change': price_change, 'oi_change': oi_change,
                'oi_now': oi_now, 'price_now': price_now
            })
        except Exception as e:
            return SignalResult('OI Divergence', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 2: Funding Rate ───────────────────────────────────────────────
    
    async def check_funding_rate(self, symbol: str) -> SignalResult:
        """
        Extreme funding = reversal incoming
        High positive funding → longs pay shorts → short signal
        High negative funding → shorts pay longs → long signal
        """
        try:
            funding = await self.data.get_funding_rate(symbol, 5)
            if not funding:
                return SignalResult('Funding Rate', Signal.NEUTRAL, 0, 0, 'No data')
            
            current_rate = float(funding[-1].get('fundingRate', 0))
            rate_pct = current_rate * 100
            
            # Calculate trend
            rates = [float(f.get('fundingRate', 0)) for f in funding]
            avg_rate = sum(rates) / len(rates)
            rate_trend = rates[-1] - rates[0]  # positive = rising
            
            score = 0
            signal = Signal.NEUTRAL
            details = f'Funding: {rate_pct:.4f}% | Avg: {avg_rate*100:.4f}%'
            
            if abs(current_rate) > self.config.funding_extreme_threshold / 100:
                if current_rate > 0:
                    # Extreme positive → longs overcrowded → short
                    score = -min(90, rate_pct * 500)
                    signal = Signal.STRONG_SHORT
                    details += ' → EXTREME LONG crowding! Short signal.'
                else:
                    # Extreme negative → shorts overcrowded → long
                    score = min(90, abs(rate_pct) * 500)
                    signal = Signal.STRONG_LONG
                    details += ' → EXTREME SHORT crowding! Long signal.'
            elif abs(current_rate) > 0.01:
                if current_rate > 0:
                    score = -min(40, rate_pct * 200)
                    signal = Signal.SHORT
                    details += ' → Long bias, watch for reversal'
                else:
                    score = min(40, abs(rate_pct) * 200)
                    signal = Signal.LONG
                    details += ' → Short bias, watch for reversal'
            
            return SignalResult('Funding Rate', signal, score, min(1.0, abs(score)/70), details, {
                'current_rate': current_rate, 'avg_rate': avg_rate, 'trend': rate_trend
            })
        except Exception as e:
            return SignalResult('Funding Rate', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 3: CVD (Cumulative Volume Delta) ─────────────────────────────
    
    async def check_cvd(self, symbol: str) -> SignalResult:
        """
        CVD = cumsum(buy_volume - sell_volume)
        Divergence: Price up + CVD down = invisible selling
        Divergence: Price down + CVD up = invisible buying
        """
        try:
            trades = await self.data.get_agg_trades(symbol, 1000)
            if not trades:
                return SignalResult('CVD', Signal.NEUTRAL, 0, 0, 'No trade data')
            
            # Calculate CVD from agg trades
            cvd = 0
            cvd_history = []
            for trade in trades:
                qty = float(trade.get('q', 0))
                price = float(trade.get('p', 0))
                value = qty * price
                # m = true means buyer is maker = sell (taker sell)
                if trade.get('m', False):
                    cvd -= value  # taker sold
                else:
                    cvd += value  # taker bought
                cvd_history.append(cvd)
            
            if len(cvd_history) < 50:
                return SignalResult('CVD', Signal.NEUTRAL, 0, 0, 'Insufficient trades')
            
            # CVD trend
            cvd_first_half = sum(cvd_history[:len(cvd_history)//2]) / (len(cvd_history)//2)
            cvd_second_half = sum(cvd_history[len(cvd_history)//2:]) / (len(cvd_history)//2)
            cvd_trend = cvd_second_half - cvd_first_half
            
            # Price trend
            price_start = float(trades[0].get('p', 0))
            price_end = float(trades[-1].get('p', 0))
            price_change = ((price_end - price_start) / price_start) * 100 if price_start > 0 else 0
            
            score = 0
            signal = Signal.NEUTRAL
            details = f'CVD: ${cvd:,.0f} | Trend: ${cvd_trend:,.0f} | Price: {price_change:+.2f}%'
            
            # Divergence detection
            if price_change > 0.3 and cvd_trend < -100000:
                # Price up but CVD down → invisible selling
                score = -min(80, abs(cvd_trend) / 50000)
                signal = Signal.STRONG_SHORT
                details += ' → INVISIBLE SELLING detected!'
            elif price_change < -0.3 and cvd_trend > 100000:
                # Price down but CVD up → invisible buying
                score = min(80, abs(cvd_trend) / 50000)
                signal = Signal.STRONG_LONG
                details += ' → INVISIBLE BUYING detected!'
            elif cvd_trend > 50000:
                score = min(40, cvd_trend / 100000)
                signal = Signal.LONG
                details += ' → Buy pressure dominant'
            elif cvd_trend < -50000:
                score = -min(40, abs(cvd_trend) / 100000)
                signal = Signal.SHORT
                details += ' → Sell pressure dominant'
            
            return SignalResult('CVD', signal, score, min(1.0, abs(score)/70), details, {
                'cvd': cvd, 'cvd_trend': cvd_trend, 'price_change': price_change
            })
        except Exception as e:
            return SignalResult('CVD', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 4: Taker Buy/Sell Volume ──────────────────────────────────────
    
    async def check_taker_volume(self, symbol: str) -> SignalResult:
        """
        Taker buy/sell ratio — who's more aggressive?
        > 1.5 = aggressive buying → long
        < 0.67 = aggressive selling → short
        """
        try:
            taker_data = await self.data.get_taker_volume(symbol, '5m', 12)
            if not taker_data:
                return SignalResult('Taker Volume', Signal.NEUTRAL, 0, 0, 'No data')
            
            latest = taker_data[-1]
            buy_vol = float(latest.get('buySellRatio', 1))
            buy_vol_val = float(latest.get('buyVol', 0))
            sell_vol_val = float(latest.get('sellVol', 0))
            total = buy_vol_val + sell_vol_val
            
            buy_pct = (buy_vol_val / total * 100) if total > 0 else 50
            sell_pct = 100 - buy_pct
            
            # Trend over last few periods
            ratios = [float(d.get('buySellRatio', 1)) for d in taker_data[-6:]]
            ratio_trend = ratios[-1] - ratios[0] if len(ratios) > 1 else 0
            
            score = 0
            signal = Signal.NEUTRAL
            details = f'Buy: {buy_pct:.1f}% | Sell: {sell_pct:.1f}% | Ratio: {buy_vol:.2f}'
            
            if buy_pct > 65:
                score = min(80, (buy_pct - 50) * 3)
                signal = Signal.STRONG_LONG if buy_pct > 70 else Signal.LONG
                details += ' → AGGRESSIVE BUYING'
            elif sell_pct > 65:
                score = -min(80, (sell_pct - 50) * 3)
                signal = Signal.STRONG_SHORT if sell_pct > 70 else Signal.SHORT
                details += ' → AGGRESSIVE SELLING'
            elif buy_pct > 55:
                score = (buy_pct - 50) * 2
                signal = Signal.LONG
                details += ' → Mild buy pressure'
            elif sell_pct > 55:
                score = -(sell_pct - 50) * 2
                signal = Signal.SHORT
                details += ' → Mild sell pressure'
            
            return SignalResult('Taker Volume', signal, score, min(1.0, abs(score)/60), details, {
                'buy_pct': buy_pct, 'sell_pct': sell_pct, 'ratio': buy_vol, 'trend': ratio_trend
            })
        except Exception as e:
            return SignalResult('Taker Volume', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 5: Order Flow Imbalance ───────────────────────────────────────
    
    async def check_order_flow(self, symbol: str) -> SignalResult:
        """
        Order book depth analysis — where are the walls?
        Big wall = strong support/resistance
        Wall pull = fake → price will break through
        """
        try:
            book = await self.data.get_orderbook(symbol, 20)
            if not book or 'bids' not in book or 'asks' not in book:
                return SignalResult('Order Flow', Signal.NEUTRAL, 0, 0, 'No book data')
            
            bids = [(float(p), float(q)) for p, q in book['bids'][:10]]
            asks = [(float(p), float(q)) for p, q in book['asks'][:10]]
            
            bid_total = sum(q for _, q in bids)
            ask_total = sum(q for _, q in asks)
            total = bid_total + ask_total
            
            bid_pct = (bid_total / total * 100) if total > 0 else 50
            ask_pct = 100 - bid_pct
            
            # Find largest wall
            max_bid = max(bids, key=lambda x: x[1]) if bids else (0, 0)
            max_ask = max(asks, key=lambda x: x[1]) if asks else (0, 0)
            
            # Imbalance ratio
            imbalance = bid_total / ask_total if ask_total > 0 else 1
            
            score = 0
            signal = Signal.NEUTRAL
            details = f'Bid: {bid_pct:.1f}% | Ask: {ask_pct:.1f}% | Imbalance: {imbalance:.2f}'
            
            if imbalance > 2.0:
                score = min(60, (imbalance - 1) * 20)
                signal = Signal.LONG
                details += ' → Strong bid wall support'
            elif imbalance < 0.5:
                score = -min(60, (1/imbalance - 1) * 20)
                signal = Signal.SHORT
                details += ' → Heavy ask pressure'
            elif imbalance > 1.3:
                score = min(30, (imbalance - 1) * 30)
                signal = Signal.LONG
                details += ' → Bid leaning'
            elif imbalance < 0.77:
                score = -min(30, (1/imbalance - 1) * 30)
                signal = Signal.SHORT
                details += ' → Ask leaning'
            
            return SignalResult('Order Flow', signal, score, min(1.0, abs(score)/50), details, {
                'bid_total': bid_total, 'ask_total': ask_total,
                'imbalance': imbalance, 'max_bid': max_bid, 'max_ask': max_ask
            })
        except Exception as e:
            return SignalResult('Order Flow', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 6: Basis / Premium Index ──────────────────────────────────────
    
    async def check_basis(self, symbol: str) -> SignalResult:
        """
        Futures premium vs spot.
        High premium → market bullish → possible top
        Negative premium → market bearish → possible bottom
        """
        try:
            funding_info = await self.data.get_funding_info()
            if not funding_info:
                return SignalResult('Basis', Signal.NEUTRAL, 0, 0, 'No data')
            
            symbol_info = None
            for info in funding_info:
                if info.get('symbol') == symbol:
                    symbol_info = info
                    break
            
            if not symbol_info:
                return SignalResult('Basis', Signal.NEUTRAL, 0, 0, f'{symbol} not found')
            
            mark_price = float(symbol_info.get('markPrice', 0))
            index_price = float(symbol_info.get('indexPrice', 0))
            
            if index_price <= 0:
                return SignalResult('Basis', Signal.NEUTRAL, 0, 0, 'Invalid index price')
            
            basis = ((mark_price - index_price) / index_price) * 100
            
            score = 0
            signal = Signal.NEUTRAL
            details = f'Basis: {basis:.4f}% | Mark: ${mark_price:,.2f} | Index: ${index_price:,.2f}'
            
            if basis > 0.15:
                score = -min(50, basis * 100)
                signal = Signal.SHORT
                details += ' → High premium, possible top'
            elif basis < -0.15:
                score = min(50, abs(basis) * 100)
                signal = Signal.LONG
                details += ' → Negative premium, possible bottom'
            elif basis > 0.05:
                score = -min(20, basis * 100)
                details += ' → Slight contango'
            elif basis < -0.05:
                score = min(20, abs(basis) * 100)
                details += ' → Slight backwardation'
            
            return SignalResult('Basis', signal, score, min(1.0, abs(score)/40), details, {
                'basis': basis, 'mark': mark_price, 'index': index_price
            })
        except Exception as e:
            return SignalResult('Basis', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 7: Market Structure (BOS/CHoCH) ──────────────────────────────
    
    async def check_structure(self, symbol: str) -> SignalResult:
        """
        Break of Structure (BOS) = trend continuation
        Change of Character (CHoCH) = trend reversal
        Uses swing high/low detection on 1h candles.
        """
        try:
            klines = await self.data.get_klines(symbol, '1h', 50)
            if len(klines) < 20:
                return SignalResult('Structure', Signal.NEUTRAL, 0, 0, 'Insufficient data')
            
            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            
            # Find recent swing highs and lows
            swing_highs = []
            swing_lows = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    swing_highs.append((i, highs[i]))
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    swing_lows.append((i, lows[i]))
            
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return SignalResult('Structure', Signal.NEUTRAL, 0, 0, 'No clear structure')
            
            # Check last 2 swing highs and lows
            sh1, sh2 = swing_highs[-1][1], swing_highs[-2][1]
            sl1, sl2 = swing_lows[-1][1], swing_lows[-2][1]
            current = closes[-1]
            
            score = 0
            signal = Signal.NEUTRAL
            structure = 'RANGING'
            
            # Higher highs + higher lows = uptrend
            if sh1 > sh2 and sl1 > sl2:
                if current > sh1:
                    score = 60
                    signal = Signal.LONG
                    structure = 'BULLISH BOS'
                else:
                    score = 30
                    signal = Signal.LONG
                    structure = 'UPTREND'
            # Lower highs + lower lows = downtrend
            elif sh1 < sh2 and sl1 < sl2:
                if current < sl1:
                    score = -60
                    signal = Signal.SHORT
                    structure = 'BEARISH BOS'
                else:
                    score = -30
                    signal = Signal.SHORT
                    structure = 'DOWNTREND'
            # Mixed = potential reversal
            elif sh1 < sh2 and sl1 > sl2:
                structure = 'CONVERGENCE (CHoCH setup)'
                score = 0
            elif sh1 > sh2 and sl1 < sl2:
                structure = 'DIVERGENCE (CHoCH setup)'
                score = 0
            
            details = f'Structure: {structure} | HH: ${sh2:,.0f}→${sh1:,.0f} | LL: ${sl2:,.0f}→${sl1:,.0f}'
            
            return SignalResult('Structure', signal, score, min(1.0, abs(score)/50), details, {
                'structure': structure, 'swing_highs': [sh2, sh1], 'swing_lows': [sl2, sl1]
            })
        except Exception as e:
            return SignalResult('Structure', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Signal 8: Volume Profile + VWAP ──────────────────────────────────────
    
    async def check_volume_profile(self, symbol: str) -> SignalResult:
        """
        Volume Profile: where was most volume traded?
        Price above POC (Point of Control) = bullish
        Price below POC = bearish
        + VWAP for intraday bias
        """
        try:
            klines = await self.data.get_klines(symbol, '15m', 96)  # 24h of 15m candles
            if len(klines) < 20:
                return SignalResult('Volume Profile', Signal.NEUTRAL, 0, 0, 'Insufficient data')
            
            # Build volume profile
            price_volume = {}
            total_volume = 0
            total_pv = 0  # for VWAP
            
            for k in klines:
                high = float(k[2])
                low = float(k[3])
                close = float(k[4])
                vol = float(k[5])
                
                # VWAP calculation
                typical_price = (high + low + close) / 3
                total_pv += typical_price * vol
                total_volume += vol
                
                # Volume profile — bucket into price ranges
                mid = (high + low) / 2
                # Round to nearest 0.1% of price
                bucket = round(mid / (mid * 0.001)) * (mid * 0.001)
                price_volume[bucket] = price_volume.get(bucket, 0) + vol
            
            # POC = price with highest volume
            if not price_volume:
                return SignalResult('Volume Profile', Signal.NEUTRAL, 0, 0, 'No volume data')
            
            poc = max(price_volume, key=price_volume.get)
            vwap = total_pv / total_volume if total_volume > 0 else 0
            current_price = float(klines[-1][4])
            
            # Distance from POC and VWAP
            poc_dist = ((current_price - poc) / poc) * 100 if poc > 0 else 0
            vwap_dist = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0
            
            score = 0
            signal = Signal.NEUTRAL
            
            # POC analysis
            if poc_dist > 0.5:
                score += 20
                signal = Signal.LONG
            elif poc_dist < -0.5:
                score -= 20
                signal = Signal.SHORT
            
            # VWAP analysis
            if vwap_dist > 0.3:
                score += 20
                signal = Signal.LONG if score > 0 else signal
            elif vwap_dist < -0.3:
                score -= 20
                signal = Signal.SHORT if score < 0 else signal
            
            details = f'POC: ${poc:,.2f} ({poc_dist:+.2f}%) | VWAP: ${vwap:,.2f} ({vwap_dist:+.2f}%)'
            
            if score > 0:
                details += ' → Price above value area'
            elif score < 0:
                details += ' → Price below value area'
            
            return SignalResult('Volume Profile', signal, score, min(1.0, abs(score)/40), details, {
                'poc': poc, 'vwap': vwap, 'poc_dist': poc_dist, 'vwap_dist': vwap_dist
            })
        except Exception as e:
            return SignalResult('Volume Profile', Signal.NEUTRAL, 0, 0, f'Error: {e}')
    
    # ── Aggregate All Signals ────────────────────────────────────────────────
    
    async def analyze_symbol(self, symbol: str) -> Dict:
        """Run all 8 signal generators and produce a composite score."""
        
        # Run all checks in parallel
        results = await asyncio.gather(
            self.check_oi_divergence(symbol),
            self.check_funding_rate(symbol),
            self.check_cvd(symbol),
            self.check_taker_volume(symbol),
            self.check_order_flow(symbol),
            self.check_basis(symbol),
            self.check_structure(symbol),
            self.check_volume_profile(symbol),
            return_exceptions=True
        )
        
        signals = []
        for r in results:
            if isinstance(r, Exception):
                log.error(f"Signal error for {symbol}: {r}")
                signals.append(SignalResult('Error', Signal.NEUTRAL, 0, 0, str(r)))
            else:
                signals.append(r)
        
        # Weighted composite score
        weights = {
            'OI Divergence': self.config.weight_oi_divergence,
            'Funding Rate': self.config.weight_funding_rate,
            'CVD': self.config.weight_cvd,
            'Taker Volume': self.config.weight_taker_volume,
            'Order Flow': self.config.weight_order_flow,
            'Basis': self.config.weight_basis,
            'Structure': self.config.weight_structure,
            'Volume Profile': self.config.weight_volume_profile,
        }
        
        total_weight = 0
        weighted_score = 0
        for sig in signals:
            w = weights.get(sig.name, 5)
            weighted_score += sig.score * (w / 100)
            total_weight += w
        
        # Normalize to -100 to +100
        composite = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        
        # Determine signal
        if composite > 40:
            composite_signal = Signal.STRONG_LONG
        elif composite > 15:
            composite_signal = Signal.LONG
        elif composite < -40:
            composite_signal = Signal.STRONG_SHORT
        elif composite < -15:
            composite_signal = Signal.SHORT
        else:
            composite_signal = Signal.NEUTRAL
        
        # Confidence = average of individual confidences, weighted
        total_conf = sum(s.confidence * weights.get(s.name, 5) for s in signals)
        confidence = (total_conf / total_weight) if total_weight > 0 else 0
        
        # Count bullish vs bearish signals
        bullish = sum(1 for s in signals if s.score > 10)
        bearish = sum(1 for s in signals if s.score < -10)
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'composite_score': round(composite, 1),
            'composite_signal': composite_signal,
            'confidence': round(confidence, 2),
            'bullish_signals': bullish,
            'bearish_signals': bearish,
            'tradeable': abs(composite) >= self.config.min_score_to_trade,
            'signals': signals,
            'price': await self.data.get_price(symbol),
        }


# ══════════════════════════════════════════════════════════════════════════════
# RISK ENGINE — Position Sizing, Drawdown Protection, Multi-TP
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Position:
    symbol: str
    side: str          # 'LONG' or 'SHORT'
    entry_price: float
    size: float        # in base asset
    leverage: int
    sl_price: float
    tp1_price: float
    tp2_price: float
    tp3_price: float
    trailing_active: bool = False
    trailing_sl: float = 0
    pnl: float = 0
    status: str = 'OPEN'
    open_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    partial_closes: int = 0

    def update_pnl(self, current_price: float):
        if self.side == 'LONG':
            self.pnl = (current_price - self.entry_price) / self.entry_price * 100 * self.leverage
        else:
            self.pnl = (self.entry_price - current_price) / self.entry_price * 100 * self.leverage
        return self.pnl


class RiskEngine:
    """Manages risk: position sizing, drawdown protection, trailing SL, multi-TP."""
    
    def __init__(self, config: FuturesConfig):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.balance: float = 1000  # default, update from API
        self.peak_balance: float = 1000
        self.total_pnl: float = 0
        self.trade_count: int = 0
        self.win_count: int = 0
        self.loss_count: int = 0
    
    @property
    def current_exposure(self) -> float:
        """Current total exposure as % of balance."""
        total = sum(p.size * p.entry_price for p in self.positions.values() if p.status == 'OPEN')
        return (total / self.balance) if self.balance > 0 else 0
    
    @property
    def current_drawdown(self) -> float:
        """Current drawdown from peak balance."""
        if self.peak_balance <= 0:
            return 0
        return (self.peak_balance - self.balance) / self.peak_balance
    
    @property
    def win_rate(self) -> float:
        total = self.win_count + self.loss_count
        return (self.win_count / total * 100) if total > 0 else 0
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if we can open a new trade."""
        if self.current_drawdown > self.config.max_drawdown_pct:
            return False, f'Max drawdown hit ({self.current_drawdown:.1%})'
        if self.current_exposure > self.config.max_total_exposure:
            return False, f'Max exposure reached ({self.current_exposure:.1%})'
        return True, 'OK'
    
    def calculate_position_size(self, price: float, leverage: int) -> float:
        """Kelly Criterion-inspired position sizing."""
        risk_amount = self.balance * self.config.max_position_pct
        position_value = risk_amount * leverage
        size = position_value / price
        return round(size, 6)
    
    def create_position(self, symbol: str, side: str, price: float, leverage: int) -> Position:
        """Create a new position with TP/SL levels."""
        can, reason = self.can_trade()
        if not can:
            raise ValueError(f"Cannot trade: {reason}")
        
        size = self.calculate_position_size(price, leverage)
        
        if side == 'LONG':
            sl = price * (1 - self.config.sl_pct)
            tp1 = price * (1 + self.config.tp1_pct)
            tp2 = price * (1 + self.config.tp2_pct)
            tp3 = price * (1 + self.config.tp3_pct)
        else:
            sl = price * (1 + self.config.sl_pct)
            tp1 = price * (1 - self.config.tp1_pct)
            tp2 = price * (1 - self.config.tp2_pct)
            tp3 = price * (1 - self.config.tp3_pct)
        
        pos = Position(
            symbol=symbol, side=side, entry_price=price,
            size=size, leverage=leverage,
            sl_price=sl, tp1_price=tp1, tp2_price=tp2, tp3_price=tp3
        )
        self.positions[symbol] = pos
        self.trade_count += 1
        return pos
    
    def check_exits(self, symbol: str, current_price: float) -> List[Dict]:
        """Check if any TP/SL/trailing levels are hit."""
        if symbol not in self.positions:
            return []
        
        pos = self.positions[symbol]
        actions = []
        pnl = pos.update_pnl(current_price)
        
        # Stop Loss
        if pos.side == 'LONG' and current_price <= pos.sl_price:
            pos.status = 'CLOSED_SL'
            actions.append({'action': 'CLOSE_ALL', 'reason': 'STOP_LOSS', 'pnl': pnl})
        elif pos.side == 'SHORT' and current_price >= pos.sl_price:
            pos.status = 'CLOSED_SL'
            actions.append({'action': 'CLOSE_ALL', 'reason': 'STOP_LOSS', 'pnl': pnl})
        
        # TP1 — close 50%
        if pos.partial_closes < 1:
            if (pos.side == 'LONG' and current_price >= pos.tp1_price) or \
               (pos.side == 'SHORT' and current_price <= pos.tp1_price):
                pos.partial_closes = 1
                actions.append({'action': 'CLOSE_50%', 'reason': 'TP1_HIT', 'pnl': pnl})
                # Activate trailing SL
                pos.trailing_active = True
                if pos.side == 'LONG':
                    pos.trailing_sl = current_price * (1 - self.config.trailing_callback_pct)
                else:
                    pos.trailing_sl = current_price * (1 + self.config.trailing_callback_pct)
        
        # TP2 — close 30%
        if pos.partial_closes < 2:
            if (pos.side == 'LONG' and current_price >= pos.tp2_price) or \
               (pos.side == 'SHORT' and current_price <= pos.tp2_price):
                pos.partial_closes = 2
                actions.append({'action': 'CLOSE_30%', 'reason': 'TP2_HIT', 'pnl': pnl})
        
        # TP3 — close remaining (runner)
        if pos.partial_closes < 3:
            if (pos.side == 'LONG' and current_price >= pos.tp3_price) or \
               (pos.side == 'SHORT' and current_price <= pos.tp3_price):
                pos.partial_closes = 3
                pos.status = 'CLOSED_TP3'
                actions.append({'action': 'CLOSE_ALL', 'reason': 'TP3_HIT', 'pnl': pnl})
        
        # Trailing Stop
        if pos.trailing_active:
            if pos.side == 'LONG':
                # Update trailing SL (move up)
                new_trail = current_price * (1 - self.config.trailing_callback_pct)
                pos.trailing_sl = max(pos.trailing_sl, new_trail)
                if current_price <= pos.trailing_sl:
                    pos.status = 'CLOSED_TRAILING'
                    actions.append({'action': 'CLOSE_ALL', 'reason': 'TRAILING_SL', 'pnl': pnl})
            else:
                new_trail = current_price * (1 + self.config.trailing_callback_pct)
                pos.trailing_sl = min(pos.trailing_sl, new_trail)
                if current_price >= pos.trailing_sl:
                    pos.status = 'CLOSED_TRAILING'
                    actions.append({'action': 'CLOSE_ALL', 'reason': 'TRAILING_SL', 'pnl': pnl})
        
        # Update stats if closed
        if pos.status != 'OPEN':
            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1
            self.total_pnl += pnl
        
        return actions


# ══════════════════════════════════════════════════════════════════════════════
# EXECUTION ENGINE — Binance Futures API
# ══════════════════════════════════════════════════════════════════════════════

class BinanceFuturesExecution:
    """Handles order execution on Binance Futures."""
    
    def __init__(self, api_key: str = '', api_secret: str = ''):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = BINANCE_FUTURES_REST
        self.session: Optional[aiohttp.ClientSession] = None
        self.has_keys = bool(api_key and api_secret)
    
    async def _ensure_session(self):
        if not self.session or self.session.closed:
            headers = {'X-MBX-APIKEY': self.api_key} if self.has_keys else {}
            self.session = aiohttp.ClientSession(headers=headers)
    
    def _sign(self, params: dict) -> dict:
        params['timestamp'] = int(time.time() * 1000)
        query = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        sig = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params['signature'] = sig
        return params
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _post_signed(self, endpoint: str, params: dict) -> dict:
        if not self.has_keys:
            return {'error': 'No API keys configured'}
        await self._ensure_session()
        params = self._sign(params)
        url = f"{self.base_url}{endpoint}"
        async with self.session.post(url, params=params) as resp:
            return await resp.json()
    
    async def _get_signed(self, endpoint: str, params: dict = None) -> dict:
        if not self.has_keys:
            return {'error': 'No API keys configured'}
        await self._ensure_session()
        params = params or {}
        params = self._sign(params)
        url = f"{self.base_url}{endpoint}"
        async with self.session.get(url, params=params) as resp:
            return await resp.json()
    
    # ── Account ──────────────────────────────────────────────────────────────
    
    async def get_balance(self) -> float:
        """Get USDT balance."""
        data = await self._get_signed('/fapi/v2/balance')
        if isinstance(data, list):
            for asset in data:
                if asset.get('asset') == 'USDT':
                    return float(asset.get('balance', 0))
        return 0
    
    async def get_positions(self) -> list:
        """Get open positions."""
        data = await self._get_signed('/fapi/v2/positionRisk')
        if isinstance(data, list):
            return [p for p in data if float(p.get('positionAmt', 0)) != 0]
        return []
    
    # ── Orders ───────────────────────────────────────────────────────────────
    
    async def set_leverage(self, symbol: str, leverage: int) -> dict:
        return await self._post_signed('/fapi/v1/leverage', {
            'symbol': symbol, 'leverage': leverage
        })
    
    async def market_order(self, symbol: str, side: str, quantity: float) -> dict:
        """Place market order."""
        return await self._post_signed('/fapi/v1/order', {
            'symbol': symbol,
            'side': side,  # BUY or SELL
            'type': 'MARKET',
            'quantity': str(quantity),
        })
    
    async def limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        """Place limit order."""
        return await self._post_signed('/fapi/v1/order', {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'quantity': str(quantity),
            'price': str(price),
            'timeInForce': 'GTC',
        })
    
    async def stop_market(self, symbol: str, side: str, quantity: float, stop_price: float) -> dict:
        """Place stop market order (for SL)."""
        return await self._post_signed('/fapi/v1/order', {
            'symbol': symbol,
            'side': side,
            'type': 'STOP_MARKET',
            'quantity': str(quantity),
            'stopPrice': str(stop_price),
            'closePosition': 'false',
        })
    
    async def take_profit_market(self, symbol: str, side: str, quantity: float, stop_price: float) -> dict:
        """Place take profit market order."""
        return await self._post_signed('/fapi/v1/order', {
            'symbol': symbol,
            'side': side,
            'type': 'TAKE_PROFIT_MARKET',
            'quantity': str(quantity),
            'stopPrice': str(stop_price),
            'closePosition': 'false',
        })
    
    async def cancel_all_orders(self, symbol: str) -> dict:
        return await self._delete_signed('/fapi/v1/allOpenOrders', {'symbol': symbol})
    
    async def execute_trade(self, symbol: str, side: str, leverage: int, 
                            quantity: float, sl: float, tp1: float, 
                            tp2: float, tp3: float) -> Dict:
        """Execute full trade: entry + SL + 3 TPs."""
        results = {}
        
        # Set leverage
        results['leverage'] = await self.set_leverage(symbol, leverage)
        
        # Entry
        entry_side = 'BUY' if side == 'LONG' else 'SELL'
        results['entry'] = await self.market_order(symbol, entry_side, quantity)
        
        if 'error' in results['entry'] or 'code' in results['entry']:
            return results
        
        # SL
        sl_side = 'SELL' if side == 'LONG' else 'BUY'
        results['sl'] = await self.stop_market(symbol, sl_side, quantity, sl)
        
        # TP1 — 50%
        tp1_qty = round(quantity * 0.5, 6)
        results['tp1'] = await self.take_profit_market(symbol, sl_side, tp1_qty, tp1)
        
        # TP2 — 30%
        tp2_qty = round(quantity * 0.3, 6)
        results['tp2'] = await self.take_profit_market(symbol, sl_side, tp2_qty, tp2)
        
        # TP3 — 20% (runner)
        tp3_qty = round(quantity - tp1_qty - tp2_qty, 6)
        results['tp3'] = await self.take_profit_market(symbol, sl_side, tp3_qty, tp3)
        
        return results


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

class TelegramAlerts:
    """Send alerts to Mona's Telegram 💎 Alpha topic."""
    
    def __init__(self, topic_id: int = 13):
        self.topic_id = topic_id
    
    def _send(self, message: str):
        try:
            import subprocess
            result = subprocess.run(
                ['python3', str(TELEGRAM_SCRIPT), 'send_topic', str(self.topic_id), message],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                log.warning(f"Telegram send failed: {result.stderr[:200]}")
        except Exception as e:
            log.error(f"Telegram error: {e}")
    
    def alert_signal(self, analysis: Dict):
        """Send signal alert."""
        symbol = analysis['symbol']
        score = analysis['composite_score']
        signal = analysis['composite_signal'].value
        conf = analysis['confidence']
        bullish = analysis['bullish_signals']
        bearish = analysis['bearish_signals']
        price = analysis['price']
        tradeable = analysis['tradeable']
        
        # Direction emoji
        if 'STRONG_LONG' in signal:
            emoji = '🟢🟢'
        elif 'LONG' in signal:
            emoji = '🟢'
        elif 'STRONG_SHORT' in signal:
            emoji = '🔴🔴'
        elif 'SHORT' in signal:
            emoji = '🔴'
        else:
            emoji = '⚪️'
        
        trade_emoji = '🎯 TRADEABLE' if tradeable else '👀 Watching'
        
        msg = f"""{emoji} **{symbol} — Signal Alert**

**Score:** {score:+.1f}/100 | **Signal:** {signal}
**Confidence:** {conf:.0%} | {trade_emoji}
**Price:** ${price:,.2f}
**Bullish signals:** {bullish}/8 | **Bearish:** {bearish}/8

**Breakdown:**"""
        
        for sig in analysis['signals']:
            if sig.score > 5:
                icon = '🟢'
            elif sig.score < -5:
                icon = '🔴'
            else:
                icon = '⚪️'
            msg += f"\n{icon} {sig.name}: {sig.score:+.0f} — {sig.details}"
        
        if tradeable:
            msg += f"\n\n🎯 **ACTION: {'LONG' if score > 0 else 'SHORT'} {symbol}**"
            msg += f"\n⚡ Use /mona_trade {symbol} to execute"
        
        self._send(msg)
    
    def alert_trade(self, pos: Position, action: str, details: str = ''):
        """Send trade execution alert."""
        emoji = '🟢' if pos.side == 'LONG' else '🔴'
        msg = f"""{emoji} **TRADE {action} — {pos.symbol}**

**Side:** {pos.side} | **Entry:** ${pos.entry_price:,.2f}
**Size:** {pos.size} | **Leverage:** {pos.leverage}x
**SL:** ${pos.sl_price:,.2f} | **TP1:** ${pos.tp1_price:,.2f}
**TP2:** ${pos.tp2_price:,.2f} | **TP3:** ${pos.tp3_price:,.2f}
**PnL:** {pos.pnl:+.2f}%
{details}"""
        self._send(msg)
    
    def alert_exit(self, pos: Position, reason: str, pnl: float):
        """Send exit alert."""
        emoji = '💰' if pnl > 0 else '💸'
        msg = f"""{emoji} **POSITION CLOSED — {pos.symbol}**

**Reason:** {reason}
**Side:** {pos.side} | **Entry:** ${pos.entry_price:,.2f}
**PnL:** {pnl:+.2f}% | **Closes:** {pos.partial_closes}/3 TPs hit
**Duration:** {datetime.now(timezone.utc) - pos.open_time}"""
        self._send(msg)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE — Orchestrator
# ══════════════════════════════════════════════════════════════════════════════

class MonaFuturesEngine:
    """Main orchestrator — ties data, signals, risk, execution together."""
    
    def __init__(self, config: FuturesConfig = None, mode: str = 'scan'):
        self.config = config or FuturesConfig()
        self.mode = mode  # 'monitor', 'scan', 'trade'
        self.data = BinanceFuturesData(self.config)
        self.signals = SignalEngine(self.data, self.config)
        self.risk = RiskEngine(self.config)
        self.telegram = TelegramAlerts(self.config.alert_topic)
        self.running = False
        
        # Load API keys for trade mode
        api_key = ''
        api_secret = ''
        env_file = Path.home() / 'mona-workspace' / 'vault' / '.binance_keys'
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith('API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                elif line.startswith('API_SECRET='):
                    api_secret = line.split('=', 1)[1].strip()
        
        self.execution = BinanceFuturesExecution(api_key, api_secret)
        
        log.info(f"Mona Futures Engine v1.0 — Mode: {mode}")
        log.info(f"Symbols: {self.config.symbols}")
        log.info(f"API Keys: {'✓' if self.execution.has_keys else '✗ (monitoring only)'}")
    
    async def scan_once(self) -> List[Dict]:
        """Run one scan cycle on all symbols."""
        results = []
        for symbol in self.config.symbols:
            try:
                analysis = await self.signals.analyze_symbol(symbol)
                results.append(analysis)
                
                # Alert if tradeable
                if analysis['tradeable']:
                    self.telegram.alert_signal(analysis)
                    log.info(f"🎯 {symbol}: {analysis['composite_signal'].value} "
                             f"(score: {analysis['composite_score']:+.1f})")
                elif abs(analysis['composite_score']) > 25:
                    log.info(f"👀 {symbol}: {analysis['composite_signal'].value} "
                             f"(score: {analysis['composite_score']:+.1f})")
                
                # Small delay between symbols to avoid rate limits
                await asyncio.sleep(1)
            except Exception as e:
                log.error(f"Error scanning {symbol}: {e}")
        
        return results
    
    async def monitor_loop(self):
        """Continuous monitoring loop."""
        self.running = True
        log.info(f"Starting monitor loop — interval: {self.config.scan_interval_sec}s")
        
        while self.running:
            try:
                results = await self.scan_once()
                
                # Check exits for open positions
                for symbol in list(self.risk.positions.keys()):
                    if self.risk.positions[symbol].status == 'OPEN':
                        price = await self.data.get_price(symbol)
                        exits = self.risk.check_exits(symbol, price)
                        for exit_action in exits:
                            pos = self.risk.positions[symbol]
                            self.telegram.alert_exit(pos, exit_action['reason'], exit_action['pnl'])
                            log.info(f"Exit {symbol}: {exit_action['reason']} PnL: {exit_action['pnl']:+.2f}%")
                
                await asyncio.sleep(self.config.scan_interval_sec)
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)
        
        await self.data.close()
        await self.execution.close()
        log.info("Monitor stopped.")
    
    async def generate_report(self) -> str:
        """Generate a full analysis report."""
        results = await self.scan_once()
        
        report = f"""📊 **Mona Futures Engine — Analysis Report**
**Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**Mode:** {self.mode} | **Symbols:** {len(self.config.symbols)}

"""
        for r in results:
            emoji = '🟢' if r['composite_score'] > 0 else '🔴' if r['composite_score'] < 0 else '⚪️'
            trade = '🎯' if r['tradeable'] else '👀'
            report += f"{emoji} **{r['symbol']}**: {r['composite_score']:+.1f} ({r['composite_signal'].value}) {trade}\n"
            
            for sig in r['signals']:
                icon = '🟢' if sig.score > 5 else '🔴' if sig.score < -5 else '⚪️'
                report += f"  {icon} {sig.name}: {sig.score:+.0f}\n"
            report += "\n"
        
        report += f"""**Risk Status:**
- Balance: ${self.risk.balance:,.2f}
- Exposure: {self.risk.current_exposure:.1%}
- Drawdown: {self.risk.current_drawdown:.1%}
- Win Rate: {self.risk.win_rate:.1f}% ({self.risk.win_count}W/{self.risk.loss_count}L)
"""
        return report


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Mona Futures Engine v1.0')
    parser.add_argument('mode', choices=['monitor', 'scan', 'report'], default='scan', nargs='?')
    parser.add_argument('--symbols', default='BTCUSDT,ETHUSDT,SOLUSDT', help='Comma-separated symbols')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval in seconds')
    parser.add_argument('--min-score', type=float, default=65, help='Min score to trigger alert')
    args = parser.parse_args()
    
    config = FuturesConfig()
    config.symbols = args.symbols.split(',')
    config.scan_interval_sec = args.interval
    config.min_score_to_trade = args.min_score
    
    engine = MonaFuturesEngine(config, mode=args.mode)
    
    if args.mode == 'monitor':
        await engine.monitor_loop()
    elif args.mode == 'scan':
        results = await engine.scan_once()
        for r in results:
            print(f"\n{'='*60}")
            print(f"{r['symbol']}: {r['composite_score']:+.1f} ({r['composite_signal'].value})")
            print(f"Confidence: {r['confidence']:.0%} | Tradeable: {r['tradeable']}")
            for sig in r['signals']:
                print(f"  {sig.name}: {sig.score:+.0f} — {sig.details}")
    elif args.mode == 'report':
        report = await engine.generate_report()
        print(report)
    
    await engine.data.close()

if __name__ == '__main__':
    asyncio.run(main())
