
class MISC:
	NAN = "Not a number."
	NO_STRUCT = "Unable to locate structure."
	NO_CARGO = "Cargo does not exist."
	NO_OP = "Unable to locate operator."
	COUNT_GTZ = "Count must be greater than zero."
	NOT_IN_FACTION = "You are not in a faction."
	PERMISSION_DENIED = "Permission denied."
	
	GOODBYE = "Goodbye."
	RESPAWN = "Please wait {remaining} seconds before respawning."
	UPDATED_EMAIL = "Updated email address."
	UPDATED_LANGUAGE = "Updated language."
	NO_LANGUAGE = "Language '{lang}' is not available."
	UPDATED_PASSWORD = "Updated password."
	ALREADY_PREMIUM = "This account already has premium status."
	REDEEM_SUCCESS = "Redeemed premium unlock code. Enjoy your premium status!"
	REDEEM_FAIL = "Premium code is invalid. Please check that the code was entered correctly."
	ALPHANUM_USERNAME = "Username can only contain letters and numbers."
	UPDATED_USERNAME = "Updated username."
	USERNAME_TAKEN = "Username '{username}' is already taken."
	INVALID_CHAT = "Invalid chat mode. Acceptable values between 0 and 3."
	SET_CHAT = "Updated chat settings."
	NO_COMMAND = "No command '{command}'."
	DISCONNECTED_BY = "You have been disconnected by another session."
	DISCONNECTED_EXISTING = "Disconnected an existing session from '{ip}'."
	LOGGED_IN = "Logged in as '{username}'."
	EMAIL_WARNING = "WARNING: Please set an email address with the 'email' command. This is used only for resetting your password."
	INCORRECT_LOGIN = "Incorrect username or password."
	REGISTERED = "Registration successful! Try logging in with 'login <username> <password>'."
	NOT_LOGGED_IN = "You are not logged in. Use 'login <username> <password>' to log in, or 'register <username> <password>' to create a new account."
	STRUCT_DESTROYED = "Your structure was destroyed. Log in again to respawn."
	HELP_MESSAGE = "No such command '{command}'. Use 'help' for a list of commands."

class USAGE:
	NAV = "Usage: nav [x] [y]"
	SCAN = "Usage: scan [structure ID]"
	DESTROY = "Usage: destroy <structure ID>"
	TARGET = "Usage: target <structure ID>"
	CANCEL = "Usage: cancel <queue ID> <count>"
	BASE = "Usage: base <outfit space> <name>"
	CONSTRUCT = "Usage: construct <outfit space> <name>"
	CRAFT = "Usage: craft [recipe ID] [count] [mark]"
	JETTISON = "Usage: jettison <cargo ID> <count>"
	FACT = "Usage: fact <message>"
	SUBS = "Usage: subs <username> <message>"
	LOCL = "Usage: locl <message>"
	HAIL = "Usage: hail <structure ID> <message>"
	AIRLOCK = "Usage: airlock <username>"
	BEAM = "Usage: beam <structure ID>"
	TRANS = "Usage: trans <structure ID>"
	EJECT = "Usage: eject [structure ID]"
	INSTALL = "Usage: install <cargo ID>"
	LOAD = "Usage: load <structure ID> <cargo ID> <count>"
	SET = "Usage: set <outfit ID> <setting>"
	SUPPLY = "Usage: supply <structure ID> <energy>"
	UNINSTALL = "Usage: uninstall <outfit ID>"
	DOCK = "Usage: dock <structure ID>"
	RDOCK = "Usage: rdock <structure ID>"
	LAND = "Usage: land <planet ID>"
	JUMP = "Usage: jump <link ID> [structure IDs]"
	FACTION_CHOWN = "Usage: faction_chown <username>"
	FACTION_INFO = "Usage: faction_info [faction name]"
	FACTION_JOIN = "Usage: faction_join <faction name> <password>"
	FACTION_KICK = "Usage: faction_kick <username>"
	FACTION_NAME = "Usage: faction_name <name>"
	FACTION_PASSWD = "Usage: faction_passwd <new password>"
	FACTION_RENAME = "Usage: faction_rename <new name>"
	REPF = "Usage: repf <faction name> [value]"
	REP = "Usage: rep <username> [value]"
	FACTION_REPF = "Usage: faction_repf <faction name> [value]"
	FACTION_REP = "Usage: faction_rep <username> [value]"
	EMAIL = "Usage: email <new email>"
	PASSWD = "Usage: passwd <new password>"
	REDEEM = "Usage: redeem <premium code>"
	USERNAME = "Usage: username <new username>"
	CHAT = "Usage: chat <mode>"
	LOGIN = "Usage: login <username> <password>"
	REGISTER = "Usage: register <username> <password>"
	LANGUAGE = "Usage: language [language code]"

