# Tools

Assorted tools needed when dealing with e.g. Onshape DXF exports.

Example usage to batch fix all .dxf files in a directory:

```
> cd directory_with_dxf_files
> pip install ezdxf
> mkdir output
> for f in `ls *.dxf`; do python convert_onshape_dxf.py -i $f -o output/$f; done;
```
