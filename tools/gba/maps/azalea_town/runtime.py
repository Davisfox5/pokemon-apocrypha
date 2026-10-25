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
 // Original HGSS spiral: town -> east corridor -> northern slope -> west court.
 go(50,49,20);shot("well-spiral-entry");step(UP,2);at(50,49,18,"well-east-access-landing");step(RIGHT,4);at(50,53,18,"well-east-corridor-south");shot("well-east-corridor");
 step(UP,9);at(50,53,9,"well-northern-ramp-east");shot("well-ramp-east");step(LEFT,7);at(50,46,9,"well-northern-ramp-west");shot("well-ramp-west");
 step(DOWN,6);at(50,46,15,"well-west-court-passage");step(RIGHT,2);at(50,48,15,"well-court-approach");shot("Slowpoke-Well");step(UP,1);at(50,48,15,"well-unwired-interior-blocked");
 step(DOWN,1);at(50,48,15,"well-south-back-wall-no-invented-stairs");shot("well-south-back-wall");
 step(RIGHT,2);at(50,50,15,"well-east-court-passage");step(UP,4);at(50,50,11,"well-east-court-return");shot("well-court-east");
 go(50,46,13);step(LEFT,1);at(50,46,13,"well-west-descending-rock-wall");shot("well-west-wall");
 go(50,53,13);step(RIGHT,1);at(50,53,13,"well-east-outer-rock-wall");step(LEFT,1);at(50,53,13,"well-east-inner-rock-wall");
 go(50,48,15);step(LEFT,2);step(UP,6);step(RIGHT,7);step(DOWN,9);step(LEFT,4);step(DOWN,2);at(50,49,20,"well-spiral-return-to-town");shot("well-spiral-return");
 go(50,47,19);step(DOWN,1);at(50,47,19,"well-sign-blocked");shot("well-sign");
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
