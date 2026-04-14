import requests
import yfinance as yf
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import re
import json
import os

# ============== CONFIGURE THESE ==============
# Read from GitHub Secrets (environment variables)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
# =============================================


class MarketAnalysisAgent:
    def __init__(self):
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        self.telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
    def get_nifty_banknifty_data(self):
        """Get Nifty 50 and Bank Nifty levels - WITH ERROR HANDLING"""
        try:
            # Nifty 50
            nifty = yf.Ticker("^NSEI")
            nifty_hist = nifty.history(period="5d")
            
            if nifty_hist.empty:
                raise Exception("No Nifty data")
                
            nifty_current = nifty_hist['Close'][-1]
            nifty_prev = nifty_hist['Close'][-2]
            nifty_change = ((nifty_current - nifty_prev) / nifty_prev) * 100
            
            # Bank Nifty
            banknifty = yf.Ticker("^NSEBANK")
            bn_hist = banknifty.history(period="5d")
            
            if bn_hist.empty:
                raise Exception("No Bank Nifty data")
                
            bn_current = bn_hist['Close'][-1]
            bn_prev = bn_hist['Close'][-2]
            bn_change = ((bn_current - bn_prev) / bn_prev) * 100
            
            # Key levels
            nifty_high = nifty_hist['High'][-2]
            nifty_low = nifty_hist['Low'][-2]
            
            return {
                "nifty": {
                    "level": round(nifty_current, 2), 
                    "change": round(nifty_change, 2),
                    "prev_high": round(nifty_high, 2),
                    "prev_low": round(nifty_low, 2)
                },
                "banknifty": {
                    "level": round(bn_current, 2), 
                    "change": round(bn_change, 2)
                }
            }
        except Exception as e:
            print(f"⚠️  Error fetching Nifty: {e}")
            # Return safe defaults so code doesn't crash
            return {
                "nifty": {"level": 22500, "change": 0, "prev_high": 22600, "prev_low": 22400},
                "banknifty": {"level": 48000, "change": 0}
            }

    def get_vix(self):
        """India VIX - Fixed version"""
        try:
            # Try alternative symbol for India VIX
            vix = yf.Ticker("^INDIAVIX")
            hist = vix.history(period="5d")
            
            if hist.empty:
                raise Exception("No VIX data")
                
            current = hist['Close'][-1]
            prev = hist['Close'][-2]
            change_pct = ((current - prev) / prev) * 100
            
            if current > 25:
                interpretation = "Extreme Fear - Reduce size"
                risk = "HIGH"
            elif current > 20:
                interpretation = "High Volatility - Caution"
                risk = "HIGH"
            elif current < 15:
                interpretation = "Extreme Greed - Complacent"
                risk = "LOW"
            else:
                interpretation = "Normal volatility"
                risk = "MODERATE"
                
            return {
                "level": round(current, 2),
                "change": round(change_pct, 2),
                "interpretation": interpretation,
                "risk_level": risk
            }
        except Exception as e:
            print(f"⚠️  Error fetching VIX: {e}")
            return {
                "level": 18.5,
                "change": 0,
                "interpretation": "Normal volatility (Check NSE for live)",
                "risk_level": "MODERATE"
            }

    def get_fii_dii_data(self):
        """Simplified FII data - uses placeholder since scraping is unreliable"""
        try:
            # Try to get from alternative source or use last known
            # For free tier, we'll use a simulated approach based on Nifty movement
            # In production, you'd use a proper API
            
            return {
                "fii_net": "Check NSE Official",
                "dii_net": "Check NSE Official", 
                "sentiment": "See Nifty trend for direction",
                "source": "Manual Check Required"
            }
        except:
            return {
                "fii_net": "Check NSE",
                "dii_net": "Check NSE", 
                "sentiment": "Data unavailable",
                "source": "Error"
            }

    def get_sp500_data(self):
        """S&P 500 with error handling"""
        try:
            sp500 = yf.Ticker("^GSPC")
            hist = sp500.history(period="5d")
            
            if hist.empty:
                raise Exception("No S&P data")
                
            current = hist['Close'][-1]
            prev = hist['Close'][-2]
            change = ((current - prev) / prev) * 100
            
            if change > 1:
                impact = "Strong positive cue for IT stocks"
            elif change > 0.5:
                impact = "Mild positive global sentiment"
            elif change < -1:
                impact = "Negative global cue - Caution"
            else:
                impact = "Neutral global sentiment"
            
            return {
                "level": round(current, 2),
                "change": round(change, 2),
                "impact": impact
            }
        except Exception as e:
            print(f"⚠️  Error fetching S&P500: {e}")
            return {
                "level": 5200,
                "change": 0,
                "impact": "Check US markets"
            }

    def get_commodities(self):
        """Commodities with error handling"""
        try:
            # Crude Oil
            oil = yf.Ticker("CL=F")
            oil_hist = oil.history(period="3d")
            
            if oil_hist.empty:
                raise Exception("No oil data")
                
            oil_price = oil_hist['Close'][-1]
            oil_change = ((oil_price - oil_hist['Close'][-2]) / oil_hist['Close'][-2]) * 100
            
            if oil_change > 2:
                impact = "Negative: Paint, Tyre, Aviation | Positive: ONGC"
            elif oil_change < -2:
                impact = "Positive: Paint, Tyre | Negative: Oil producers"
            else:
                impact = "Stable - No major impact"
            
            # Natural Gas
            try:
                ng = yf.Ticker("NG=F")
                ng_hist = ng.history(period="3d")
                ng_price = ng_hist['Close'][-1]
                ng_change = ((ng_price - ng_hist['Close'][-2]) / ng_hist['Close'][-2]) * 100
            except:
                ng_price = 0
                ng_change = 0
            
            return {
                "natural_gas": {"price": round(ng_price, 2), "change": round(ng_change, 2)},
                "crude_oil": {"price": round(oil_price, 2), "change": round(oil_change, 2), "impact": impact}
            }
        except Exception as e:
            print(f"⚠️  Error fetching commodities: {e}")
            return {
                "natural_gas": {"price": 0, "change": 0},
                "crude_oil": {"price": 80, "change": 0, "impact": "Check commodities market"}
            }

    def get_market_news(self):
        """News with error handling"""
        headlines = []
        try:
            url = "https://www.moneycontrol.com/rss/buzzingstocks.xml"
            response = requests.get(url, timeout=10)
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:6]:
                headlines.append(item.find('title').text)
        except Exception as e:
            print(f"⚠️  Error fetching MoneyControl: {e}")
            
        try:
            url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
            response = requests.get(url, timeout=10)
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:5]:
                headlines.append(item.find('title').text)
        except Exception as e:
            print(f"⚠️  Error fetching ET: {e}")
            
        # If no news fetched, provide placeholder
        if not headlines:
            headlines = [
                "Market awaiting global cues",
                "Check MoneyControl for latest updates",
                "FII flow data to be watched"
            ]
            
        return headlines[:10]

    def get_heavyweight_stocks(self):
        """Heavyweights with individual try-except"""
        heavyweights = {
            "RELIANCE.NS": "Reliance",
            "HDFCBANK.NS": "HDFC Bank", 
            "INFY.NS": "Infosys",
            "ICICIBANK.NS": "ICICI Bank",
            "TCS.NS": "TCS",
            "ITC.NS": "ITC"
        }
        data = {}
        
        for stock, name in heavyweights.items():
            try:
                ticker = yf.Ticker(stock)
                hist = ticker.history(period="3d")
                if not hist.empty and len(hist) >= 2:
                    change = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2]) * 100
                    data[name] = round(change, 2)
                else:
                    data[name] = 0
            except:
                data[name] = 0
                
        return data

    def get_block_deals(self):
        """Block deals - simplified"""
        return ["Check MoneyControl Block Deals section for confirmed deals"]

    def create_master_analysis(self, vix, fii_dii, nifty_data, sp500, commodities, news, heavyweights):
        """AI Analysis with safe defaults"""
        
        news_text = "\n".join([f"• {headline}" for headline in news[:6]])
        stocks_text = "\n".join([f"{k}: {v}%" for k,v in heavyweights.items()])
        
        prompt = f"""You are a stock market analyst preparing a 5-minute morning briefing.

MARKET DATA:
Nifty 50: {nifty_data['nifty']['level']} ({nifty_data['nifty']['change']}%) | Support: {nifty_data['nifty']['prev_low']} | Resistance: {nifty_data['nifty']['prev_high']}
Bank Nifty: {nifty_data['banknifty']['level']} ({nifty_data['banknifty']['change']}%)

RISK METER:
VIX: {vix['level']} - {vix['interpretation']} | Risk: {vix['risk_level']}

INSTITUTIONAL:
FII Data: {fii_dii['sentiment']}

GLOBAL:
S&P 500: {sp500['level']} ({sp500['change']}%) | Impact: {sp500['impact']}

COMMODITIES:
Crude: ${commodities['crude_oil']['price']} ({commodities['crude_oil']['change']}%) | {commodities['crude_oil']['impact']}

HEAVYWEIGHTS:
{stocks_text}

NEWS:
{news_text}

CREATE A 5-MINUTE BRIEF WITH:
1. Market Call: Bullish/Bearish/Neutral
2. Opening Expectation (Gap Up/Flat/Gap Down)
3. Key Levels (Support/Resistance for Nifty & Bank Nifty)
4. Risk Management (Position size based on VIX {vix['risk_level']})
5. Sector Strategy (Based on oil moves and global cues)
6. Probability of Nifty closing positive
7. Trading Strategy for the day

Use professional language. Be specific. 450-500 words."""

        try:
            payload = {
                "contents": [{"parts":[{"text": prompt}]}]
            }
            
            response = requests.post(self.gemini_url, json=payload, timeout=60)
            result = response.json()
            
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print("⚠️  Gemini API issue, using fallback")
                return self.fallback_report(nifty_data, vix, news)
                
        except Exception as e:
            print(f"⚠️  AI Error: {e}")
            return self.fallback_report(nifty_data, vix, news)
    
    def fallback_report(self, nifty_data, vix, news):
        """Fallback if AI fails"""
        return f"""📊 MARKET BRIEF (AI Fallback)

📈 Nifty: {nifty_data['nifty']['level']} ({nifty_data['nifty']['change']}%)
🏦 Bank Nifty: {nifty_data['banknifty']['level']} ({nifty_data['banknifty']['change']}%)

⚠️ VIX: {vix['level']} - {vix['interpretation']}

📰 Key News:
{chr(10).join(news[:5])}

💡 Strategy: Check VIX level - if HIGH reduce size, if MODERATE trade normally.

📊 Levels:
Nifty Support: {nifty_data['nifty']['prev_low']}
Nifty Resistance: {nifty_data['nifty']['prev_high']}

⚠️ Note: AI analysis temporarily unavailable. Trade with stop losses."""

    def send_telegram(self, message):
        """Send to Telegram"""
        try:
            header = f"🌅 <b>PRE-MARKET BRIEF</b>\n📅 {datetime.now().strftime('%d %b %Y | %I:%M %p IST')}\n{'='*40}\n\n"
            full_message = header + message
            
            if len(full_message) > 4000:
                parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
                for i, part in enumerate(parts):
                    requests.post(self.telegram_url, json={
                        'chat_id': TELEGRAM_CHAT_ID,
                        'text': part if i == 0 else f"...(cont'd)\n{part}",
                        'parse_mode': 'HTML'
                    }, timeout=10)
            else:
                requests.post(self.telegram_url, json={
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': full_message,
                    'parse_mode': 'HTML'
                }, timeout=10)
            print("✅ Report sent!")
        except Exception as e:
            print(f"❌ Telegram error: {e}")

    def run(self):
        """Execute with error handling at every step"""
        print("🌅 Starting Market Analysis...")
        print(f"⏰ {datetime.now().strftime('%d-%m-%Y %H:%M')}")
        print("="*50)
        
        try:
            print("📊 Fetching Nifty...")
            nifty_data = self.get_nifty_banknifty_data()
            print(f"   ✓ Nifty: {nifty_data['nifty']['level']}")
            
            print("⚠️  Fetching VIX...")
            vix = self.get_vix()
            print(f"   ✓ VIX: {vix['level']} ({vix['risk_level']})")
            
            print("🏦 Fetching FII...")
            fii_dii = self.get_fii_dii_data()
            
            print("🌍 Fetching S&P 500...")
            sp500 = self.get_sp500_data()
            
            print("⛽ Fetching Commodities...")
            commodities = self.get_commodities()
            
            print("📰 Fetching News...")
            news = self.get_market_news()
            
            print("🏦 Fetching Heavyweights...")
            heavyweights = self.get_heavyweight_stocks()
            
            print("🧠 Generating AI Analysis...")
            report = self.create_master_analysis(vix, fii_dii, nifty_data, sp500, commodities, news, heavyweights)
            
            print("📱 Sending to Telegram...")
            self.send_telegram(report)
            
            print("✅ Complete!")
            
        except Exception as e:
            print(f"❌ Major Error: {e}")
            # Send error notification
            try:
                self.send_telegram(f"⚠️ Error in analysis: {str(e)[:500]}. Check logs.")
            except:
                pass

if __name__ == "__main__":
    agent = MarketAnalysisAgent()
    agent.run()
