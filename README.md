# Textflight

A command line space exploration MMO.

## Playing

You can use any SSL-secured socket client to connect to the server. Here is an example using the program `socat`:

```
socat - openssl:leagueh.xyz:10000
```

## Translation

Textflight supports localization via GNU gettext. Programs like `xgettext` will not work on the source code; instead, run `./src/generate_pot.py` to automatically generate a POT file.

## Running

Note: Although you can run your own server, remember that this is an MMO; the more people are playing on a server, the more fun it is, so running a public server is strongly discouraged so as not to fragment the community. Thanks for your understanding!

To start the server, simply execute `./src/main.py`, ensuring all the dependencies listed below have been installed:

- Python 3
- sqlite3
- bcrypt

By default, the server runs without SSL on port `10000`. You can connect using socket clients such as `socat`.

The following tables can be safely modified. Never modify any other tables while the server is running, as this could cause undefined behaviour or data loss.

- `factions`
- `faction_systems`
- `faction_planets`
- `faction_reputation`
- `user_reputation`
- `personal_reputation`

When deleting rows from the `users` table, ensure that all rows referencing that user in other tables have also been deleted. When deleting rows from the `structures` table, ensure that all rows referencing that structure in other tables have also been deleted, with the exception of `users.structure_id`, which should be set to `NULL` instead.

