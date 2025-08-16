            # --- Imports ---
import asyncio
import websockets # Use version 11.0.3 as established
import json
import os
import base64
import traceback
import logging
import threading # Use standard threading
from queue import Queue # Use standard thread-safe queue
import re # <<< Import regex

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s'
)
log = logging.getLogger(__name__)

# --- OpenAI Realtime Configuration ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    log.critical("CRITICAL: OPENAI_API_KEY environment variable not set!")
    # exit()

MODEL_ID = "gpt-4o-realtime-preview" # Standard realtime model
WEBSOCKET_URL = f"wss://api.openai.com/v1/realtime?model={MODEL_ID}"
INPUT_API_FORMAT_STRING = "pcm16"
OUTPUT_API_FORMAT_STRING = "pcm16"
ASSUMED_OUTPUT_SAMPLE_RATE = 24000

# --- Load ETF Corpus ---
def load_etf_corpus():
    try:
        with open('corpus.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        log.warning("corpus.txt not found, using empty ETF content")
        return ""

ETF_CORPUS = load_etf_corpus()

# --- Advisor Context ---
ADVISOR_CONTEXT = """
# Comprehensive Client Datasets

## CLIENT 1: THOMAS J. WILSON

### CONTACT INFORMATION
- **Full Name:** Thomas J. Wilson
- **Nickname:** Tom
- **Email:** thomas.wilson@goldmansachs.com
- **Phone:** (212) 555-7891

### PROFESSIONAL DETAILS
- **Buying Unit Lead:** Thomas Wilson
- **Designation:** Partner, Wealth Management Advisor, Executive Director
- **Organization:** Goldman Sachs
- **Past Organizations:** Morgan Stanley, BlackRock Inc., Fidelity Investments
- **AF Tenure:** 22 years
- **Total Experience:** 34 years
- **Firm Experience:** 15 years
- **Education:** Harvard University, MBA
- **Recent Professional Update:** Named Partner at Wilson & Associates Law Firm (01/2025)

### PERSONAL INFORMATION
- **Interests:** Tennis, Classic Cars, Art Collection, Mountain Biking
- **Personal Website:** https://advisor.goldmansachs.com/wilson-partners-group
- **LinkedIn:** https://www.linkedin.com/in/thomas-wilson-84672195/
- **Recent Personal Update:** Recently purchased vacation property in Scottsdale, AZ (02/2025)

### LICENSING & REGULATORY
- **Licenses:** 7, 66, 24, 9, 10
- **Dually Licensed BD/RIA:** Yes
- **Dually Registered BD/RIA:** Yes
- **No of Registered States:** 16

### SEGMENTATION INFORMATION
- **Branch Reps changed YTD:** 3
- **PW Segmentation:** Ultra-High Net Worth
- **RP Rating:** HP1
- **Retail Segmentation:** HNW
- **RP Segmentation:** Heavy RP

### ASSETS & BOOK
- **CG AUM:** $28.4M as of Jan 2025 (65.3% Retail, 34.7% Retirement)
- **Top holdings in MF (100%):** 41.2% WGI, 15.8% NPF, 9.3% GFA
- **Total Book:** $712.6M (18.3% SMA, 36.5% ETF, 45.2% MF)
- **Market Position:** Among top 5% proactive in territory with 2.4% market share
- **Top Categories:** 1.2% Global Large-Stock Blend, 0.6% Global Large-Stock Growth, 0.5% Large Growth
- **ETF Addressable Opportunity:** $58.7M in Large Blend, $42.3M in Large Growth
- **SMA Addressable Opportunity:** $34.6M in Large Blend, $23.9M in Large Growth

### SALES & REDEMPTIONS
- **Sales YTD:** $43.5M (+28% YoY)
- **Retail Sales YTD:** $28.4M
- **Retirement Sales YTD:** $15.1M
- **YTD Redemptions:** $1.75M as of Feb 2025

### RECENT INTERACTIONS & DISCUSSIONS
- **Investment Performance:** Reviewed 2024 investment performance (01/15/2025)
- **Tax Planning:** Discussed year-end tax planning strategies (11/08/2024)
- **Portfolio Rebalancing:** Requested portfolio rebalancing analysis (01/15/2025)
- **Alternative Investments:** Interested in alternative investment options (02/08/2025) and requested detailed analysis (02/2025)

### INVESTMENT PREFERENCES & CONCERNS
- **Portfolio Allocation:** Wants to maintain 70/30 equity-to-bond ratio despite market volatility (02/2025)
- **Sector Focus:** Added specialized technology sector ETFs to growth portion (01/2025)
- **Income Strategy:** Comparing VYM and SCHD for dividend growth strategy (02/2025)
- **Concerns:** Inflation impact on fixed income holdings (01/2025)

### ENGAGEMENTS
- **Recent Event Attendance:** Quarterly portfolio review & private client dinner event since last visit in Jan 2025
- **Forum Attendance:** Global Market Outlook: Q1 Update (Jan 2025)

### OFFICE INTEL
- **Pages Viewed:** GRAL, AMBAL, WGI (Feb 2025), AFTD30, GFA, NPF, Tools & Planning Hypotheticals (Jan 2025)
- **Team Activity:** Team member Rebecca Zhang viewed pages on Technology Sector Analysis (Feb 2025)


---

## CLIENT 2: SAMANTHA L. CHEN

### CONTACT INFORMATION
- **Full Name:** Samantha L. Chen
- **Nickname:** Sam
- **Email:** samantha.chen@morganstanley.com
- **Phone:** (512) 555-2367

### PROFESSIONAL DETAILS
- **Buying Unit Lead:** Samantha Chen
- **Designation:** Chief Marketing Officer, Senior Wealth Advisor, Managing Director
- **Organization:** Morgan Stanley
- **Past Organizations:** UBS Financial Services, Wells Fargo Advisors, Credit Suisse
- **AF Tenure:** 15 years
- **Total Experience:** 24 years
- **Firm Experience:** 8 years
- **Education:** University of Texas, MBA
- **Recent Professional Update:** Relocated to Austin for new position as CMO at TechEdge (12/2024)

### PERSONAL INFORMATION
- **Interests:** Marathon Running, Photography, International Cuisine, Volunteering
- **Personal Website:** https://advisor.morganstanley.com/chen-wealth-partners
- **LinkedIn:** https://www.linkedin.com/in/samantha-chen-62894731/
- **Recent Personal Update:** Children starting at new schools in fall semester (02/2025)

### LICENSING & REGULATORY
- **Licenses:** 7, 65, 63, 31
- **Dually Licensed BD/RIA:** No
- **Dually Registered BD/RIA:** Yes
- **No of Registered States:** 9

### SEGMENTATION INFORMATION
- **Branch Reps changed YTD:** 1
- **PW Segmentation:** High Net Worth
- **RP Rating:** HP2
- **Retail Segmentation:** HP
- **RP Segmentation:** Medium RP

### ASSETS & BOOK
- **CG AUM:** $9.6M as of Jan 2025 (81.5% Retail, 18.5% Retirement)
- **Top holdings in MF (100%):** 38.3% WGI, 11.2% NPF, 7.8% GFA
- **Total Book:** $328.9M (25.4% SMA, 42.1% ETF, 32.5% MF)
- **Market Position:** Among top 15% proactive in territory with 1.5% market share
- **Top Categories:** 0.7% Global Large-Stock Blend, 0.4% Global Large-Stock Growth, 0.4% Mid-Cap Value
- **ETF Addressable Opportunity:** $32.5M in Large Blend, $18.7M in Large Growth
- **SMA Addressable Opportunity:** $19.3M in Large Blend, $11.8M in Large Growth

### SALES & REDEMPTIONS
- **Sales YTD:** $18.7M (-15% YoY)
- **Retail Sales YTD:** $15.2M
- **Retirement Sales YTD:** $3.5M
- **YTD Redemptions:** $4.25M as of Feb 2025

### RECENT INTERACTIONS & DISCUSSIONS
- **Interstate Move:** Discussed implications of interstate move (12/05/2024)
- **Retirement Planning:** Reviewed retirement projections based on new compensation (01/12/2025)
- **ESG Portfolio:** Requested ESG portfolio analysis (02/12/2025)
- **Tax Optimization:** Interested in tax optimization strategies (01/28/2025)

### MOST RECENT FOLLOW-UPS
- **Tax Analysis:** Provide analysis of Texas vs. previous state tax implications (01/2025)
- **Local Advisor Research:** Research local financial advisors for face-to-face meetings (02/2025)

### ENGAGEMENTS
- **Recent Events:** 2 calls & attended technology investment symposium since last visit in Feb 2025
- **Forum Attendance:** Emerging Markets: Challenges & Opportunities (Feb 2025)

### OFFICE INTEL
- **Pages Viewed:** NPF, AFTD45, WMIF (Jan 2025), Tools & Planning Hypotheticals, GFA (Feb 2025)
- **Team Activity:** Team member James Thompson viewed pages on Client Retention Strategies (Jan 2025)

---

## CLIENT 3: MICHAEL R. JOHNSON

### CONTACT INFORMATION
- **Full Name:** Michael R. Johnson
- **Nickname:** Mike
- **Email:** mjohnson@jpmorgan.com
- **Phone:** (415) 555-9876

### PROFESSIONAL DETAILS
- **Buying Unit Lead:** Michael Johnson
- **Designation:** Family Office Director, Private Client Advisor, Executive Vice President
- **Organization:** J.P. Morgan Private Bank
- **Past Organizations:** Merrill Lynch, Charles Schwab, Goldman Sachs
- **AF Tenure:** 25 years
- **Total Experience:** 38 years
- **Firm Experience:** 12 years
- **Education:** Stanford University, Finance

### PERSONAL INFORMATION
- **Interests:** Sailing, Wine Collecting, Historical Biographies, Philanthropy
- **Personal Website:** https://privatebank.jpmorgan.com/johnson-family-office
- **LinkedIn:** https://www.linkedin.com/in/michael-johnson-52173984/
- **Recent Personal Updates:** 
  - Celebrated 25th wedding anniversary (02/2025)
  - Planning European vacation for summer 2025 (02/2025)

### LICENSING & REGULATORY
- **Licenses:** 7, 63, 65, 3, 9
- **Dually Licensed BD/RIA:** Yes
- **Dually Registered BD/RIA:** Yes
- **No of Registered States:** 21

### SEGMENTATION INFORMATION
- **Branch Reps changed YTD:** 0
- **PW Segmentation:** Ultra-High Net Worth
- **RP Rating:** HP1
- **Retail Segmentation:** HNW
- **RP Segmentation:** Heavy RP

### ASSETS & BOOK
- **CG AUM:** $42.5M as of Jan 2025 (58.7% Retail, 41.3% Retirement)
- **Top holdings in MF (100%):** 36.9% WGI, 14.2% NPF, 10.1% GFA
- **Total Book:** $945.2M (22.7% SMA, 28.4% ETF, 48.9% MF)
- **Market Position:** Among top 3% proactive in territory with 3.2% market share
- **Top Categories:** 1.4% Global Large-Stock Blend, 0.9% Global Large-Stock Growth, 0.8% Large Value
- **ETF Addressable Opportunity:** $87.4M in Large Blend, $65.2M in Large Growth
- **SMA Addressable Opportunity:** $48.6M in Large Blend, $36.3M in Large Growth

### SALES & REDEMPTIONS
- **Sales YTD:** $67.3M (+42% YoY)
- **Retail Sales YTD:** $39.5M
- **Retirement Sales YTD:** $27.8M
- **YTD Redemptions:** $2.18M as of Feb 2025

### RECENT INTERACTIONS & DISCUSSIONS
- **Charitable Giving:** Discussed charitable giving strategies (10/17/2024)
- **Medicare Planning:** Reviewed Medicare enrollment options (01/08/2025)
- **Family Office:** Requested family office structure analysis (02/18/2025)
- **Philanthropy Planning:** Interested in philanthropy planning options (02/05/2025)

### INVESTMENT PREFERENCES & CONCERNS
- **Sector Focus:** Increased allocation to healthcare sector following analyst call (01/2025)
- **Fixed Income Strategy:** Rebalanced fixed income to include more TIPS for inflation protection (02/2025)
- **Sustainable Investing:** Interested in exploring ESG-focused funds for portfolio (02/2025)
- **Income Generation:** Requested analysis of QYLD vs. JEPI for income generation (02/2025)

### ENGAGEMENTS
- **Recent Events:** 5 calls & attended exclusive client appreciation event since last visit in Dec 2024
- **Forum Attendance:** Private Equity: Opportunities for Family Offices (Jan 2025)

### OFFICE INTEL
- **Pages Viewed:** GRAL, IFA, AMBAL, WGI (Feb 2025), AFTD60, GFA, NPF, Tools & Planning Hypotheticals (Jan 2025)
- **Team Activity:** Team member Sarah Williams viewed pages on Alternative Investments (Feb 2025)

---

## CLIENT 4: JESSICA A. MARTINEZ

### CONTACT INFORMATION
- **Full Name:** Jessica A. Martinez
- **Nickname:** Jess
- **Email:** jessica.martinez@ubs.com
- **Phone:** (617) 555-4321

### PROFESSIONAL DETAILS
- **Buying Unit Lead:** Jessica Martinez
- **Designation:** Senior Portfolio Manager, Financial Advisor, Vice President
- **Organization:** UBS Financial Services
- **Past Organizations:** Raymond James, Morgan Stanley, Edward Jones
- **AF Tenure:** 13 years
- **Total Experience:** 19 years
- **Firm Experience:** 7 years
- **Education:** Boston College, Economics

### PERSONAL INFORMATION
- **Interests:** Hiking, Yoga, Contemporary Art, Book Club
- **Personal Website:** https://financialservices.ubs.com/martinez-wealth-management
- **LinkedIn:** https://www.linkedin.com/in/jessica-martinez-39257461/
- **Recent Personal Updates:**
  - Received substantial bonus after company acquisition (12/2024)
  - Eldest child accepted to graduate program at Stanford (02/2025)

### LICENSING & REGULATORY
- **Licenses:** 7, 66, 31
- **Dually Licensed BD/RIA:** No
- **Dually Registered BD/RIA:** Yes
- **No of Registered States:** 8

### SEGMENTATION INFORMATION
- **Branch Reps changed YTD:** 2
- **PW Segmentation:** Affluent
- **RP Rating:** HP3
- **Retail Segmentation:** AF
- **RP Segmentation:** Medium RP

### ASSETS & BOOK
- **CG AUM:** $7.3M as of Jan 2025 (85.4% Retail, 14.6% Retirement)
- **Top holdings in MF (100%):** 32.5% WGI, 14.8% NPF, 6.9% GFA
- **Total Book:** $215.6M (31.2% SMA, 48.5% ETF, 20.3% MF)
- **Market Position:** Among top 25% proactive in territory with 1.3% market share
- **Top Categories:** 0.5% Global Large-Stock Blend, 0.4% Small-Cap Value, 0.3% Mid-Cap Blend
- **ETF Addressable Opportunity:** $24.8M in Large Blend, $17.5M in Small-Cap Value
- **SMA Addressable Opportunity:** $16.2M in Large Blend, $12.7M in Small-Cap Value

### SALES & REDEMPTIONS
- **Sales YTD:** $12.8M (-28% YoY)
- **Retail Sales YTD:** $10.9M
- **Retirement Sales YTD:** $1.9M
- **YTD Redemptions:** $5.37M as of Feb 2025

### RECENT INTERACTIONS & DISCUSSIONS
- **Lump Sum Investment:** Discussed strategies for lump sum investment (12/15/2024)
- **Estate Planning:** Reviewed updated estate planning documents (01/22/2025)
- **College Planning:** Requested college planning analysis for clients (02/03/2025)
- **Investment Comparisons:** Interested in small-cap value comparisons (01/22/2025)

### MOST RECENT FOLLOW-UPS
- **Investment Strategy Analysis:** Provide analysis of dollar-cost averaging vs. lump sum investment (01/2025)
- **Education Planning:** Research 529 plan options for graduate school funding (02/2025)
- **Tax Planning:** Schedule meeting with tax specialist regarding equity compensation (03/2025)

### ENGAGEMENTS
- **Recent Events:** No calls & not attended events since last visit in Feb 2025
- **Forum Attendance:** Women in Wealth Management (Feb 2025)

### OFFICE INTEL
- **Pages Viewed:** NPF, Insights & Practice Management articles (Feb 2025), AFTD45 (Jan 2025)
- **Team Activity:** Team member David Rodriguez viewed pages on Small-Cap Value Analysis (Jan 2025)

---

## CLIENT 5: RICHARD H. PALMER

### CONTACT INFORMATION
- **Full Name:** Richard H. Palmer
- **Nickname:** Rich
- **Email:** richard.palmer@ml.com
- **Phone:** (310) 555-6789

### PROFESSIONAL DETAILS
- **Buying Unit Lead:** Richard Palmer
- **Designation:** Medical Practice Director, Senior Financial Advisor, Managing Director
- **Organization:** Merrill Lynch Wealth Management
- **Past Organizations:** LPL Financial, Ameriprise Financial, Edward Jones
- **AF Tenure:** 29 years
- **Total Experience:** 35 years
- **Firm Experience:** 18 years
- **Education:** UCLA, Medical Economics
- **Recent Professional Update:** Plans to semi-retire from medical practice next year (02/2025)

### PERSONAL INFORMATION
- **Interests:** Golf, Medical Innovation Investments, Classical Music, European Travel
- **Personal Website:** https://fa.ml.com/palmer-medical-practice-group
- **LinkedIn:** https://www.linkedin.com/in/richard-palmer-md-cfp-83652147/
- **Recent Personal Update:** Recently completed renovation of primary residence (01/2025)

### LICENSING & REGULATORY
- **Licenses:** 7, 24, 65, 66
- **Dually Licensed BD/RIA:** Yes
- **Dually Registered BD/RIA:** Yes
- **No of Registered States:** 12

### SEGMENTATION INFORMATION
- **Branch Reps changed YTD:** 1
- **PW Segmentation:** High Net Worth
- **RP Rating:** HP2
- **Retail Segmentation:** HP
- **RP Segmentation:** Heavy RP

### ASSETS & BOOK
- **CG AUM:** $18.7M as of Jan 2025 (63.8% Retail, 36.2% Retirement)
- **Top holdings in MF (100%):** 38.5% WGI, 13.7% NPF, 8.9% GFA
- **Total Book:** $583.4M (16.8% SMA, 35.2% ETF, 48.0% MF)
- **Market Position:** Among top 8% proactive in territory with 2.1% market share
- **Top Categories:** 0.9% Global Large-Stock Blend, 0.7% Healthcare Sector, 0.5% Large Value
- **ETF Addressable Opportunity:** $45.2M in Large Blend, $37.8M in Healthcare Sector
- **SMA Addressable Opportunity:** $29.5M in Large Blend, $22.6M in Healthcare Sector

### SALES & REDEMPTIONS
- **Sales YTD:** $31.9M (+12% YoY)
- **Retail Sales YTD:** $20.3M
- **Retirement Sales YTD:** $11.6M
- **YTD Redemptions:** $2.84M as of Feb 2025

### RECENT INTERACTIONS & DISCUSSIONS
- **Practice Succession:** Discussed practice succession planning (09/23/2024)
- **Tax Legislation:** Reviewed potential impact of new tax legislation (11/05/2024)
- **Healthcare Sector:** Requested healthcare sector investment analysis (02/10/2025)
- **Retirement Income:** Interested in retirement income strategies (01/30/2025)

### INVESTMENT PREFERENCES & CONCERNS
- **Portfolio Focus:** Shifting portfolio focus toward income generation for semi-retirement (01/2025)
- **Fixed Income Strategy:** Added municipal bond ladder for tax-efficient income (02/2025)
- **Tax Concerns:** Concerned about potential capital gains tax increases (02/2025)
- **Sector Diversification:** Interested in reducing single-stock concentration in healthcare sector (02/2025)
- **Retirement Planning:** Comparing various annuity options for guaranteed income stream (02/2025)

### ENGAGEMENTS
- **Recent Events:** 3 calls & attended healthcare innovation symposium since last visit in Jan 2025
- **Forum Attendance:** Healthcare Sector: Innovation & Investment (Feb 2025)

### OFFICE INTEL
- **Pages Viewed:** GRAL, IFA, WGI (Jan 2025), AFTD25, GFA, NPF, Tools & Planning Hypotheticals (Feb 2025)
- **Team Activity:** Team member Jennifer Adams viewed pages on Retirement Income Strategies (Jan 2025)

"""

# --- Helper to Parse Advisor Context ---
def parse_advisor_context(context_string):
    advisors = {}
    client_blocks = re.split(r'\n## CLIENT \d+: ', context_string.strip())[1:]
    for i, block in enumerate(client_blocks, 1):
        lines = block.strip().split('\n')
        full_name = lines[0].strip()
        advisors[full_name] = {'id': i}
        current_section = None
        section_content = []
        for line in lines[1:]:
            section_match = re.match(r'###\s+(.+)', line)
            if section_match:
                if current_section and section_content:
                    advisors[full_name][current_section] = '\n'.join(section_content).strip()
                current_section = section_match.group(1).strip()
                section_content = []
            elif current_section and line.strip() and not line.startswith('- **'):
                 simple_line_match = re.match(r'-\s*\*\*(.+?):\*\*\s*(.*)', line)
                 if simple_line_match:
                     key = simple_line_match.group(1).strip()
                     value = simple_line_match.group(2).strip()
                     advisors[full_name][f"{current_section}_{key}"] = value
                 elif not line.strip().startswith('---'):
                      section_content.append(line.strip())
        if current_section and section_content:
            advisors[full_name][current_section] = '\n'.join(section_content).strip()
        # Flatten specific keys for easier access
        if f'CONTACT INFORMATION_Full Name' in advisors[full_name]: advisors[full_name]['Full Name'] = advisors[full_name].pop(f'CONTACT INFORMATION_Full Name')
        if f'PROFESSIONAL DETAILS_Organization' in advisors[full_name]: advisors[full_name]['Firm Name'] = advisors[full_name].pop(f'PROFESSIONAL DETAILS_Organization')
        if f'ASSETS & BOOK_CG AUM' in advisors[full_name]: advisors[full_name]['AUM String'] = advisors[full_name].pop(f'ASSETS & BOOK_CG AUM') # Keep original string too
        if f'SALES & REDEMPTIONS_Sales YTD' in advisors[full_name]: advisors[full_name]['Sales String'] = advisors[full_name].pop(f'SALES & REDEMPTIONS_Sales YTD')
        if f'SALES & REDEMPTIONS_YTD Redemptions' in advisors[full_name]: advisors[full_name]['Redemptions String'] = advisors[full_name].pop(f'SALES & REDEMPTIONS_YTD Redemptions')

    log.info(f"Parsed data for {len(advisors)} advisors.")
    return advisors

# --- Global Parsed Advisor Data ---
PARSED_ADVISOR_DATA = parse_advisor_context(ADVISOR_CONTEXT)

# --- Flask & SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
async_mode = "threading"
log.info(f"Using {async_mode} async_mode for Flask-SocketIO")
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins="*")

