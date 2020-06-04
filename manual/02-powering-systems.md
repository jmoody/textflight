## SECTION 02: POWERING SYSTEMS

Structure outfits are operated using the `set` command, which controls how much system power is routed into them. The default operation setting is 16, however a lower setting can be used to conserve power and reduce heat. Outfits can also be overcharged, but this will cause exponential increases in the generated heat. Use the `scan` command to list outfits and cargo installed on a structure, and pass the outfit ID obtained from the outfit manifest to the `set` command in order to modify it's operation setting.

To bring a structure online, start by using the `status` command to check whether the structure is overheating or experiencing a brownout. If the structure is overheating, start by powering on coolant pumps. If the structure is experiencing a brownout, power the generators first. If both conditions exist simultaneously, the structure has been deadlocked, and will require power to be transferred to it by a donor using the `supply` command.

Once the first outfits have been brought online, run the `status` command again to view energy and heat consumption rates. If energy consumption is positive, direct more power to the generators. If heat production is positive, direct more power to the coolant pumps. As more outfits are brought online, continue to monitor the structure's status.

Solar arrays provide a steady supply of free energy, however, their efficiency depends on the brightness of the star the structure is orbiting. As a result, using solar arrays when jumping into uncharted systems can cause immediate system failure if the star is not bright enough to power all outfits.

Two types of reactors are available; fusion reactors, and fission reactors. Both act as a reliable power supply, but consume fuel, loaded directly from the structure's cargo hold. As a result, reactors will likely need to be shut down when not in use in order to conserve fuel. Fission reactors are far more compact than their fusion counterparts, but require uranium fuel cells which are extremely difficult to produce. Hydrogen fuel cells, by comparison, are much easier to obtain.
