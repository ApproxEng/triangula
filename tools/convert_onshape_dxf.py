__author__ = 'Tom Oinn'

import sys
import getopt
# Get ezdxf with 'pip install ezdxf', tested with Python2.7
import ezdxf


def mirror_coord(c):
    """
    If Z coordinate of c is less than zero, return mirrored around Y axis

    :param c:
        a coordinate (x,y,z)

    :returns:
        A flattened (Z set to 0) and optionally mirrored, copy of the input
    """
    (x, y, z) = c
    if z < 0:
        return (-x, y, 0)
    return (x, y, 0)


def mirror(a):
    """
    Return angle mirrored around 180 degrees
    """
    a = 180 - a
    if a < 0:
        a = a + 360
    return a


def main(inputfile, outputfile):
    """
    Mirror all CIRCLE and ARC entities if their centre coordinates are negative in Z axis

    :param inputfile:
        Name of a DXF file to read
    :param outputfile:
        Name of a DXF file to write
    """
    dwg = ezdxf.readfile(inputfile)
    for e in dwg.entities:
        if e.dxftype() == 'CIRCLE':
            e.dxf.center = mirror_coord(e.dxf.center)
        elif e.dxftype() == 'ARC':
            (x, y, z) = e.dxf.center
            if z < 0:
                start_angle = e.dxf.start_angle
                end_angle = e.dxf.end_angle
                e.dxf.start_angle = mirror(end_angle)
                e.dxf.end_angle = mirror(start_angle)
            e.dxf.center = mirror_coord(e.dxf.center)
    dwg.saveas(outputfile)


USAGE_MESSAGE = 'convert_onshape_dxf.py [-i|--ifile] <input_file> [-o|--ofile] <outputfile>'

if __name__ == '__main__':
    input_file = None
    output_file = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:', ['ifile=', 'ofile='])
    except getopt.GetoptError:
        print USAGE_MESSAGE
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg
    if input_file is None or output_file is None:
        print(USAGE_MESSAGE)
        sys.exit(2)
    main(input_file, output_file)