class COMBAT:
	SHIELDS_UP = "Cannot destroy structure while its shields are up."
	NOT_POWERFUL = "Weapons are not powerful enough to destroy target."
	DESTROYED = "Destroyed structure '{id} {name}'."
	NO_TARGETS = "Weapons are not targeting any structures."
	TARGET = "{id} {name}"
	TARGET_SELF = "You cannot target yourself."
	ALREADY_TARGETING = "Already targeting '{id} {name}'."
	NO_WEAPONS = "Weapons are not online."
	TARGETING = "Targeting structure '{id} {name}'."
	SAFE = "Structure is invulnerable to damage for {remaining} seconds."
	SAFE_NOTARGET = "Cannot target structures while invulnerable; expires in {remaining} seconds."

class CRAFT:
	NO_QUEUE = "Queue does not exist."
	CANCELLED = "Cancelled {count} items queued for assembly."
	OUTFIT_SPACE_GTZ = "Outfit space must be greater than zero."
	OUTFIT_SPACE_LT = "Outfit space must be less than {max}."
	NEED_ROCKY = "Must be landed on a rocky planet to construct a base."
	TOTAL_SPACE_LT = "Total outfit space of all bases must be less than {max}."
	NEED_SHIPYARD = "Shipyard is required to construct new structures."
	SMALL_SHIPYARD = "Shipyard is not large enough to construct this structure."
	INSUFFICIENT = "Insufficient '{material}' (needs {count})."
	CREATED_STRUCT = "Successfully created structure '{name}' with size {size}."
	RECIPE = "[{index}] {name} (x{count})"
	NO_RECIPE = "Recipe does not exist."
	INSUFFICIENTS = "Insufficient resources."
	MISSING_MARK = "Mark not specified."
	NO_MARK = "Recipe has no mark options."
	QUEUED = "Queued {count} items for assembly."
	JETTISONED = "Jettisoned {count} items from cargo."
	QUEUE_NEVER = "never"
	QUEUE = "[{index}] {name} x{count} - {time}"
	QUEUE_EXTRA = "[{index}] {name} ({extra}) x{count} - {time}"

class FACTION:
	NO_MEMBER = "Member does not exist."
	NEW_OWNER = "Transferred ownership of faction to '{username}'."
	ALREADY_CLAIMED = "Your faction has already claimed this system or planet."
	CANNOT_CLAIM = "Cannot claim systems or planets while there are ships from other factions present."
	CLAIMED = "Claimed '{name}' for faction."
	CLAIMED_SYSTEM = "Claimed system for faction."
	CLAIMED_PLANET = "Claimed planet for faction."
	NO_FACTION = "Faction does not exist."
	NAME = "Name: {faction_name}"
	PASSWORD = "Password: {faction_password}"
	OWNER = "Owner: {faction_owner}"
	MEMBERS = "Members ({count}):"
	MEMBER = "\t{username}"
	ALPHANUM_ONLY = "Name can only contain letters and numbers."
	ALREADY_IN_FACTION = "You are already in a faction."
	CREATING_NEW = "Creating new faction..."
	JOINED = "Joined '{faction}'."
	KICKED = "Kicked operator '{username}'."
	HAS_MEMBERS = "Faction still has members; kick all members or transfer ownership first."
	LEFT = "Left '{faction}'."
	RENAMED_SYSTEM = "Renamed this system '{name}'."
	NO_CLAIM = "Your faction has not claimed this system or planet."
	RENAMED_PLANET = "Renamed this system '{name}'."
	UPDATED_PASSWORD = "Updated password."
	RELEASED_SYSTEM = "Released claim on this system."
	RELEASED_PLANET = "Released claim on this planet."
	RENAMED = "Renamed '{old_faction}' to '{faction}'."
	SELF_REPUTATION = "Cannot view or set reputation with yourself."
	REPUTATION_OF = "Reputation of '{name}': {reputation}"
	REPUTATION_WITH = "Reputation with '{name}': {reputation}"
	SET_REPUTATION = "Set reputation of '{name}' to {reputation}."
	PERSONAL_REPUTATION_OF = "Personal reputation of '{name}': {reputation}"
	PERSONAL_REPUTATION_WITH = "Personal reputation with '{name}': {reputation}"
	SET_PERSONAL_REPUTATION = "Set personal reputation of '{name}' to {reputation}."

