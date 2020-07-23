## SECTION 08: COMBAT

The most important aspect of combat is defence. To prevent structures from being destroyed or captured, direct power to shield matrices. Shield energy will persist even if the matrices are unpowered, and prevent the destruction of the structure so long as it is present. The `status` and `scan` commands can be used to view the status of a structure's shields.

Structures will automatically target any other structures they view as having negative reputation. Personal reputation takes precedence over faction reputation in this process. Structures will also target other structures who target them, or when directed to via the `target` command.

Three types of weapons are currently available. Electron beams will drain the shields of a target, while EMP and plasma damage will drain their energy and increase their heat, respectively. The ultimate goal of combat is to reduce the target's shields to zero, or cause the target to overheat and experience a brownout simultaneously, disabling it.

Once a structure's shields have been reduced to zero, their structure can be destroyed using the `destroy` command. Note that using the `target` command will apply a reputation penalty of -10, while using the destroy command applies an additional penalty of -100. Structures can also be captured, for a penalty of -100 reputation. Capturing a structure will see your structure's crew battling the crew of the enemy. If all your crew are killed, the capture will fail. Some outfits improve your crew's ability to attack or defend themselves. If capture is successful, the ownership of the structure is transferred to your operator, and the `airlock` command can be used to remove any enemy operators from the structure.
