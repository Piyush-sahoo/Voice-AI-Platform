import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("backend/.env.local")

async def check_analysis():
    uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(uri)
    db = client.get_database("vobiz_calls")
    
    # Get the latest call
    call = await db.calls.find_one(sort=[("created_at", -1)])
    
    if call:
        print(f"Latest Call ID: {call.get('call_id')}")
        print(f"Status: {call.get('status')}")
        analysis = call.get("analysis")
        if analysis:
            print("\n✅ Analysis Found!")
            print(f"Success: {analysis.get('success')}")
            print(f"Sentiment: {analysis.get('sentiment')}")
            print(f"Summary: {analysis.get('summary')}")
        else:
            print("\n❌ No analysis data found.")
    else:
        print("No calls found.")

if __name__ == "__main__":
    asyncio.run(check_analysis())
