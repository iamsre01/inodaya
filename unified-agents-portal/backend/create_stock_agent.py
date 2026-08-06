#!/usr/bin/env python3
"""
Script to create Stock Analysis Agent with daily post-market scheduling
"""
import sys
sys.path.insert(0, '/workspace/unified-agents-portal/backend')

from models import engine, Base, Agent, Task, SessionLocal
from datetime import datetime

def create_stock_analysis_agent():
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if agent already exists
        existing = db.query(Agent).filter(Agent.name == 'Stock Analysis Agent').first()
        if existing:
            print(f'⚠️  Agent already exists: {existing.name}')
            print(f'   ID: {existing.id}, Active: {existing.is_active}')
            return existing.id
        
        # Create Stock Analysis Agent
        stock_agent = Agent(
            name='Stock Analysis Agent',
            description='Analyzes stock market data after market hours to provide buy/sell recommendations and focus stocks',
            agent_type='api',
            config={
                'provider': 'openai',
                'model': 'gpt-4-turbo',
                'system_prompt': '''You are an expert stock market analyst. Your task is to:
1. Analyze market trends, volume, and price movements
2. Identify stocks with strong momentum or undervalued opportunities
3. Provide clear buy/sell/hold recommendations with reasoning
4. Highlight 3-5 stocks to focus on for the next trading day
5. Consider technical indicators (RSI, MACD, Moving Averages) and fundamental factors
6. Always include risk warnings and suggest position sizing

Format your analysis clearly with sections:
- Market Overview
- Top Picks to Buy
- Stocks to Watch
- Stocks to Avoid/Sell
- Risk Assessment
- Action Plan for Tomorrow''',
                'temperature': 0.7,
                'max_tokens': 2000
            },
            is_active=True
        )
        
        db.add(stock_agent)
        db.commit()
        db.refresh(stock_agent)
        print(f'✅ Created Stock Analysis Agent with ID: {stock_agent.id}')
        
        # Create daily task (runs at 4:30 PM EST, after US market closes at 4:00 PM)
        # Cron: 30 16 * * 1-5 (Monday-Friday at 4:30 PM)
        stock_task = Task(
            name='Daily Post-Market Stock Analysis',
            description='Run comprehensive stock market analysis after market close to generate next-day recommendations. Parameters: US Market, Focus on Technology/Healthcare/Finance/Energy sectors',
            agent_id=stock_agent.id,
            schedule='30 16 * * 1-5',  # Weekdays at 4:30 PM
            is_active=True
        )
        
        db.add(stock_task)
        db.commit()
        db.refresh(stock_task)
        print(f'✅ Created Daily Stock Analysis Task with ID: {stock_task.id}')
        print(f'📅 Schedule: Weekdays at 4:30 PM EST (after market close)')
        print(f'⏰ Next run will be calculated automatically')
        
        return stock_agent.id
        
    except Exception as e:
        db.rollback()
        print(f'❌ Error: {str(e)}')
        raise
    finally:
        db.close()

if __name__ == '__main__':
    agent_id = create_stock_analysis_agent()
    print('\n🎉 Stock Analysis Agent setup complete!')
    print('\nNext Steps:')
    print('1. Add your OpenAI API key in the API Keys section')
    print('2. View the agent in the Dashboard graph')
    print('3. Manually trigger the task to test it')
    print('4. Wait for automatic execution at 4:30 PM on weekdays')
