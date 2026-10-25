"""Original FRLG material taxonomy, checked against the numbered donor atlas.
No rejected artwork, layout, native palette or cell assignment is imported.
"""
TOWN={}
def tag(label,ids):
 for m in ids:TOWN[m]=label
tag('tree_canopy_trunk_root',[0xe,0xf,0x14,0x15,0x16,0x17,0x1c,0x1d,0x1e,0x1f,0x24,0x25,0x26,0x27])
tag('lawn',[8,9,0x11,0x285,0x286,0x28c,0x296,0x297,0x2be])
tag('lawn_contact_shadow',[0x288,0x28e,0x28f,0x290,0x294,0x295,0x29e,0x29f,0x2a6,0x2a7,0x2ae,0x2af,0x2c6,0x2c7,0x2cd])
tag('shore_lip_and_water',[0x123,0x12a,0x12c,0x2d1,0x2d2]);tag('water',[0x12b])
tag('flowers_on_lawn',[4]);tag('sign',[2,3,0x2a5,0x2ad]);tag('picket_fence',[0x284,0x287])
tag('home_roof_eave',[0x281,0x282,0x283,0x289,0x28a,0x28b,0x291,0x292,0x293])
tag('home_wall_window',[0x298,0x299,0x29a,0x29b,0x29c,0x2a0,0x2a1,0x2a2,0x2a4]);tag('home_entrance',[0x2a3])
tag('lab_roof_rim_chimney',[0x2a8,0x2a9,0x2ab,0x2b0,0x2b1,0x2b3,0x2b4,0x2b5,0x2b6,0x2b8,0x2b9,0x2bb,0x2bc,0x2bd])
tag('lab_wall_window',[0x2bf,0x2c0,0x2c1,0x2c2,0x2c3,0x2c4,0x2c5,0x2c8,0x2c9,0x2cb,0x2cc,0x2ce,0x2d0,0x2d8]);tag('lab_entrance',[0x2ac])
def material(n,x,y,mid):
 if n=='ApocPalletTown':return TOWN[mid]
 if mid==8:return 'void'
 # Explicit footprints measured on each original numbered reference, including mixed edge cells.
 features=[]
 if n in ('ApocPalletRedHouse1F','ApocPalletOakHouse'):
  features=[('wall_cap_face',0,0,12,1),('kitchen_sink_cabinet',1 if n.endswith('1F') else 0,1,3 if n.endswith('1F') else 2,2),('telephone',4 if n.endswith('1F') else 3,1,4 if n.endswith('1F') else 3,2),('television',6 if n.endswith('1F') else 5,1,6 if n.endswith('1F') else 5,2),('table_chairs_rug',4,3,9,6),('exit_rug',3,8,5,8)]
  if n.endswith('1F'):features += [('stairs_treads_landing',10,1,12,3),('plant',1,6,1,7),('plant',12,6,12,7)]
  else:features += [('bookshelf',11,1,12,2),('plant',0,7,0,8),('plant',12,7,12,8),('family_wall_map',9,1,9,1)]
 elif n=='ApocPalletRedHouse2F':
  features=[('wall_cap_face',1,0,11,1),('personal_computer_desk',1,1,2,2),('chair',3,1,3,2),('bookshelf',4,1,5,2),('stairs_treads_landing',8,1,10,3),('wall_notice',11,1,11,1),('bed',2,4,3,6),('rug',4,4,8,7),('television_console',6,4,6,5)]
 elif n=='ApocPalletLab':
  features=[('wall_cap_face',0,0,12,1),('research_machines',0,1,3,2),('desk',4,1,5,2),('wall_notices',6,0,7,1),('display',8,0,8,1),('bookshelf',9,1,12,2),('bookshelf',0,8,4,9),('bookshelf',8,8,12,9),('reference_books',0,3,0,4),('research_machine',1,3,2,5),('research_table',8,4,10,5),('plant',0,11,0,12),('plant',12,11,12,12),('exit_rug',5,12,7,12)]
 label='laboratory_tile_floor' if n=='ApocPalletLab' else 'wood_floor'
 for tag,x0,y0,x1,y1 in features:
  if x0<=x<=x1 and y0<=y<=y1:label=tag
 return label
