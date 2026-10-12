import asyncio,json,sys
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path
async def main():
 if len(sys.argv)!=3:raise SystemExit('usage: porygon_probe.py EXPANSION_CHECKOUT OUTPUT_JSON')
 root=str(Path(sys.argv[1]).resolve());output=Path(sys.argv[2]).resolve()
 params=StdioServerParameters(command=sys.executable,args=['-m','porygon.server'])
 async with stdio_client(params) as (reader,writer):
  async with ClientSession(reader,writer) as s:
   await s.initialize();t=await s.list_tools();results={'tools':[v.name for v in t.tools],'checks':{}}
   for name in ['CherrygroveCity','CherrygroveRoute29Approach','CherrygroveRoute30Approach','NewBarkTown','JohtoRoute31','VioletCityEntrance']:
    results['checks'][name]={}
    for method in ['get_connections','validate_scripts']:
     r=await s.call_tool(method,{'map':name,'root':root})
     results['checks'][name][method]={'isError':r.isError,'content':[v.text for v in r.content if v.type=='text']}
   output.write_text(json.dumps(results,indent=2)+'\n');print('MCP tool count',len(t.tools));print('Validation report written')
asyncio.run(main())
