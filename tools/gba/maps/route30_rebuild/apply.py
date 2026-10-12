import sys,asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from porygon.core.blockdata import Blockdata
async def main():
 root=Path(__file__).resolve().parents[4];game=Path(sys.argv[1]).resolve();raw=(root/'gba/art/route30-rebuild/source/proposed-map.bin').read_bytes();bd=Blockdata.decode(raw,35,86)
 async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','porygon.server'])) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize();result=await s.call_tool('write_blockdata',{'layout':'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH','grid':bd.to_grid(),'root':str(game)});assert not result.isError,result
   output=game/'data/layouts/CherrygroveRoute30Approach/map.bin';assert output.read_bytes()==raw
   (root/'gba/art/route30-rebuild/evidence/porygon-write.json').write_text(json.dumps({'bytes_verified':len(raw),'tool':'write_blockdata','layout':'LAYOUT_CHERRYGROVE_ROUTE30_APPROACH','result':[c.text for c in result.content if c.type=='text']},indent=2)+'\n');print('Route 30 applied through porygon MCP; exact encoded bytes verified')
asyncio.run(main())
