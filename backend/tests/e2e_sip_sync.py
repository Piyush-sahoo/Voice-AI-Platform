
import asyncio
import os
import sys
import uuid
import httpx
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from livekit import api
from dotenv import load_dotenv

# Load env from backend/.env.local if exists, else .env
# Determine environment and load .env.local
# Try Docker path header
if os.path.exists("/app/.env.local"):
    load_dotenv("/app/.env.local")
# Try local development path (relative to this script in backend/tests)
elif os.path.exists(os.path.join(os.path.dirname(__file__), "../.env.local")):
    load_dotenv(os.path.join(os.path.dirname(__file__), "../.env.local"))
else:
    print("WARNING: .env.local not found!")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Config Service URL (Internal to container)
CONFIG_SERVICE_URL = "http://localhost:8002/api"

async def test_sip_sync():
    print(f"Testing SIP Sync against {CONFIG_SERVICE_URL} and LiveKit Url: {LIVEKIT_URL}...")
    
    lk_api = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    try:
        # ==========================================
        # 1. Test Outbound SIP Config (Trunk)
        # ==========================================
        print("\n--- 1. Testing Outbound SIP Config ---")
        sip_name = f"AutoTest-SIP-{uuid.uuid4().hex[:6]}"
        
        # User credentials (verified)
        sip_payload = {
            "name": sip_name,
            "sip_domain": "383a51fe.sip.vobiz.ai",
            "sip_username": "piyush",
            "sip_password": "password@123",
            "from_number": "+912271264190",
            "trunk_id": None, 
            "description": "E2E Test Config - Verification",
            "is_default": False
        }

        # create via API
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{CONFIG_SERVICE_URL}/sip-configs", json=sip_payload, headers={"X-Workspace-ID": "test-ws"})
            if resp.status_code != 200:
                print(f"FAILED to update SIP config: {resp.text}")
                return
            sip_data = resp.json()
            print(f"Created SIP Config: {sip_data['sip_id']}")
            
            # Verify in LiveKit
            trunks = await lk_api.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())
            found_trunk = None
            for t in trunks.items:
                if t.name == sip_name:
                    found_trunk = t
                    break
            
            if found_trunk:
                print(f"✅ VERIFIED: LiveKit Outbound Trunk exists: {found_trunk.sip_trunk_id}")
            else:
                print(f"❌ FAILED: LiveKit Outbound Trunk NOT found for {sip_name}")
                return

            # Retrieve from API to confirm trunk_id stored
            resp = await client.get(f"{CONFIG_SERVICE_URL}/sip-configs/{sip_data['sip_id']}")
            current_sip = resp.json()
            if current_sip.get("trunk_id") == found_trunk.sip_trunk_id:
                print(f"✅ VERIFIED: DB stored correct trunk_id: {current_sip['trunk_id']}")
            else:
                print(f"❌ FAILED: DB trunk_id mismatch. Got {current_sip.get('trunk_id')}, expected {found_trunk.sip_trunk_id}")

            # Delete via API
            resp = await client.delete(f"{CONFIG_SERVICE_URL}/sip-configs/{sip_data['sip_id']}")
            if resp.status_code == 200:
                print(f"Deleted SIP Config: {sip_data['sip_id']}")
            else:
                print(f"FAILED to delete SIP config: {resp.text}")

            # Verify Deletion in LiveKit
            trunks = await lk_api.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())
            found_trunk = None
            for t in trunks.items:
                if t.sip_trunk_id == current_sip['trunk_id']: # Check ID directly
                    found_trunk = t
                    break
            
            if not found_trunk:
                 print(f"✅ VERIFIED: LiveKit Outbound Trunk DELETED.")
            else:
                 print(f"❌ FAILED: LiveKit Trunk still exists: {found_trunk.sip_trunk_id}")


        # ==========================================
        # 2. Test Inbound Phone Number
        # ==========================================
        print("\n--- 2. Testing Inbound Phone Number ---")
        phone_num = "+15559998888" # Unique test number
        phone_payload = {
            "number": phone_num,
            "label": "E2E Test Phone",
            "provider": "twilio"
        }

        # Create via API
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{CONFIG_SERVICE_URL}/phone-numbers", json=phone_payload, headers={"X-Workspace-ID": "test-ws"})
            if resp.status_code != 200:
                print(f"FAILED to update Phone: {resp.text}")
                return
            phone_data = resp.json()
            print(f"Created Phone Number: {phone_data['phone_id']}")
            
            # Check SIP URI response
            if phone_data.get("sip_uri"):
                print(f"✅ VERIFIED: API returned SIP URI: {phone_data['sip_uri']}")
            else:
                 print(f"❌ FAILED: API did not return SIP URI")

            # Verify LiveKit Inbound Trunk
            in_trunks = await lk_api.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
            found_in_trunk = None
            for t in in_trunks.items:
                if phone_num in t.numbers:
                    found_in_trunk = t
                    break
            
            if found_in_trunk:
                 print(f"✅ VERIFIED: LiveKit Inbound Trunk exists: {found_in_trunk.sip_trunk_id}")
            else:
                 print(f"❌ FAILED: LiveKit Inbound Trunk NOT found for {phone_num}")

            # Verify Dispatch Rule
            rules = await lk_api.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
            found_rule = None
            # We can't easily match rule name unless we know it exactly, but we can search specifically?
            # Or just check if any rule uses this trunk?
            if found_in_trunk:
                for r in rules.items:
                     if found_in_trunk.sip_trunk_id in r.trunk_ids:
                         found_rule = r
                         break
            
            if found_rule:
                print(f"✅ VERIFIED: LiveKit Dispatch Rule exists: {found_rule.sip_dispatch_rule_id}")
            else:
                print(f"❌ FAILED: LiveKit Dispatch Rule NOT found for Trunk {found_in_trunk.sip_trunk_id if found_in_trunk else 'N/A'}")

            # Delete via API
            resp = await client.delete(f"{CONFIG_SERVICE_URL}/phone-numbers/{phone_data['phone_id']}")
            if resp.status_code == 200:
                print(f"Deleted Phone Number: {phone_data['phone_id']}")
            else:
                print(f"FAILED to delete Phone: {resp.text}")

            # Verify Deletion in LiveKit
            if found_in_trunk:
                try:
                    # Try to fetch it directly or check list? checking list is safer
                     in_trunks = await lk_api.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
                     still_there = any(t.sip_trunk_id == found_in_trunk.sip_trunk_id for t in in_trunks.items)
                     if not still_there:
                         print(f"✅ VERIFIED: LiveKit Inbound Trunk DELETED.")
                     else:
                         print(f"❌ FAILED: LiveKit Inbound Trunk still exists.")
                except:
                    pass
            
            if found_rule:
                 rules = await lk_api.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
                 still_rule = any(r.sip_dispatch_rule_id == found_rule.sip_dispatch_rule_id for r in rules.items)
                 if not still_rule:
                      print(f"✅ VERIFIED: LiveKit Dispatch Rule DELETED.")
                 else:
                      print(f"❌ FAILED: LiveKit Dispatch Rule still exists.")

    except Exception as e:
        print(f"TEST EXCEPTION: {e}")
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(test_sip_sync())