# --- Dedicated Asyncio Loop Setup ---
task_queue = Queue()
asyncio_loop = None
asyncio_thread = None
clients = {} # Structure: clients[sid] = {'client_connected': bool}

def run_asyncio_loop(loop):
    log.info("Asyncio thread started.")
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_tasks_from_queue())
    except Exception as e:
        log.error(f"Exception in asyncio loop's main task: {e}")
        log.error(traceback.format_exc())
    finally:
        log.info("Asyncio loop stopping...");
        try:
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                if not task.done(): task.cancel()
            if tasks: loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e: log.error(f"Error during asyncio loop cleanup: {e}")
        finally: loop.close(); log.info("Asyncio loop closed.")

def start_asyncio_thread():
    global asyncio_loop, asyncio_thread
    if asyncio_thread is None or not asyncio_thread.is_alive():
        asyncio_loop = asyncio.new_event_loop()
        asyncio_thread = threading.Thread(target=run_asyncio_loop, args=(asyncio_loop,), name="AsyncioThread", daemon=True)
        asyncio_thread.start()
        log.info("Dedicated asyncio thread started.")

# --- Background Task Runner (Runs in Asyncio Thread) ---
async def process_tasks_from_queue():
    log.info("Asyncio task processor started.")
    openai_sessions = {} # Structure: openai_sessions[sid] = {'task': Future, 'input_queue': asyncio.Queue}

    while True:
        try:
            item = await asyncio_loop.run_in_executor(None, task_queue.get)
            if item is None: log.info("Task processor stop signal. Shutting down..."); break
            action = item.get('action'); sid = item.get('sid')
            if not sid: log.warning("Task without SID."); task_queue.task_done(); continue

            if action == 'start':
                if clients.get(sid, {}).get('client_connected') and (sid not in openai_sessions or openai_sessions[sid]['task'].done()):
                    log.info(f"[{sid}] 'start', launching OpenAI task.")
                    client_async_input_queue = asyncio.Queue()
                    task_future = asyncio.create_task(openai_session_task(sid, client_async_input_queue))
                    openai_sessions[sid] = {'task': task_future, 'input_queue': client_async_input_queue}
                elif sid in openai_sessions and not openai_sessions[sid]['task'].done(): log.warning(f"[{sid}] 'start' received, task active.")
                else: log.warning(f"[{sid}] 'start', client '{sid}' not connected.")
            elif action == 'stop':
                 if sid in openai_sessions:
                     log.info(f"[{sid}] 'stop', signalling task.")
                     session_data = openai_sessions[sid]
                     session_data['input_queue'].put_nowait(None)
                     del openai_sessions[sid]
                 else: log.warning(f"[{sid}] 'stop' received, no active session.")
            elif action == 'audio':
                 if sid in openai_sessions:
                     session_data = openai_sessions[sid]
                     if not session_data['task'].done():
                         audio_data = item.get('data')
                         if audio_data: session_data['input_queue'].put_nowait(audio_data)
            task_queue.task_done()
        except Exception as e: log.error(f"Error in task processor: {e}\n{traceback.format_exc()}")
    log.info("Asyncio task processor finished. Cleaning up sessions...");
    for sid, session_data in list(openai_sessions.items()):
         log.warning(f"[{sid}] Cancelling remaining session task on processor exit.")
         session_data['task'].cancel()
         del openai_sessions[sid]
    log.info("Processor cleanup complete.")


