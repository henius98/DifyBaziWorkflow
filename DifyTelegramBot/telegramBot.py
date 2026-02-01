import aiohttp
import asyncio
import logging
import json
import datetime
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram_calendar.schemas import SimpleCalAct
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CustomSimpleCalendar(SimpleCalendar):
    async def process_selection(self, query: types.CallbackQuery, data: SimpleCalendarCallback) -> tuple:
        if data.act == SimpleCalAct.today:
            # Select today's date directly
            await query.answer()
            return True, datetime.datetime.now()
        return await super().process_selection(query, data)

load_dotenv()

# 1. Setup your Token from BotFather
TOKEN = os.getenv("TOKEN")
DIFY_WEBHOOK_URL = os.getenv("DIFY_WEBHOOK_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Function to send data to Dify
async def send_to_dify(user_id, date_value):
    headers = {
        "Content-Type": "application/json"
    }
    
    # payload matches the variables you set in Dify's "Start" node
    payload = {
        "target_date": date_value
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(DIFY_WEBHOOK_URL, json=payload, headers=headers) as resp:
            status = resp.status
            text = await resp.text()
            
            if status != 200:
                 raise Exception(f"Bad status {status}: {text}")
            
            try:
                return json.loads(text)
            except:
                return {"data": {"outputs": {"text": text}}}

# 2. Command: /start (Sends the calendar)
@dp.message(Command("start"))
async def start_command(message: types.Message):
    calendar = CustomSimpleCalendar()
    markup = await calendar.start_calendar()
    await message.answer("Please select a date", reply_markup=markup)

# 3. Callback: Handles clicking dates or switching months
@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback):
    calendar = CustomSimpleCalendar()
    selected, date = await calendar.process_selection(callback_query, callback_data)
    
    if selected:
        # 1. Format the date
        formatted_date = date.strftime("%Y-%m-%d")
        logging.info(f"User {callback_query.from_user.id} selected date: {formatted_date}")
        await callback_query.message.edit_text(f"Processing date: {formatted_date}")
        
        # 2. Send to Dify
        try:
            dify_response = await send_to_dify(callback_query.from_user.id, formatted_date)
            
            # 3. Get Dify's answer
            # Standard Dify Workflow API response structure check
            if 'message' in dify_response and isinstance(dify_response['message'], str):
                 result_text = dify_response['message']
            elif 'answer' in dify_response:
                 result_text = dify_response['answer']
            else:
                 result_text = dify_response.get('data', {}).get('outputs', {}).get('text')
            
            # Fallback for direct webhook response which might return outputs directly
            if not result_text:
                 result_text = str(dify_response)
            
            await callback_query.message.answer(f"Dify received: {result_text}")
            
        except Exception as e:
            logging.error(f"Error: {e}")
            await callback_query.message.answer(f"Error connecting to Dify: {e}")
            
        await callback_query.answer() # Stop loading animation
            
    else:
        # User is navigating months, do nothing
        pass

# 4. Scheduled Job: Runs everyday at a specific time
async def scheduled_dify_job():
    try:
        logging.info("Running scheduled Dify job...")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # We pass None as user_id since it's not used in send_to_dify currently
        response = await send_to_dify(None, today)
        logging.info(f"Scheduled Job Response: {response}")
        
    except Exception as e:
        logging.error(f"Scheduled Job Error: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Set bot commands in the menu
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Select Date"),
    ])
    
    # Initialize and start scheduler
    scheduler = AsyncIOScheduler()
    # Add job to run daily at 10:00 pm. Adjust hour/minute as needed.
    scheduler.add_job(scheduled_dify_job, 'cron', hour=20, minute=0)
    scheduler.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")