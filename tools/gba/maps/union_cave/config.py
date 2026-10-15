"""Reviewed native registration of visible HGSS cave sections and original warp topology."""
FLOORS={
 '1f':{'name':'UnionCaveRoute32Entrance','id':'MAP_UNION_CAVE_ROUTE32_ENTRANCE','layout':'LAYOUT_UNION_CAVE_ROUTE32_ENTRANCE','set':'union_cave','symbol':'UnionCave','size':(34,60),'map_num':46,
       'ladders':[(5,5),(7,57)],'doors':[(28,19),(28,58)],'stone_boxes':[(80,240,112,280),(464,576,496,632)],
       'warps':[(28,19,'MAP_JOHTO_ROUTE32',1),(5,5,'MAP_UNION_CAVE_B1F',0),(7,57,'MAP_UNION_CAVE_B1F',1)]},
 'b1f':{'name':'UnionCaveB1F','id':'MAP_UNION_CAVE_B1F','layout':'LAYOUT_UNION_CAVE_B1F','set':'union_cave_b1f','symbol':'UnionCaveB1F','size':(36,52),'map_num':47,
       'ladders':[(31,35),(4,48),(29,46),(4,5),(4,12)],'doors':[],'stone_boxes':[(448,496,480,544),(128,200,144,216)],
       'warps':[(31,35,'MAP_UNION_CAVE_ROUTE32_ENTRANCE',1),(4,48,'MAP_UNION_CAVE_ROUTE32_ENTRANCE',2),(29,46,'MAP_UNION_CAVE_B2F',0)]},
 'b2f':{'name':'UnionCaveB2F','id':'MAP_UNION_CAVE_B2F','layout':'LAYOUT_UNION_CAVE_B2F','set':'union_cave_b2f','symbol':'UnionCaveB2F','size':(40,47),'map_num':48,
       'ladders':[(4,5)],'doors':[],'stone_boxes':[],
       'warps':[(4,5,'MAP_UNION_CAVE_B1F',2)]}
}
# Original warp graph comes from pret/pokeheartgold zone_event records. Overview
# images project DS Z at roughly 12 px per unit and crop/stitch visible sections;
# DS coordinates cannot be pasted into the native image grid. Register against
# actor/item landmarks and branch ends, retaining the owner-approved proportions.
# Original off-image Alph transit rooms/warps remain unimplemented, not rerouted.