# --- OpenAI Task (runs in asyncio loop) ---
async def openai_session_task(sid, client_async_input_queue):
    log.info(f"[{sid}] OpenAI task {id(asyncio.current_task())} started.")
    openai_ws = None
    output_sample_rate = ASSUMED_OUTPUT_SAMPLE_RATE
    is_connected_to_openai = False
    loaded_advisor_name = None # <<< Track loaded advisor

    session_instructions = f"""
You are Michael Davidson, a senior ETF specialist with American Funds specializing in Capital Group ETFs. You're making an outbound call to a financial advisor to discuss how our ETF lineup can benefit their clients and grow their business.

**Your Role & Approach:**
- You're confident, knowledgeable, and genuinely helpful
- Your goal is to build a relationship and convert this prospect into a client
- You have extensive knowledge about Capital Group ETFs and their performance
- You understand the advisor's business and can speak their language
- You're consultative, not pushy - you want to help them succeed

**Conversation Flow:**

1. **Opening Greeting (Start immediately with this):**
   "Hi there! This is Michael Davidson calling from American Funds. I'm one of the ETF specialists here, and I wanted to reach out because I've been seeing some great opportunities in the market that might be perfect for your clients. Do you have a couple minutes to chat about how our ETF lineup has been performing?"

2. **Discovery & Needs Assessment:**
   - Ask about their current ETF usage and client needs
   - Listen for pain points: fees, performance, client demands
   - Identify opportunities where Capital Group ETFs could help

3. **Solution Presentation:**
   - Present relevant Capital Group ETFs based on their needs
   - Use specific performance data and compelling facts
   - Focus on client benefits and business growth opportunities

4. **Handle Objections:**
   - Address concerns professionally
   - Use data and examples to overcome resistance
   - Always redirect to client benefits

5. **Call to Action:**
   - Schedule a follow-up meeting
   - Offer to send materials or arrange a deeper dive
   - Get commitment for next steps

**Key Talking Points & Data:**
- CGUS: 29.43% 1-year return, 0.33% expense ratio
- CGGR: 27.33% 1-year return for growth-focused clients  
- CGDV: 17.67% 1-year return with 1.44% yield for income needs
- Active management with daily transparency
- Tight bid-ask spreads and strong liquidity

**Advisor Profiles Available:**
{ADVISOR_CONTEXT}

**ETF Knowledge Base:**
{ETF_CORPUS}

**Conversation Style:**
- Professional but warm and personable
- Use "you" and "your clients" frequently
- Ask open-ended questions to engage
- Share specific success stories when relevant
- Be genuinely helpful and consultative
- Use natural contractions and conversational language

IMPORTANT: As soon as you receive any message (including "start"), immediately begin speaking with your opening greeting. Do not wait for the prospect to speak first - you are making an outbound call.
    """
    headers = { "Authorization": f"Bearer {OPENAI_API_KEY}", "OpenAI-Beta": "realtime=v1" }

    def safe_emit(event, data, room):
        if clients.get(sid, {}).get('client_connected', False):
            try: socketio.emit(event, data, room=room)
            except Exception as e: log.warning(f"[{sid}] Error emitting '{event}': {e}")

    try:
        log.info(f"[{sid}] Connecting to OpenAI WebSocket...")
        async with websockets.connect(WEBSOCKET_URL, extra_headers=headers, ping_interval=5, ping_timeout=20) as openai_ws:
            log.info(f"[{sid}] Connected to OpenAI WS."); is_connected_to_openai = True
            safe_emit('status_update', {'message': 'Connected to Voice Mode'}, room=sid)

            config_event = {
                "type": "session.update",
                "session": {
                    "voice": "alloy",
                    "instructions": session_instructions.strip(),
                    "input_audio_format": INPUT_API_FORMAT_STRING,
                    "output_audio_format": OUTPUT_API_FORMAT_STRING,
                    "turn_detection": { "type": "server_vad", "threshold": 0.5, "prefix_padding_ms": 300, "silence_duration_ms": 200, "interrupt_response": True, "create_response": True }
                }
            }
            log.info(f"[{sid}] Sending config to OpenAI...")
            await openai_ws.send(json.dumps(config_event))
            log.info(f"[{sid}] Config sent.")
            
            # Send a conversation item to trigger the initial greeting
            await asyncio.sleep(0.5)  # Small delay to ensure session is ready
            initial_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "start"}]
                }
            }
            await openai_ws.send(json.dumps(initial_message))
            
            # Trigger response generation
            response_create = {"type": "response.create"}
            await openai_ws.send(json.dumps(response_create))
            log.info(f"[{sid}] Triggered initial greeting.")

            async def receive_from_openai():
                nonlocal output_sample_rate, loaded_advisor_name
                # Only accumulate assistant response
                current_assistant_response = ""
                current_turn_id = None
                speech_count_since_advisor_load = 0
                agenda_triggered = False
                try:
                    async for message in openai_ws:
                        if not clients.get(sid, {}).get('client_connected', False): break
                        try:
                            server_event = json.loads(message); event_type = server_event.get("type")
                            # Log all events to debug what we're receiving
                            if event_type in ["response.text.delta", "response.done", "response.created"]:
                                log.info(f"[{sid}] Event: {event_type}")
                            else:
                                log.debug(f"[{sid}] Event: {event_type}")

                            if event_type == "session.created": log.info(f"[{sid}] OpenAI Session Created...")
                            elif event_type == "session.updated": log.info(f"[{sid}] OpenAI Session Updated.")
                            elif event_type == "input_audio_buffer.speech_started": 
                                log.info(f"[{sid}] OpenAI speech start. Emit interrupt.")
                                safe_emit('interrupt_playback', {}, room=sid)
                                # Reset response accumulation for new turn
                                current_assistant_response = ""
                                log.info(f"[{sid}] Reset assistant response for new turn")
                            elif event_type == "input_audio_buffer.speech_stopped": 
                                log.info(f"[{sid}] OpenAI speech stop.")
                                # Sales specialist mode - no auto-agenda creation needed
                                log.info(f"[{sid}] Sales call speech interaction")
                            elif event_type == "response.text.delta":
                                text = server_event.get('delta')
                                log.info(f"[{sid}] response.text.delta event received. Text: '{text}' (length: {len(text) if text else 0})")
                                if text:
                                    # <<< IMPROVED LOGGING FOR ACCUMULATION >>>
                                    log.info(f"[{sid}] response.text.delta: Received text chunk: '{text}'")
                                    current_assistant_response += text # Accumulate assistant text
                                    log.info(f"[{sid}] response.text.delta: Total accumulated so far: '{current_assistant_response}'")
                                    # <<< END LOGGING >>>
                                    safe_emit('response_text_update', {'text': text, 'is_final': False}, room=sid)
                                else:
                                    log.info(f"[{sid}] response.text.delta: Empty text received")

                                    # Sales specialist mode - no need for advisor detection
                                    # Just log the conversation for analytics
                                    log.info(f"[{sid}] Sales conversation in progress")
                            elif event_type == "response.audio_transcript.delta":
                                # This is the assistant's speech transcript
                                text = server_event.get('delta')
                                if text:
                                    log.info(f"[{sid}] Assistant speaking: '{text}'")
                                    current_assistant_response += text
                                    safe_emit('response_text_update', {'text': text, 'is_final': False}, room=sid)
                            elif event_type == "response.audio.delta":
                                audio_delta = server_event.get('delta')
                                if audio_delta:
                                    log.info(f"[{sid}] Sending audio chunk, length: {len(audio_delta)}")
                                    safe_emit('audio_response', {'audio': audio_delta, 'sample_rate': output_sample_rate}, room=sid)
                                else:
                                    log.warning(f"[{sid}] Received audio.delta with no data")
                            elif event_type == "response.done":
                                log.info(f"[{sid}] Response Done. Assistant Acc: '{current_assistant_response}'")
                                log.debug(f"[{sid}] Full response.done event: {server_event}")

                                # --- Try to get final USER transcript for THIS turn directly from event data --- 
                                turn_user_transcript = server_event.get('transcript') or server_event.get('input_transcript')
                                if turn_user_transcript:
                                    log.info(f"[{sid}] Found user transcript in response.done: '{turn_user_transcript}'")
                                else:
                                    log.warning(f"[{sid}] Could not find user transcript in response.done event.")
                                    turn_user_transcript = "" # Ensure string

                                # --- Sales Call Flow --- 
                                # Get user transcript for logging and analysis
                                turn_user_transcript = server_event.get('transcript') or server_event.get('input_transcript')
                                if turn_user_transcript:
                                    log.info(f"[{sid}] User said: '{turn_user_transcript}'")
                                    safe_emit('transcript_update', {'text': turn_user_transcript, 'is_final': True}, room=sid)
                                else:
                                    log.info(f"[{sid}] No user transcript found in response.done")
                                
                                # Check if user wants follow-up materials or meeting
                                follow_up_keywords = ["send", "email", "materials", "meeting", "follow up", "call back", "schedule"]
                                if turn_user_transcript and any(keyword in turn_user_transcript.lower() for keyword in follow_up_keywords):
                                    log.info(f"[{sid}] User expressed interest in follow-up")
                                
                                # Signal end of ASSISTANT text stream for this turn
                                safe_emit('response_text_update', {'text': '', 'is_final': True}, room=sid)

                                # --- Reset assistant accumulator for next turn --- 
                                current_assistant_response = ""

                            elif event_type == "error" or "error" in event_type:
                                log.error(f"[{sid}] OpenAI Error Event: {server_event}")
                                err_msg = f"OpenAI Error: {server_event.get('error',{}).get('message', 'Unknown')}"
                                safe_emit('error_message', {'message': err_msg}, room=sid)
                        except json.JSONDecodeError:
                            log.warning(f"[{sid}] OpenAI non-JSON: {message[:200]}")
                        except Exception as e:
                            log.error(f"[{sid}] Error processing OpenAI msg: {e}\nData: {message[:200]}")
                            log.error(traceback.format_exc())
                except websockets.exceptions.ConnectionClosed as e:
                    log.warning(f"[{sid}] OpenAI WS recv loop closed: {e.code}")
                except asyncio.CancelledError:
                    log.info(f"[{sid}] OpenAI receive task cancelled.")
                except Exception as e:
                    log.error(f"[{sid}] Error in OpenAI receive loop: {e}\n{traceback.format_exc()}")
                finally:
                    log.info(f"[{sid}] OpenAI receive loop finished.")

            async def send_to_openai():
                try:
                    while True:
                        if not clients.get(sid, {}).get('client_connected', False): break
                        base64_audio = await client_async_input_queue.get()
                        if base64_audio is None: client_async_input_queue.task_done(); break
                        try:
                            if not is_connected_to_openai: log.warning(f"[{sid}] OpenAI WS disconnected, cannot send."); break
                            event = { "type": "input_audio_buffer.append", "audio": base64_audio }
                            if openai_ws and openai_ws.open: await openai_ws.send(json.dumps(event))
                            else: log.warning(f"[{sid}] OpenAI WS closed state? Cannot send."); break
                        except Exception as send_err: log.error(f"[{sid}] Error sending to OpenAI: {send_err}"); break
                        finally: client_async_input_queue.task_done()
                except asyncio.CancelledError: log.info(f"[{sid}] OpenAI send task cancelled.")
                except Exception as e: log.error(f"[{sid}] Error in OpenAI send loop: {e}\n{traceback.format_exc()}")
                finally: log.info(f"[{sid}] OpenAI send loop finished.")

            recv_task = asyncio.create_task(receive_from_openai())
            send_task = asyncio.create_task(send_to_openai())
            done, pending = await asyncio.wait([recv_task, send_task], return_when=asyncio.FIRST_COMPLETED)
            for task in pending: task.cancel()
            if pending: await asyncio.gather(*pending, return_exceptions=True)

    except websockets.exceptions.InvalidStatusCode as e: reason = getattr(e, 'reason', 'Unknown'); log.error(f"[{sid}] OpenAI Conn Failed: {e.status_code} {reason}"); safe_emit('error_message', {'message': f'OpenAI Conn Failed: {e.status_code}'}, room=sid)
    except Exception as e: log.error(f"[{sid}] Unexpected error in OpenAI task: {e}\n{traceback.format_exc()}"); safe_emit('error_message', {'message': 'Server error connecting to OpenAI'}, room=sid)
    finally:
        log.info(f"[{sid}] OpenAI session task {id(asyncio.current_task())} finishing.")
        is_connected_to_openai = False
        if openai_ws and openai_ws.open:
             await openai_ws.close()
             log.info(f"[{sid}] Closed OpenAI WS.")
        if sid in clients: clients[sid]['client_connected'] = False


