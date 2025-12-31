"""
Setup LiveKit inbound trunk and dispatch rule for Vobiz calls.
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import api
from livekit.protocol import sip as sip_proto

load_dotenv(".env.local")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
VOBIZ_INBOUND_NUMBER = os.getenv("VOBIZ_INBOUND_NUMBER", "+912271264190")
AGENT_NAME = "voice-assistant"

async def main():
    lk = api.LiveKitAPI()
    
    project_id = LIVEKIT_URL.replace("wss://", "").replace("ws://", "").split(".")[0]
    sip_endpoint = f"{project_id}.sip.livekit.cloud"
    
    print("="*60)
    print("LIVEKIT INBOUND SETUP")
    print("="*60)
    print(f"\nProject: {project_id}")
    print(f"SIP Endpoint: {sip_endpoint}")
    print(f"Inbound Number: {VOBIZ_INBOUND_NUMBER}")
    
    try:
        # Clean up existing config
        print("\n[1] Cleaning existing configuration...")
        rules = await lk.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
        for r in rules.items:
            await lk.sip.delete_sip_dispatch_rule(
                api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=r.sip_dispatch_rule_id)
            )
        
        trunks = await lk.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
        for t in trunks.items:
            await lk.sip.delete_sip_trunk(
                api.DeleteSIPTrunkRequest(sip_trunk_id=t.sip_trunk_id)
            )
        print("    Done")
        
        # Create Inbound Trunk
        print(f"\n[2] Creating inbound trunk for {VOBIZ_INBOUND_NUMBER}...")
        trunk = await lk.sip.create_sip_inbound_trunk(
            api.CreateSIPInboundTrunkRequest(
                trunk=api.SIPInboundTrunkInfo(
                    name="Vobiz Inbound",
                    numbers=[VOBIZ_INBOUND_NUMBER],
                    allowed_addresses=["0.0.0.0/0"],  # Accept from any IP
                    krisp_enabled=True,
                )
            )
        )
        trunk_id = trunk.sip_trunk_id
        print(f"    Created: {trunk_id}")
        
        # Create Dispatch Rule with agent dispatch
        print(f"\n[3] Creating dispatch rule for agent '{AGENT_NAME}'...")
        dispatch_rule = sip_proto.SIPDispatchRuleInfo(
            name="Inbound Agent Dispatch",
            trunk_ids=[trunk_id],
            rule=sip_proto.SIPDispatchRule(
                dispatch_rule_individual=sip_proto.SIPDispatchRuleIndividual(
                    room_prefix="call-",
                )
            ),
        )
        dispatch_rule.room_config.CopyFrom(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME)]
            )
        )
        
        result = await lk.sip.create_sip_dispatch_rule(
            api.CreateSIPDispatchRuleRequest(dispatch_rule=dispatch_rule)
        )
        print(f"    Created: {result.sip_dispatch_rule_id}")
        
        # Summary
        print("\n" + "="*60)
        print("SETUP COMPLETE")
        print("="*60)
        print(f"""
Inbound Trunk: {trunk_id}
  Number: {VOBIZ_INBOUND_NUMBER}
  
Dispatch Rule: {result.sip_dispatch_rule_id}
  Agent: {AGENT_NAME}

IMPORTANT - Set Vobiz Primary URI to:
  {sip_endpoint}
""")
        
    finally:
        await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())
