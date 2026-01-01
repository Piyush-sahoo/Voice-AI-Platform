"""
Database Cleanup Script - Clears test data from MongoDB Atlas
"""
from pymongo import MongoClient

# MongoDB Atlas connection
MONGODB_URI = "mongodb+srv://piyush_db_user:MySecurePass123@livekitvobiz.umwvp9s.mongodb.net/vobiz_calls"
DB_NAME = "vobiz_calls"

def cleanup_database():
    """Remove all test SIP configs and phone numbers from the database."""
    print("🔗 Connecting to MongoDB Atlas...")
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    
    try:
        # Clear SIP configs
        sip_result = db.sip_configs.delete_many({})
        print(f"✅ Deleted {sip_result.deleted_count} SIP configs")
        
        # Clear phone numbers (they reference SIP configs)
        phone_result = db.phone_numbers.delete_many({})
        print(f"✅ Deleted {phone_result.deleted_count} phone numbers")
        
        print("\n🎉 Database cleanup complete!")
        
        # Verify cleanup
        sip_count = db.sip_configs.count_documents({})
        phone_count = db.phone_numbers.count_documents({})
        print(f"\n📊 Remaining counts:")
        print(f"   SIP Configs: {sip_count}")
        print(f"   Phone Numbers: {phone_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()
        print("\n🔒 Connection closed")

if __name__ == "__main__":
    cleanup_database()