# --- Flask Routes & SocketIO Handlers ---
@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/api/advisor-data')
def get_advisor_data():
    return PARSED_ADVISOR_DATA

@app.route('/static/images/<filename>')
def serve_images(filename):
    return send_from_directory('static/images', filename)

@socketio.on('connect')
def handle_connect():
    sid = request.sid; log.info(f"Client connected: {sid}")
    clients[sid] = { 'client_connected': True }
    emit('status_update', {'message': 'Connected to Server'})

@socketio.on('disconnect')
def handle_disconnect(*args): # Accept potential args
    sid = request.sid; log.info(f"Client disconnected: {sid}")
    # Correct Indentation
    if sid in clients:
        clients[sid]['client_connected'] = False # Mark as disconnected
        log.info(f"[{sid}] Putting 'stop' action on task queue for disconnect.")
        task_queue.put({'action': 'stop', 'sid': sid}) # Signal processor to stop task for this SID
        del clients[sid] # Remove client state immediately
        log.info(f"[{sid}] Client state removed.")
    else:
        log.warning(f"Disconnect for unknown sid: {sid}")
    # End Correct Indentation

@socketio.on('start_stream')
def handle_start_stream(data):
    sid = request.sid; log.info(f"[{sid}] Received start_stream event.")
    # Correct Indentation
    if sid in clients:
        clients[sid]['client_connected'] = True
        log.info(f"[{sid}] Putting 'start' action on task queue.")
        task_queue.put({'action': 'start', 'sid': sid})
    else:
        log.warning(f"[{sid}] 'start_stream' for unknown client.")
    # End Correct Indentation

