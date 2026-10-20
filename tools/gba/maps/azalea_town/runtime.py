"""Azalea exterior: native walking, closed entrances, forest/wall/ledge and saves."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from johto_connections import runtime as r
start=r.MAIN[:r.MAIN.index('  // Actual east connection')];end=r.MAIN[r.MAIN.index('  unsigned status=call("TrySavingData"'):]
steps=r'''
 go(50,20,18);shot("main-street");step(LEFT,6);at(50,14,18,"main-street-to-Kurt-spur");step(UP,6);at(50,14,12,"Kurt-door-approach");shot("Kurt-house");step(UP,1);at(50,14,12,"Kurt-interior-not-wired");
 step(RIGHT,6);at(50,20,12,"Kurt-yard-path-entry");step(UP,3);at(50,20,9,"Kurt-rear-firewood-approach");shot("Kurt-firewood-yard");step(UP,1);at(50,20,9,"Kurt-firewood-blocks");step(RIGHT,1);at(50,20,9,"Kurt-retained-east-forest-blocks");
 step(DOWN,1);step(LEFT,1);at(50,20,10,"Kurt-kiln-east-wall-blocks");shot("Kurt-kiln-east");step(DOWN,2);step(LEFT,2);at(50,18,12,"Kurt-kiln-front-approach");shot("Kurt-kiln-front");step(UP,1);at(50,18,12,"Kurt-kiln-front-blocks");
 go(50,16,12);shot("Kurt-expanded-property");go(50,14,12);
 step(DOWN,6);step(RIGHT,11);step(UP,2);at(50,25,16,"Center-door-approach");shot("pokemon-center");step(UP,1);at(50,25,16,"Center-interior-not-wired");
 step(DOWN,2);step(RIGHT,9);step(UP,4);at(50,34,14,"Mart-door-approach");shot("poke-mart");step(UP,1);at(50,34,14,"Mart-interior-not-wired");
 go(50,14,18);step(DOWN,9);step(RIGHT,14);at(50,28,27,"southern-loop");shot("southern-loop");step(UP,3);at(50,28,24,"eastern-Gym-loop");step(LEFT,3);at(50,26,24,"Gym-lawn-edge");shot("gym-east");
 go(50,20,25);shot("Azalea-gym");step(UP,1);at(50,20,25,"Gym-interior-not-wired");
 go(50,28,24);step(RIGHT,6);step(UP,2);at(50,34,22,"ordinary-house-approach");shot("ordinary-house");step(UP,1);at(50,34,22,"house-interior-not-wired");
 go(50,38,17);step(RIGHT,8);step(DOWN,1);step(RIGHT,2);step(UP,2);at(50,48,16,"well-court-approach");shot("Slowpoke-Well");step(UP,1);at(50,48,16,"well-interior-not-wired");
 go(50,43,10);shot("well-west-stairs");step(RIGHT,2);at(50,45,10,"well-side-stairs-eastbound");shot("well-upper-landing");step(LEFT,2);at(50,43,10,"well-side-stairs-westbound");
 go(50,43,12);step(LEFT,1);at(50,43,12,"well-outer-west-wall");step(RIGHT,1);at(50,43,12,"well-inner-west-wall");
 go(50,49,17);step(UP,1);at(50,49,16,"well-south-stairs-northbound");shot("well-south-stairs");step(DOWN,1);at(50,49,17,"well-south-stairs-southbound");
 go(50,52,16);step(DOWN,1);at(50,52,18,"well-lower-return-down-ledge");shot("well-lower-return");step(UP,1);at(50,52,18,"well-lower-return-blocks-climb");
 go(50,52,9);step(UP,1);at(50,52,8,"well-ramp-east-landing");step(LEFT,1);at(50,52,8,"well-ramp-face-blocks");shot("well-ramp-landing");
 go(50,52,12);step(RIGHT,1);at(50,52,12,"well-outer-east-wall");shot("well-east-corridor");
 go(50,49,17);step(DOWN,2);step(LEFT,2);step(DOWN,1);at(50,47,21,"east-field-south-ledge-jump");step(UP,1);at(50,47,21,"east-field-ledge-blocked-return");shot("eastern-field");
 go(50,48,24);step(RIGHT,15);at(50,62,24,"Route33-integration-pending-boundary");shot("east-approach");
 go(50,14,18);step(LEFT,6);at(50,8,18,"Ilex-gate-approach");step(LEFT,1);at(50,8,18,"Ilex-gate-interior-pending");shot("Ilex-gate");
 go(50,8,17);step(LEFT,1);at(50,8,17,"Ilex-gate-northern-bypass-blocked");shot("gate-north-closure");
 go(50,8,20);step(LEFT,1);at(50,8,20,"Ilex-gate-southern-bypass-blocked");shot("gate-south-closure");
 go(50,9,18);step(LEFT,1);at(50,8,18,"Ilex-gate-approach-preserved");shot("gate-closed-seams");
 go(50,11,22);step(LEFT,1);at(50,10,22,"west-lawn");step(LEFT,1);at(50,10,22,"west-forest-blocks");shot("western-woods");
 go(50,38,18);step(DOWN,1);at(50,38,18,"southern-forest-footprint");shot("southern-woods");
 go(50,20,18);shot("save-Azalea");
'''
r.MAIN=(start+steps+end).replace('at(11,27,18','at(50,20,18').replace('cold-reload-new-bark','cold-reload-Azalea')
if __name__=='__main__':r.main()
