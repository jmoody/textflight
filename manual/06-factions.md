## SECTION 06: FACTIONS

Factions provide a convenient way for you to share resources with the people you're playing with, as well as keep track of your friends (and enemies) using the reputation system.

To join a faction or create a new one, simply use the `faction_join` command. Faction names cannot have spaces, however faction passwords can.

To view information on your current faction, use the `faction_info` command; you can also use this to view other factions. You can leave your faction at any time with the `faction_leave` command.

If you are a faction owner, you can use `faction_rename` to change the name of your faction, and `faction_passwd` to change the password required to join it. You can also kick members from the faction using `faction_kick`. Faction owners cannot leave their faction unless there are no other members remaining; if you wish to do so anyways, transfer ownership to someone else with `faction_chown`.

Systems and planets can be claimed by factions; using `faction_claim` in space will claim the system you're currently in, and using it on the surface of a planet will claim that planet. You cannot claim systems or planets if there are any structures from an opposing faction present.

Claimed systems and planets can be named with the `faction_name` command. These names can contain spaces. Claims can also be released using the `faction_release` command; any names assigned to systems or planets will be removed if this command is used.
