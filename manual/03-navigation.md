## SECTION 03: NAVIGATION

The universe is a difficult place to navigate. To begin, use the `nav` command to list available hyperspace links, planets, and nearby structures. Ships have a class designation based on their outfit space:

- 1: Junk [JNK]
- 2: Satellite [SAT]
- 4: Meteor [MET]
- 8: Asteroid [AST]
- 16: Lunar [LUN]
- 32: Planetary [PLA]
- 64: Giant [GIA]
- 128: Dwarf [DWA]
- 256: Stellar [STE]
- 512: Nebula [NEB]
- 1024: Galaxy [GAL]

Use the `jump` command with the link ID to jump. You need 100% warp charge to jump, however only some of the charge will be consumed. How much charge is consumed depends on the drag value of the hyperspace link. Warp engines can be charged by directing power to them; if not set to full power, they will be unable to reach 100% charge, but will still charge partially (albeit at a slower rate). Overcharging warp engines will cause them to charge faster, but will not grant additional charge beyond 100%. The greater a structure's mass, the longer it will take to charge. Jettisoning cargo can be used to provide a quick escape if not enough time is present to fully charge the warp engines.

Below is a table relating link IDs to headings:

- `0`: 315 degrees, X=-1, Y=-1 (northwest)
- `1`: 0 degrees, X=0, Y=-1 (north)
- `2`: 45 degrees, X=1, Y=-1 (northeast)
- `3`: 270 degrees, X=-1, Y=0 (west)
- `4`: 90 degrees, X=1, Y=0 (east)
- `5`: 225 degrees, X=-1, Y=1 (southwest)
- `6`: 180 degrees, X=0, Y=-1 (south)
- `7`: 135 degrees, X=1, Y=-1 (southeast)

The `jump` command can also be given the IDs of other ships as arguments, if you wish to jump an entire fleet at once. Remote jump initiation will not function if you do not have high enough reputation with the ship's owner, or if an operator has transferred their control core to the ship.

Antigravity engines are used to land and take off from planets, with the `land` and `launch` commands respectively. Planet IDs are listed in the output from the `nav` command. Antigravity engines operate instantly, but can only lift a limited amount of mass. As a result, ships with large quantities of outfits or cargo will need larger antigravity engines to compensate for the additional load.

Systems vary in their available resources; each system carries a specific type of ore, with varying densities. Planets can be used to construct bases, with the exception of gas giants. Each type also carries their own unique traits:

- Gas: Various gases can be collected using mining beams, but no bases can be constructed.
- Barren: Causes additional heat production based on the structure's size. Bases can have up to 2048 outfit space.
- Frozen: No special traits. Bases can have up to 2048 outfit space.
- Greenhouse: Various gases can be collected using mining beams, and causes additional heat production based on the structure's size. Bases can have up to 2048 outfit space.
- Habitable: Bases are extremely cheap to construct, and can have up to 4096 outfit space. Living spaces don't require Distribution Centers and have increased capacity.

To dock to another structure, use the `dock` command. The `dock` command can be executed on a remote ship using the `rdock` command. Ships can only be docked to one structure at a time, and ships cannot be docked to if they are already docked to another structure. Other types of structures, such as bases, cannot be docked but can be docked to. The `eject` command is used to eject docked structures; passing without arguments will eject all docked structures.