@socketio.on('stop_stream')
def handle_stop_stream():
    sid = request.sid; log.info(f"[{sid}] Received stop_stream event (user ended session).")
    # Correct Indentation
    if sid in clients:
        clients[sid]['client_connected'] = False
        log.info(f"[{sid}] Putting 'stop' action on task queue due to user stop.")
        task_queue.put({'action': 'stop', 'sid': sid})
    else:
        log.warning(f"[{sid}] 'stop_stream' for unknown client.")
    # End Correct Indentation

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sid = request.sid
    # Correct Indentation
    if sid in clients and clients[sid].get('client_connected', False):
        audio_b64 = data.get('audio')
        if audio_b64:
            task_queue.put({'action': 'audio', 'sid': sid, 'data': audio_b64}) # Put command on queue
    # End Correct Indentation
    # else: pass # Ignore chunks from disconnected clients

# --- Main Execution ---
if __name__ == '__main__':
    log.info("Starting Flask-SocketIO server...")
    if not OPENAI_API_KEY: log.critical("CRITICAL: OPENAI_API_KEY missing!")
    else:
        start_asyncio_thread()
        log.info(f"Starting server with async_mode='{async_mode}'...")
        # Make sure to install required packages: pip install Flask Flask-SocketIO python-dotenv websockets==11.0.3 numpy pyaudio
        socketio.run(app, host='0.0.0.0', port=5050, debug=False, use_reloader=False, log_output=True)
        # --- Cleanup ---
        log.info("Flask server shutting down...")
        task_queue.put(None) # Signal processor thread to stop
        if asyncio_thread and asyncio_thread.is_alive():
             log.info("Waiting for asyncio thread...")
             if asyncio_loop and asyncio_loop.is_running(): asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
             asyncio_thread.join(timeout=5)
             if asyncio_thread.is_alive(): log.warning("Asyncio thread did not stop.")
        log.info("Shutdown complete.")