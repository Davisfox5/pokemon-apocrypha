#!/usr/bin/env python3
"""Apply the inspected HGSS-block proposal through porygon MCP."""
import sys,asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from porygon.core.blockdata import Blockdata
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'gba/art/route30-hgss-blocks'
async def main():
 game=Path(sys.argv[1]).resolve();raw=(OUT/'source/proposed-map.bin').read_bytes();bd=Blockdata.decode(raw,35,86)
 async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','porygon.server'])) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize();result=await s.call_tool('write_blockdata',{'layout':'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH','grid':bd.to_grid(),'root':str(game)});assert not result.isError,result
   assert (game/'data/layouts/CherrygroveRoute30Approach/map.bin').read_bytes()==raw
   (OUT/'evidence/porygon-write.json').write_text(json.dumps({'tool':'write_blockdata','layout':'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH','bytes_verified':len(raw)},indent=2)+'\n')
   metadata=json.loads((game/'data/maps/CherrygroveRoute30Approach/map.json').read_text())
   if not any(e['x']==8 and e['y']==24 for e in metadata['bg_events']):
    result=await s.call_tool('add_bg_event',{'map':'CherrygroveRoute30Approach','event':{'type':'sign','x':8,'y':24,'elevation':0,'player_facing_dir':'BG_EVENT_PLAYER_FACING_ANY','script':'CherrygroveRoute30Approach_RouteSign'},'root':str(game)})
    assert not result.isError,result
 print('HGSS blockdata applied byte-exactly')
asyncio.run(main())
