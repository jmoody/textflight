#!/bin/sh

SRCDIR="manual"
BUILDDIR="./"
MANUAL_MD="$BUILDDIR/textflight-manual.md"
MANUAL_HTML="$BUILDDIR/textflight-manual.html"
MANUAL_PDF="$BUILDDIR/textflight-manual.pdf"

# Generate section 9
./src/generate_section_9.py > $SRCDIR/09-data-files.md

# Generate Markdown manual
mkdir -p $BUILDDIR
rm -f $MANUAL_MD
for f in $SRCDIR/*.md; do
	cat $f >> $MANUAL_MD
	printf "\n\n\n" >> $MANUAL_MD
done

# Generate HTML and PDF manuals
# TODO: Fancy formatting and stuff
pandoc -s $MANUAL_MD -o $MANUAL_HTML
pandoc -s $MANUAL_MD -o $MANUAL_PDF
