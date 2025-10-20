import React, { useState, useEffect, useRef } from 'react';

const MaterialIcon = ({ children, style = {} }) => (
  <span style={{ fontFamily: 'Material Symbols Outlined', fontWeight: 300, fontSize: '20px', ...style }}>
    {children}
  </span>
);

const generatePremarketData = () => {
  const stocks = [
    { symbol: 'TSLA', score: 87.3, volatility: 4.2, momentum: 2.1, volume: '1.8M', risk: 'conservative', confidence: 89, avg: 245.30, high: 268.50, low: 228.10, stdDev: 2.1 },
    { symbol: 'NVDA', score: 85.1, volatility: 3.8, momentum: 1.9, volume: '1.6M', risk: 'moderate', confidence: 86, avg: 485.20, high: 512.30, low: 461.80, stdDev: 3.2 },
    { symbol: 'AAPL', score: 82.7, volatility: 2.9, momentum: 1.5, volume: '1.4M', risk: 'aggressive', confidence: 83, avg: 178.50, high: 189.20, low: 171.30, stdDev: 4.5 },
    { symbol: 'MSFT', score: 80.2, volatility: 2.5, momentum: 1.3, volume: '1.3M', risk: 'moderate', confidence: 81, avg: 412.80, high: 425.50, low: 398.20, stdDev: 2.8 },
    { symbol: 'AMD', score: 78.8, volatility: 3.5, momentum: 1.8, volume: '1.5M', risk: 'aggressive', confidence: 78, avg: 152.30, high: 168.90, low: 145.20, stdDev: 5.1 },
    { symbol: 'GOOGL', score: 76.4, volatility: 3.1, momentum: 1.4, volume: '1.2M', risk: 'moderate', confidence: 75, avg: 142.60, high: 151.20, low: 137.80, stdDev: 3.4 },
    { symbol: 'META', score: 74.2, volatility: 3.8, momentum: 1.7, volume: '1.4M', risk: 'aggressive', confidence: 72, avg: 485.70, high: 502.30, low: 471.20, stdDev: 4.2 },
    { symbol: 'AMZN', score: 72.5, volatility: 2.7, momentum: 1.2, volume: '1.3M', risk: 'conservative', confidence: 70, avg: 178.90, high: 186.40, low: 173.50, stdDev: 2.3 }
  ];
  return stocks;
};

const getMarketProgress = () => {
  const now = new Date();
  const marketOpen = new Date(now);
  marketOpen.setHours(9, 30, 0, 0);
  const marketClose = new Date(now);
  marketClose.setHours(16, 0, 0, 0);
  
  if (now < marketOpen) return { percent: 0, status: 'Pre-market' };
  if (now > marketClose) return { percent: 100, status: 'After-hours' };
  
  const totalMs = marketClose - marketOpen;
  const elapsedMs = now - marketOpen;
  const percent = (elapsedMs / totalMs) * 100;
  
  return { percent: Math.min(100, Math.max(0, percent)), status: 'Open' };
};

