"""
Chart Generator Module
Creates interactive charts using Plotly with EMA 20/50/200 alert system
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates interactive stock charts with EMA alert system"""
    
    def __init__(self, data: pd.DataFrame, symbol: str):
        if data.empty:
            logger.warning(f"Empty data provided for chart generation: {symbol}")
        
        self.data = data.copy()
        self.symbol = symbol.upper()
        self._calculate_emas()
        self._detect_alerts()
    
    def _calculate_emas(self):
        """Calculate EMA 20, 50, 200 if not present"""
        if 'EMA_20' not in self.data.columns:
            self.data['EMA_20'] = self.data['Close'].ewm(span=20, adjust=False).mean()
        if 'EMA_50' not in self.data.columns:
            self.data['EMA_50'] = self.data['Close'].ewm(span=50, adjust=False).mean()
        if 'EMA_200' not in self.data.columns:
            self.data['EMA_200'] = self.data['Close'].ewm(span=200, adjust=False).mean()
    
    def _detect_alerts(self) -> Dict:
        """Detect EMA crossover/crossunder alerts"""
        alerts = {
            'ema200_cross_above': False,
            'ema200_cross_below': False,
            'ema50_cross_above': False,
            'ema50_cross_below': False,
            'ema20_cross_above': False,
            'ema20_cross_below': False
        }
        
        if len(self.data) < 2:
            return alerts
        
        try:
            close = self.data['Close']
            ema20 = self.data['EMA_20']
            ema50 = self.data['EMA_50']
            ema200 = self.data['EMA_200']
            
            # Check latest 5 bars for crossovers
            for i in range(max(1, len(self.data) - 5), len(self.data)):
                if i == 0:
                    continue
                
                # EMA 200 crossovers
                if pd.notna(ema200.iloc[i]) and pd.notna(ema200.iloc[i-1]):
                    if close.iloc[i-1] <= ema200.iloc[i-1] and close.iloc[i] > ema200.iloc[i]:
                        alerts['ema200_cross_above'] = True
                    elif close.iloc[i-1] >= ema200.iloc[i-1] and close.iloc[i] < ema200.iloc[i]:
                        alerts['ema200_cross_below'] = True
                
                # EMA 50 crossovers
                if pd.notna(ema50.iloc[i]) and pd.notna(ema50.iloc[i-1]):
                    if close.iloc[i-1] <= ema50.iloc[i-1] and close.iloc[i] > ema50.iloc[i]:
                        alerts['ema50_cross_above'] = True
                    elif close.iloc[i-1] >= ema50.iloc[i-1] and close.iloc[i] < ema50.iloc[i]:
                        alerts['ema50_cross_below'] = True
                
                # EMA 20 crossovers
                if pd.notna(ema20.iloc[i]) and pd.notna(ema20.iloc[i-1]):
                    if close.iloc[i-1] <= ema20.iloc[i-1] and close.iloc[i] > ema20.iloc[i]:
                        alerts['ema20_cross_above'] = True
                    elif close.iloc[i-1] >= ema20.iloc[i-1] and close.iloc[i] < ema20.iloc[i]:
                        alerts['ema20_cross_below'] = True
        
        except Exception as e:
            logger.error(f"Error detecting EMA alerts: {e}")
        
        return alerts
    
    def get_ema_alerts(self) -> Dict:
        """Get current EMA alert status"""
        return self._detect_alerts()
    
    def create_main_chart(self, show_indicators: bool = True, interval: str = "1d") -> go.Figure:
        """Create comprehensive trading chart with all indicators for swing and long-term traders"""
        if self.data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for chart",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        try:
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in self.data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Create subplots: Price, Volume, RSI, MACD/Stochastic
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,
                subplot_titles=(
                    f'{self.symbol} - Price Chart (EMA 20/50/200, VWAP, Bollinger Bands)',
                    'Volume',
                    'RSI & Stochastic Oscillator',
                    'MACD'
                ),
                row_heights=[0.5, 0.15, 0.175, 0.175]
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=self.data.index,
                    open=self.data['Open'],
                    high=self.data['High'],
                    low=self.data['Low'],
                    close=self.data['Close'],
                    name='Price',
                    increasing_line_color='#10b981',
                    decreasing_line_color='#ef4444'
                ),
                row=1, col=1
            )
            
            if show_indicators:
                # EMA 20 - Green, thin line
                ema20 = self.data['EMA_20'].dropna()
                if not ema20.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=ema20.index,
                            y=ema20.values,
                            name='EMA 20',
                            line=dict(color='#10b981', width=1.5),
                            hovertemplate='EMA 20: $%{y:.2f}<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # EMA 50 - Blue, medium line
                ema50 = self.data['EMA_50'].dropna()
                if not ema50.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=ema50.index,
                            y=ema50.values,
                            name='EMA 50',
                            line=dict(color='#3b82f6', width=2),
                            hovertemplate='EMA 50: $%{y:.2f}<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # EMA 200 - Red/Orange, thick line
                ema200 = self.data['EMA_200'].dropna()
                if not ema200.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=ema200.index,
                            y=ema200.values,
                            name='EMA 200',
                            line=dict(color='#f59e0b', width=2.5),
                            hovertemplate='EMA 200: $%{y:.2f}<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # VWAP (Volume Weighted Average Price) - Important for intraday trading
                if 'VWAP' in self.data.columns:
                    vwap = self.data['VWAP'].dropna()
                    if not vwap.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=vwap.index,
                                y=vwap.values,
                                name='VWAP',
                                line=dict(color='#8b5cf6', width=2, dash='dot'),
                                hovertemplate='VWAP: $%{y:.2f}<extra></extra>'
                        ),
                        row=1, col=1
                    )
                
                # Bollinger Bands
                if all(col in self.data.columns for col in ['BB_high', 'BB_low', 'BB_mid']):
                    bb_high = self.data['BB_high'].dropna()
                    bb_low = self.data['BB_low'].dropna()
                    bb_mid = self.data['BB_mid'].dropna()
                    
                    if not bb_high.empty and not bb_low.empty:
                        # Upper band
                        fig.add_trace(
                            go.Scatter(
                                x=bb_high.index,
                                y=bb_high.values,
                                name='BB Upper',
                                line=dict(color='rgba(148, 163, 184, 0.6)', width=1, dash='dash'),
                                showlegend=False,
                                hovertemplate='BB Upper: $%{y:.2f}<extra></extra>'
                            ),
                            row=1, col=1
                        )
                        # Lower band with fill
                        fig.add_trace(
                            go.Scatter(
                                x=bb_low.index,
                                y=bb_low.values,
                                name='BB Lower',
                                line=dict(color='rgba(148, 163, 184, 0.6)', width=1, dash='dash'),
                                fill='tonexty',
                                fillcolor='rgba(148, 163, 184, 0.1)',
                                showlegend=False,
                                hovertemplate='BB Lower: $%{y:.2f}<extra></extra>'
                            ),
                            row=1, col=1
                        )
                        # Middle band
                        if not bb_mid.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=bb_mid.index,
                                    y=bb_mid.values,
                                    name='BB Mid',
                                    line=dict(color='rgba(148, 163, 184, 0.4)', width=1),
                                    showlegend=False,
                                    hovertemplate='BB Mid: $%{y:.2f}<extra></extra>'
                                ),
                                row=1, col=1
                            )
                
                # Support/Resistance levels (simplified - using recent highs/lows)
                if len(self.data) >= 20:
                    recent_high = self.data['High'].tail(20).max()
                    recent_low = self.data['Low'].tail(20).min()
                    current_price = self.data['Close'].iloc[-1]
                    
                    # Resistance level
                    if recent_high > current_price * 1.02:
                        fig.add_hline(
                            y=recent_high,
                            line_dash="dot",
                            line_color="red",
                            annotation_text=f"Resistance: ${recent_high:.2f}",
                            annotation_position="right",
                            row=1,
                            col=1
                        )
                    
                    # Support level
                    if recent_low < current_price * 0.98:
                        fig.add_hline(
                            y=recent_low,
                            line_dash="dot",
                            line_color="green",
                            annotation_text=f"Support: ${recent_low:.2f}",
                            annotation_position="right",
                            row=1,
                            col=1
                        )
            
            # Volume
            if 'Volume' in self.data.columns:
                colors = []
                for i in range(len(self.data)):
                    if i > 0:
                        colors.append(
                            'red' if self.data['Close'].iloc[i] < self.data['Close'].iloc[i-1] 
                            else 'green'
                        )
                    else:
                        colors.append('gray')
                
                fig.add_trace(
                    go.Bar(
                        x=self.data.index,
                        y=self.data['Volume'],
                        name='Volume',
                        marker_color=colors,
                        opacity=0.7
                    ),
                    row=2, col=1
                )
            
            # RSI in separate panel
            if 'RSI' in self.data.columns:
                rsi = self.data['RSI'].dropna()
                if not rsi.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=rsi.index,
                            y=rsi.values,
                            name='RSI',
                            line=dict(color='#3b82f6', width=2),
                            hovertemplate='RSI: %{y:.2f}<extra></extra>'
                        ),
                        row=3, col=1
                    )
                    # RSI levels
                    fig.add_hline(
                        y=70,
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Overbought (70)",
                        row=3,
                        col=1
                    )
                    fig.add_hline(
                        y=30,
                        line_dash="dash",
                        line_color="green",
                        annotation_text="Oversold (30)",
                        row=3,
                        col=1
                    )
            
            # Stochastic Oscillator (in same panel as RSI)
            if 'Stoch_K' in self.data.columns and 'Stoch_D' in self.data.columns:
                stoch_k = self.data['Stoch_K'].dropna()
                stoch_d = self.data['Stoch_D'].dropna()
                
                if not stoch_k.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=stoch_k.index,
                            y=stoch_k.values,
                            name='Stochastic %K',
                            line=dict(color='#8b5cf6', width=2),
                            hovertemplate='Stoch %K: %{y:.2f}<extra></extra>'
                        ),
                        row=3, col=1
                    )
                
                if not stoch_d.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=stoch_d.index,
                            y=stoch_d.values,
                            name='Stochastic %D',
                            line=dict(color='#f59e0b', width=2),
                            hovertemplate='Stoch %D: %{y:.2f}<extra></extra>'
                        ),
                        row=3, col=1
                    )
                
                # Stochastic levels
                fig.add_hline(y=80, line_dash="dot", line_color="rgba(255,0,0,0.3)", row=3, col=1)
                fig.add_hline(y=20, line_dash="dot", line_color="rgba(0,255,0,0.3)", row=3, col=1)
            
            # MACD in separate panel
            if 'MACD' in self.data.columns and 'MACD_signal' in self.data.columns:
                macd = self.data['MACD'].dropna()
                macd_signal = self.data['MACD_signal'].dropna()
                macd_diff = self.data['MACD_diff'].dropna() if 'MACD_diff' in self.data.columns else pd.Series()
                
                if not macd.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=macd.index,
                            y=macd.values,
                            name='MACD',
                            line=dict(color='#3b82f6', width=2),
                            hovertemplate='MACD: %{y:.2f}<extra></extra>'
                        ),
                        row=4, col=1
                    )
                
                if not macd_signal.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=macd_signal.index,
                            y=macd_signal.values,
                            name='MACD Signal',
                            line=dict(color='#f59e0b', width=2),
                            hovertemplate='MACD Signal: %{y:.2f}<extra></extra>'
                        ),
                        row=4, col=1
                    )
                
                # MACD Histogram (difference)
                if not macd_diff.empty:
                    colors_hist = ['green' if val >= 0 else 'red' for val in macd_diff.values]
                    fig.add_trace(
                        go.Bar(
                            x=macd_diff.index,
                            y=macd_diff.values,
                            name='MACD Histogram',
                            marker_color=colors_hist,
                            opacity=0.6,
                            hovertemplate='MACD Hist: %{y:.2f}<extra></extra>'
                        ),
                        row=4, col=1
                    )
                
                # Zero line for MACD
                fig.add_hline(y=0, line_dash="dash", line_color="gray", row=4, col=1)
            
            # Update layout
            fig.update_layout(
                title=f'{self.symbol} - Comprehensive Trading Chart (Swing & Long-Term)',
                xaxis_rangeslider_visible=False,
                height=1000,
                showlegend=True,
                hovermode='x unified',
                template='plotly_white',
                margin=dict(l=60, r=50, t=100, b=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10)
                )
            )
            
            fig.update_xaxes(title_text="Date/Time", row=4, col=1)
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            fig.update_yaxes(title_text="RSI / Stochastic (0-100)", row=3, col=1, range=[0, 100])
            fig.update_yaxes(title_text="MACD", row=4, col=1)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating chart for {self.symbol}: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def create_comparison_chart(self, data_1h: pd.DataFrame, data_1d: pd.DataFrame) -> go.Figure:
        """Create side-by-side comparison chart (1h vs 1 day)"""
        try:
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f'{self.symbol} - 1 Hour Chart', f'{self.symbol} - 1 Day Chart'),
                horizontal_spacing=0.1
            )
            
            # 1 Hour Chart (Left)
            if not data_1h.empty:
                fig.add_trace(
                    go.Candlestick(
                        x=data_1h.index,
                        open=data_1h['Open'],
                        high=data_1h['High'],
                        low=data_1h['Low'],
                        close=data_1h['Close'],
                        name='1H Price',
                        increasing_line_color='#10b981',
                        decreasing_line_color='#ef4444',
                        showlegend=False
                    ),
                    row=1, col=1
                )
                
                # Add EMAs for 1h
                if 'EMA_20' in data_1h.columns:
                    ema20_1h = data_1h['EMA_20'].dropna()
                    if not ema20_1h.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=ema20_1h.index,
                                y=ema20_1h.values,
                                name='EMA 20 (1H)',
                                line=dict(color='#10b981', width=1),
                                showlegend=True
                            ),
                            row=1, col=1
                        )
                
                if 'EMA_50' in data_1h.columns:
                    ema50_1h = data_1h['EMA_50'].dropna()
                    if not ema50_1h.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=ema50_1h.index,
                                y=ema50_1h.values,
                                name='EMA 50 (1H)',
                                line=dict(color='#3b82f6', width=2),
                                showlegend=True
                            ),
                            row=1, col=1
                        )
                
                if 'EMA_200' in data_1h.columns:
                    ema200_1h = data_1h['EMA_200'].dropna()
                    if not ema200_1h.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=ema200_1h.index,
                                y=ema200_1h.values,
                                name='EMA 200 (1H)',
                                line=dict(color='#ef4444', width=3),
                                showlegend=True
                            ),
                            row=1, col=1
                        )
            
            # 1 Day Chart (Right)
            if not data_1d.empty:
                fig.add_trace(
                    go.Candlestick(
                        x=data_1d.index,
                        open=data_1d['Open'],
                        high=data_1d['High'],
                        low=data_1d['Low'],
                        close=data_1d['Close'],
                        name='1D Price',
                        increasing_line_color='#10b981',
                        decreasing_line_color='#ef4444',
                        showlegend=False
                    ),
                    row=1, col=2
                )
                
                # Add EMAs for 1d
                if 'EMA_20' in data_1d.columns:
                    ema20_1d = data_1d['EMA_20'].dropna()
                    if not ema20_1d.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=ema20_1d.index,
                                y=ema20_1d.values,
                                name='EMA 20 (1D)',
                                line=dict(color='#10b981', width=1),
                                showlegend=True
                            ),
                            row=1, col=2
                        )
                
                if 'EMA_50' in data_1d.columns:
                    ema50_1d = data_1d['EMA_50'].dropna()
                    if not ema50_1d.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=ema50_1d.index,
                                y=ema50_1d.values,
                                name='EMA 50 (1D)',
                                line=dict(color='#3b82f6', width=2),
                                showlegend=True
                            ),
                            row=1, col=2
                        )
                
                if 'EMA_200' in data_1d.columns:
                    ema200_1d = data_1d['EMA_200'].dropna()
                    if not ema200_1d.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=ema200_1d.index,
                                y=ema200_1d.values,
                                name='EMA 200 (1D)',
                                line=dict(color='#ef4444', width=3),
                                showlegend=True
                            ),
                            row=1, col=2
                        )
            
            fig.update_layout(
                title=f'{self.symbol} - 1 Hour vs 1 Day Comparison',
                height=600,
                showlegend=True,
                hovermode='x unified',
                template='plotly_white',
                margin=dict(l=50, r=50, t=80, b=50),
                xaxis_rangeslider_visible=False,
                xaxis2_rangeslider_visible=False
            )
            
            fig.update_xaxes(title_text="Time (1H)", row=1, col=1)
            fig.update_xaxes(title_text="Date (1D)", row=1, col=2)
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Price ($)", row=1, col=2)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating comparison chart: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating comparison chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
