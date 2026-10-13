"""Read and validate the map with Claude's porygon MCP workflow."""
import sys,asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
OUT=Path(__file__).resolve().parents[4]/'gba/art/violet-city/evidence'
async def main():
 root=str(Path(sys.argv[1]).resolve());report={}
 async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','porygon.server'])) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize()
   for name,args in [('get_layout',{'layout':'LAYOUT_VIOLET_CITY'}),('read_blockdata',{'layout':'LAYOUT_VIOLET_CITY'}),('validate_scripts',{'map':'VioletCity'}),('get_connections',{'map':'VioletCity'}),('poryscript_status',{})]:
    result=await s.call_tool(name,{**args,'root':root});assert not result.isError,(name,result);report[name]=[c.text for c in result.content if hasattr(c,'text')]
 (OUT/'porygon.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
asyncio.run(main())