const StockSymbolButton = ({ stock }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipStyle, setTooltipStyle] = useState({});
  const buttonRef = useRef(null);
  
  const riskColors = {
    conservative: '#2c3e50',
    moderate: '#5b7a9c',
    aggressive: '#8fa8c4'
  };
  
  const riskLabels = {
    conservative: 'Conservative',
    moderate: 'Moderate',
    aggressive: 'Aggressive'
  };
  
  const handleClick = (e) => {
    e.stopPropagation();
    
    if (!showTooltip && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const tooltipWidth = 200;
      const tooltipHeight = 140;
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      
      // Default: below the button
      let top = rect.bottom + 8;
      let left = rect.left + (rect.width / 2) - (tooltipWidth / 2);
      
      // If would go off right edge, align to right
      if (left + tooltipWidth > viewportWidth - 10) {
        left = viewportWidth - tooltipWidth - 10;
      }
      
      // If would go off left edge (or covered by sidebar), align to left
      if (left < 240) {
        left = rect.right + 8;
        top = rect.top;
      }
      
      // If would go off bottom, place above
      if (top + tooltipHeight > viewportHeight - 10) {
        top = rect.top - tooltipHeight - 8;
      }
      
      setTooltipStyle({
        position: 'fixed',
        top: `${top}px`,
        left: `${left}px`,
        width: '200px',
        background: '#3d3d3a',
        color: '#fff',
        borderRadius: '8px',
        padding: '10px',
        fontSize: '11px',
        zIndex: 1000,
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
      });
    }
    
    setShowTooltip(!showTooltip);
  };
  
  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        ref={buttonRef}
        onClick={handleClick}
        style={{
          padding: '3px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: 600,
          border: 'none',
          cursor: 'pointer',
          background: riskColors[stock.risk],
          color: '#fff'
        }}
      >
        {stock.symbol}
      </button>
      {showTooltip && (
        <>
          <div
            onClick={(e) => {
              e.stopPropagation();
              setShowTooltip(false);
            }}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 999
            }}
          />
          <div
            style={tooltipStyle}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ fontWeight: 600, marginBottom: '8px', fontSize: '12px' }}>
              {stock.symbol} - {riskLabels[stock.risk]}
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '8px',
              fontSize: '11px'
            }}>
              <div>
                <div style={{ fontSize: '9px', color: '#b0b0b0', marginBottom: '2px' }}>20-Day Avg</div>
                <div style={{ fontWeight: 600 }}>${stock.avg}</div>
              </div>
              <div>
                <div style={{ fontSize: '9px', color: '#b0b0b0', marginBottom: '2px' }}>Std Dev</div>
                <div style={{ fontWeight: 600 }}>{stock.stdDev}%</div>
              </div>
              <div>
                <div style={{ fontSize: '9px', color: '#b0b0b0', marginBottom: '2px' }}>High</div>
                <div style={{ fontWeight: 600, color: '#5dcc7c' }}>${stock.high}</div>
              </div>
              <div>
                <div style={{ fontSize: '9px', color: '#b0b0b0', marginBottom: '2px' }}>Low</div>
                <div style={{ fontWeight: 600, color: '#ff6b6b' }}>${stock.low}</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default function TradingDashboard() {
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState('premarket');
  const [premarketData] = useState(generatePremarketData());
  const [marketProgress, setMarketProgress] = useState(getMarketProgress());
  
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketProgress(getMarketProgress());
    }, 60000);
    return () => clearInterval(interval);
  }, []);
  
  const navItems = [
    { id: 'premarket', icon: 'bar_chart', label: 'Forecast' },
    { id: 'live', icon: 'show_chart', label: 'Live' },
    { id: 'report', icon: 'description', label: 'Report' },
    { id: 'settings', icon: 'settings', label: 'Settings' }
  ];
  
  const titles = {
    premarket: { title: 'Premarket Forecast', subtitle: '20-day historical analysis' },
    live: { title: 'Live Monitor', subtitle: 'Real-time position tracking' },
    report: { title: 'Daily Report', subtitle: 'Performance summary' },
    settings: { title: 'Settings', subtitle: 'Configure your trading preferences' }
  };
  
  const dataCards = [
    { label: 'Total Positions', value: '8' },
    { label: 'Avg Score', value: '82.4' },
    { label: 'High Confidence', value: '6' },
    { label: 'Volatility Avg', value: '3.2%' },
    { label: 'Momentum Score', value: '1.8' },
    { label: 'Volume (Total)', value: '12.4M' },
    { label: 'Conservative', value: '3' },
    { label: 'Aggressive', value: '2' }
  ];
  
  return (
    <>
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,300,0,0" />
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto+Flex:wght@400;500;600;700&display=swap" />
      
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; font-family: 'Roboto Flex', -apple-system, sans-serif; }
      `}</style>
      
      <div style={{ display: 'flex', height: '100vh', background: '#faf9f5' }}>
        {/* Sidebar */}
        <aside style={{
          width: sidebarExpanded ? '220px' : '56px',
          background: sidebarExpanded ? '#f5f4ed' : '#faf9f5',
          borderRight: '1px solid #CFC9C1',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.3s ease, background 0.3s ease'
        }}>
          {/* Logo Section */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px',
            minHeight: '64px'
          }}>
            <div 
              onClick={() => !sidebarExpanded && setSidebarExpanded(true)}
              style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
            >
              <MaterialIcon style={{ color: '#D87757', fontSize: '24px' }}>
                {sidebarExpanded ? 'train' : 'view_sidebar'}
              </MaterialIcon>
              {sidebarExpanded && (
                <span style={{ color: '#3d3d3a', fontSize: '16px', fontWeight: 600 }}>
                  LRBFund
                </span>
              )}
            </div>
            {sidebarExpanded && (
              <button
                onClick={() => setSidebarExpanded(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex'
                }}
              >
                <MaterialIcon style={{ color: '#3d3d3a' }}>chevron_left</MaterialIcon>
              </button>
            )}
          </div>
          
          {/* Market Progress */}
          {sidebarExpanded && (
            <div style={{ padding: '0 12px 12px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '11px',
                color: '#3d3d3a',
                marginBottom: '4px'
              }}>
                <span>{marketProgress.status}</span>
                <span>{marketProgress.percent.toFixed(0)}%</span>
              </div>
              <div style={{
                height: '3px',
                background: '#e6e1dd',
                borderRadius: '2px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: `${marketProgress.percent}%`,
                  background: '#D87757',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          )}
          
          {/* Nav Items */}
          <nav style={{ flex: 1, padding: '8px' }}>
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '8px 12px',
                  marginBottom: '4px',
                  borderRadius: '8px',
                  background: activeTab === item.id ? '#e7e5dc' : 'transparent',
                  color: '#3d3d3a',
                  fontSize: '13px',
                  fontWeight: activeTab === item.id ? 600 : 500,
                  border: 'none',
                  cursor: 'pointer',
                  justifyContent: sidebarExpanded ? 'flex-start' : 'center',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== item.id) e.currentTarget.style.background = '#e7e5dc';
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== item.id) e.currentTarget.style.background = 'transparent';
                }}
              >
                <MaterialIcon>{item.icon}</MaterialIcon>
                {sidebarExpanded && <span>{item.label}</span>}
              </button>
            ))}
          </nav>
          
          {/* Profile Section */}
          <div
            onClick={() => !sidebarExpanded && setSidebarExpanded(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#e7e5dc'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: '#D87757',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              fontWeight: 600,
              flexShrink: 0
            }}>
              C
            </div>
            {sidebarExpanded && (
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 600, lineHeight: '16px', color: '#3d3d3a' }}>
                  Colin
                </div>
                <div style={{ fontSize: '11px', lineHeight: '14px', marginTop: '2px', color: '#3d3d3a' }}>
                  Co-Founder
                </div>
              </div>
            )}
          </div>
        </aside>
        
        {/* Main Content */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Header */}
          <header style={{
            background: '#FFFFFF',
            borderBottom: '1px solid #CFC9C1',
            padding: '14px 24px',
            minHeight: '95px',
            display: 'flex',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <div>
                <h1 style={{
                  fontSize: '20px',
                  fontWeight: 600,
                  lineHeight: '24px',
                  margin: '0 0 2px 0',
                  color: '#3d3d3a'
                }}>
                  {titles[activeTab].title}
                </h1>
                <p style={{ fontSize: '12px', color: '#3d3d3a', margin: 0 }}>
                  {titles[activeTab].subtitle}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: '#3d3d3a' }}>Fund P&L</div>
                  <div style={{ fontSize: '16px', fontWeight: 600, color: '#5A7A5F' }}>
                    +$2,847.50
                  </div>
                </div>
                <div style={{ width: '1px', height: '32px', background: '#CFC9C1' }} />
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: '#3d3d3a' }}>AUM</div>
                  <div style={{ fontSize: '16px', fontWeight: 600, color: '#3d3d3a' }}>
                    $2.4M
                  </div>
                </div>
              </div>
            </div>
          </header>
          
          {/* Content Area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
            {activeTab === 'premarket' && (
              <div style={{ maxWidth: '1400px' }}>
                {/* Table */}
                <div style={{
                  background: '#f5f4ed',
                  border: '1px solid #CFC9C1',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  marginBottom: '16px'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ background: '#e7e5dc', borderBottom: '1px solid #CFC9C1' }}>
                      <tr>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'left' }}>Rank</th>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'left' }}>Symbol</th>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'right' }}>Score</th>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'right' }}>Volatility</th>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'right' }}>Momentum</th>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'right' }}>Volume</th>
                        <th style={{ padding: '8px 12px', fontSize: '11px', fontWeight: 600, color: '#3d3d3a', textAlign: 'right' }}>Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {premarketData.map((stock, idx) => (
                        <tr
                          key={stock.symbol}
                          style={{ borderBottom: '1px solid #CFC9C1' }}
                          onMouseEnter={(e) => e.currentTarget.style.background = '#e7e5dc'}
                          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                          <td style={{ padding: '10px 12px', fontSize: '12px', color: '#3d3d3a' }}>
                            #{idx + 1}
                          </td>
                          <td style={{ padding: '10px 12px' }}>
                            <StockSymbolButton stock={stock} />
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: '13px', fontWeight: 500, color: '#3d3d3a', textAlign: 'right' }}>
                            {stock.score}
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: '12px', color: '#3d3d3a', textAlign: 'right' }}>
                            {stock.volatility}%
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: '12px', color: '#3d3d3a', textAlign: 'right' }}>
                            {stock.momentum}
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: '12px', color: '#3d3d3a', textAlign: 'right' }}>
                            {stock.volume}
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: '12px', color: '#3d3d3a', textAlign: 'right' }}>
                            {stock.confidence}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Data Cards Grid - Below Table */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '12px'
                }}>
                  {dataCards.map((card, idx) => (
                    <div key={idx} style={{
                      background: '#f5f4ed',
                      border: '1px solid #CFC9C1',
                      borderRadius: '8px',
                      padding: '16px'
                    }}>
                      <div style={{ fontSize: '11px', color: '#3d3d3a', marginBottom: '8px' }}>
                        {card.label}
                      </div>
                      <div style={{ fontSize: '24px', fontWeight: 600, color: '#3d3d3a' }}>
                        {card.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {activeTab !== 'premarket' && (
              <div style={{
                background: '#f5f4ed',
                border: '1px solid #CFC9C1',
                borderRadius: '8px',
                padding: '20px',
                maxWidth: '1400px'
              }}>
                <div style={{ fontSize: '13px', color: '#3d3d3a' }}>
                  {activeTab === 'live' && 'Live trading monitor coming soon...'}
                  {activeTab === 'report' && 'Daily performance report coming soon...'}
                  {activeTab === 'settings' && 'Settings panel coming soon...'}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}