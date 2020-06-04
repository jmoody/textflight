#!/bin/sh
if [ -z "$1" ]; then
	echo "Usage: $0 <locale dir>"
	exit
fi
for file in $1/*/LC_MESSAGES/textflight.po; do
	dir=$(dirname $file)
	msgfmt $file -o $dir/textflight.mo
done