class INFO:
	
	NOT_DISCOVERED = "No available data on system."
	SYSTEM = "System: {name}"
	CLAIMED_BY = "Claimed by '{faction}'."
	BRIGHTNESS = "Brightness: {brightness}"
	ASTEROIDS = "Asteroids: {asteroid_type} (density: {asteroid_density})"
	NORTH = "north"
	SOUTH = "south"
	EAST = "east"
	WEST = "west"
	NORTHEAST = "northeast"
	NORTHWEST = "northwest"
	SOUTHEAST = "southeast"
	SOUTHWEST = "southwest"
	LINKS = "Links:"
	LINK_NAMED = "\t[{index}] {name} (faction: {faction}) ({direction}) (drag: {link_drag})"
	LINK_CLAIMED = "\t[{index}] (faction: {faction}) ({direction}) (drag: {link_drag})"
	LINK = "\t[{index}] ({direction}) (drag: {link_drag})"
	PLANETS = "Planets:"
	PLANET_NAMED = "\t[{index}] {name} (faction: {faction}) ({planet_type})"
	PLANET_CLAIMED = "\t[{index}] (faction: {faction}) ({planet_type})"
	PLANET = "\t[{index}] ({planet_type})"
	STRUCTURES = "Structures:"
	STRUCTURE = "\t{id} {name}"
	
	CALLSIGN = "{id} {name}"
	OWNER_FACTION = "Owner: {username} ({faction})"
	OWNER = "Owner: {username}"
	OPERATORS = "Operators:"
	OPERATOR = "\t{username}"
	LANDED = "Landed on planet {planet_id}."
	DOCKED_TO = "Docked to '{id} {name}'."
	DOCKED = "Docked structures:"
	DOCK = "\t{id} {name}"
	OUTFIT_SPACE_TOTAL = "Outfit space: {space}"
	SHIELD_CHARGE = "Shield charge: {charge}"
	OUTFITS = "Outfits:"
	OUTFIT = "\t[{index}] {name} mark {mark} (setting {setting})"
	CARGOS = "Cargo:"
	CARGO_EXTRA = "\t[{index}] {name} ({extra}) x{count}"
	CARGO = "\t[{index}] {name} x{count}"
	
	GENERAL = "General:"
	MASS = "\tMass: {mass}"
	OUTFIT_SPACE = "\tOutfit space: {space}/{total}"
	HEAT = "\tHeat: {heat}/{max}"
	ENERGY = "\tEnergy: {energy}/{max}"
	STABILITY = "Stability:"
	COOLING_STATUS_STABLE = "\tCooling status: Stable"
	COOLING_STATUS_OVERHEAT_IN = "\tCooling status: Overheat in {remaining} seconds!"
	COOLING_STATUS_OVERHEAT = "\tCooling status: OVERHEATED"
	NET_HEAT = "\tNet heat generation: {heat_rate}/s"
	POWER_STATUS_STABLE = "\tPower status: Stable"
	POWER_STATUS_BROWNOUT_IN = "\tPower status: Brownout in {remaining} seconds!"
	POWER_STATUS_BROWNOUT = "\tPower status: BROWNOUT"
	NET_ENERGY = "\tNet energy consumption: {energy_rate}/s"
	REACTORS = "Fuel:"
	REACTOR = "\t[{index}] {name} mark {mark}: {remaining} seconds of fuel remaining"
	REACTOR_NOFUEL = "\t[{index}] {name} mark {mark}: OUT OF FUEL"
	SHIELDS_ONLINE = "Shields: Online"
	SHIELDS_REGENERATING = "Shields: Regenerating at {rate}/s ({shield}/{max})"
	SHIELDS_OFFLINE = "Shields: Offline ({shield}/{max})"
	SHIELDS_FAILED = "Shields: FAILED"
	WARP_READY = "Warp engines: Ready to engage"
	WARP_CHARGING = "Warp engines: Charging ({charge}%)"
	WARP_OFFLINE = "Warp engines: Offline"
	ANTIGRAVITY_OVERLOADED = "Antigravity engines: OVERLOADED"
	ANTIGRAVITY_ONLINE = "Antigravity engines: Online"
	CREW = "Colonists: {crew}"
	MINING_PROGRESS = "Mining progress: {progress}% ({interval} second interval)"

