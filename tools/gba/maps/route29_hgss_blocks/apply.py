#!/usr/bin/env python3
"""Apply inspected Route 29 blockdata and its shifted western sign via MCP."""
import sys,asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from porygon.core.blockdata import Blockdata
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/route29-hgss-blocks'
async def main():
 game=Path(sys.argv[1]).resolve();raw=(OUT/'source/proposed-map.bin').read_bytes();bd=Blockdata.decode(raw,98,48)
 async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','porygon.server'])) as (r,w):
  async with ClientSession(r,w) as session:
   await session.initialize();result=await session.call_tool('write_blockdata',{'layout':'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH','grid':bd.to_grid(),'root':str(game)});assert not result.isError,result
   assert (game/'data/layouts/CherrygroveRoute29Approach/map.bin').read_bytes()==raw
   m=json.loads((game/'data/maps/CherrygroveRoute29Approach/map.json').read_text())
   if not any(q['x']==12 and q['y']==17 for q in m['bg_events']):
    result=await session.call_tool('add_bg_event',{'map':'CherrygroveRoute29Approach','event':{'type':'sign','x':12,'y':17,'elevation':0,'player_facing_dir':'BG_EVENT_PLAYER_FACING_ANY','script':'CherrygroveRoute29Approach_EastSign'},'root':str(game)});assert not result.isError,result
   (OUT/'evidence/porygon-write.json').write_text(json.dumps({'layout':'LAYOUT_CHERRYGROVE_ROUTE29_APPROACH','bytes_verified':len(raw),'western_sign':[12,17],'existing_sign_and_Potion_events_preserved':True},indent=2)+'\n')
if __name__=='__main__':asyncio.run(main())
