# Tools

Assorted tools needed when dealing with e.g. Onshape DXF exports.

Example usage:

```
> mkdir output
> for f in `ls *.dxf`; do python convert_onshape_dxf.py -i $f -o output/$f; done;
```