class SHIP:
	SELF_DOCK = "Cannot dock to yourself."
	ONLY_SHIPS = "Only ships can be docked to a structure."
	ALREADY_DOCKED = "Already docked to a structure."
	TARGET_ALREADY_DOCKED = "Target is already docked to a structure."
	DOCKED_TO = "Docked to structure '{id} {name}'."
	DOCKED = "Docked structure '{id} {name}'."
	NO_PLANET = "Planet does not exist."
	ALREADY_LANDED = "Already landed on a planet."
	LAND_WHILE_DOCKED = "Cannot land while docked."
	NO_ANTIGRAVITY = "Antigravity engines are needed to land on or launch off planets."
	LESS_ANTIGRAVITY = "Antigravity engines are not powerful enough to land or launch."
	LANDED = "Landed on planet {planet}."
	ONLY_SHIPS_LAUNCH = "Only ships can be launched from a planet."
	NOT_LANDED = "Not landed on a planet."
	LAUNCH_WHILE_DOCKED = "Cannot launch while docked."
	LAUNCHED = "Launched from planet."
	WARP_ON_PLANET = "Cannot engage warp engines in an atmosphere."
	WARP_WHILE_DOCKED = "Cannot engage warp engines while docked."
	NO_SYSTEM = "System does not exist."
	NO_CHARGE = "Warp engines are not fully charged."
	NO_STRUCTURE_X = "Unable to locate structure '{id}'."
	PERMISSION_DENIED_X = "Permission denied ({id} {name})."
	NO_CHARGE_X = "Warp engines on '{id} {name}' are not fully charged."
	ENGAGING = "Warp engines engaging."
	JUMP_COMPLETE = "Jump complete! Remaining charge: {charge}%."

class SOCIAL:
	FACTION = "Broadcast message to faction."
	NO_CHAT = "Operator has chat disabled."
	GLOBAL = "Broadcast message."
	SUBSPACE = "Sent message via subspace link."
	LOCAL = "Broadcast message to local system."
	NO_HAIL = "Unable to hail structure."
	HAIL = "Sent hail to '{id} {name}'."

class STRUCT:
	AIRLOCK = "Jettisoned operator '{username}' out the airlock."
	NO_DOCK = "Unable to locate docked structure."
	BEAMED = "Beamed onto '{id} {name}'."
	TRANSFERRED = "Transferred control core to '{id} {name}'."
	EJECT_ALL = "Ejected all docked structures."
	EJECT = "Ejected from docked structure."
	EJECTED = "Ejected '{id} {name}'."
	POWERED_DOWN = "Structure must be powered down to install or uninstall outfits."
	NOT_OUTFIT = "This is not an outfit."
	NO_OUTFIT_SPACE = "Insufficient outfit space."
	INSTALLED = "Installed a mark {mark} '{name}' from cargo."
	LOADED = "Loaded {count} '{type}' into '{id} {name}'."
	NO_OUTFIT = "Outfit does not exist."
	SET_GTZ = "Setting must be greater than zero."
	SET_LT = "Setting must be less than 1024."
	SET = "Updated setting of outfit '{name}' to {setting}."
	ENERGY_GTZ = "Energy must be greater than zero."
	NO_ENERGY = "Insufficient energy."
	SUPPLIED = "Supplied {count} energy to '{id} {name}'."
	UNINSTALLED = "Uninstalled outfit '{name}' into cargo."

