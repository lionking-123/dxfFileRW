import os
import sys
from math import sqrt, sin, cos, pi, fabs, radians
from .convert import entity_filter

import ezdxf
import svgwrite

LAYER = 'svgframe'
SVG_MAXSIZE = 512
SCALE = 1.0

#============= Initializing part ==============

def get_dxf_dwg_from_file(dxffilepath) :
    return ezdxf.readfile(dxffilepath)

def get_clear_hatch_svg(minx = -50, miny = -50, width = 100, height = 100) :
    svg = svgwrite.Drawing(size = (SVG_MAXSIZE, SVG_MAXSIZE), viewBox = "%s %s %s %s"%(minx, miny, width, height))
    svg.add(svg.rect(insert = (minx, miny), size = ('100%', '100%'), rx = None, ry = None, fill = 'rgb(0, 0, 0)'))
    return svg

def get_empty_hatch_svg(alerttext = '! nothing to display !') :
    svg = svgwrite.Drawing(size = (SVG_MAXSIZE, SVG_MAXSIZE), viewBox = "0 0 %s %s"%(SVG_MAXSIZE, SVG_MAXSIZE))
    svg.add(svgwrite.Drawing().text(alerttext, insert = [50, 50], font_size = 20))
    return svg
    
#========== Drawing Part ==============

def trans_hatch_line(dxf_entity) :
    line_start = dxf_entity.dxf.start[:2]
    line_end = dxf_entity.dxf.end[:2]
    svg_entity = svgwrite.Drawing().line(start = line_start, end = line_end, stroke = "green", stroke_width = 1.0/SCALE )
    svg_entity.scale(SCALE,-SCALE)
    return svg_entity

def trans_hatch_circle(dxf_entity) :
    circle_center = dxf_entity.dxf.center[:2]
    circle_radius = dxf_entity.dxf.radius
    svg_entity = svgwrite.Drawing().circle(center = circle_center, r = circle_radius, stroke = "green", fill = "blue", stroke_width = 1.0/SCALE )
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_hatch_arc(dxf_entity, dwg) :
    start_x = dxf_entity.dxf.center[0]
    start_y = dxf_entity.dxf.center[1]
    radius = dxf_entity.dxf.radius
    
    degree0 = dxf_entity.dxf.end_angle
    degree1 = dxf_entity.dxf.start_angle
    radians0 = radians(degree0)
    radians1 = radians(degree1)
    dx0 = radius*(sin(radians0))
    dy0 = radius*(cos(radians0))
    dx1 = radius*(sin(radians1))
    dy1 = radius*(cos(radians1))

    m0 = dy0 + start_x
    n0 = dx0 + start_y
    m1 = -dy0 + dy1
    n1 = -dx0 + dx1
    

    svg_entity = dwg.path(d = "M {0},{1} a {2},{2} 0 0,0 {3},{4}".format(m0, n0, radius, m1, n1),
            fill = "blue", 
            stroke = "green",
            stroke_width = 1.0 / SCALE
        )

    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_hatch_spline(dxf_entity, dwg) :
    ctrlPoints = dxf_entity.control_points
    ctrlCnt = dxf_entity.control_point_count

    strPath = ""
    for i in range(ctrlCnt) :
        if i == 0 :
            strPath += "M " + str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + " C "
        else :
            strPath += str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + ", "
        
    svg_entity = dwg.path(d = strPath, fill = "blue", stroke = "green", stroke_width = 1.0 / SCALE)

    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_hatch_ellipse(dxf_entity, dwg) :
    tmp = dxf_entity.to_spline(False)
    ctrlPoints = tmp.control_points
    ctrlCnt = tmp.control_point_count

    strPath = ""
    for i in range(ctrlCnt) :
        if i == 0 :
            strPath += "M " + str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + " C "
        else :
            strPath += str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + ", "
        
    svg_entity = dwg.path(d = strPath, fill = "blue", stroke = "green", stroke_width = 1.0 / SCALE)

    svg_entity.scale(SCALE, -SCALE)
    del tmp
    return svg_entity

def trans_hatch_text(dxf_entity) :
    text_text = dxf_entity.dxf.text
    text_insert = dxf_entity.dxf.insert[:2]
    text_height = dxf_entity.dxf.height * 1.4 # hotfix - 1.4 to fit svg and dvg
    svg_entity = svgwrite.Drawing().text(text_text, insert = [0, 0], font_size = text_height * SCALE)
    svg_entity.translate(text_insert[0]*(SCALE), -text_insert[1]*(SCALE))
    return svg_entity

def trans_hatch_polyline(dxf_entity) :
    points = [(vert.dxf.location[0], vert.dxf.location[1]) for vert in dxf_entity.vertices]
    
    svg_entity = svgwrite.Drawing().polyline(points = points, stroke = 'green', fill = 'blue', stroke_width = 1.0/SCALE)
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_hatch_lwpolyline(dxf_entity) :
    points = [(pt[0], pt[1]) for pt in dxf_entity.get_points("xy")]
    
    svg_entity = svgwrite.Drawing().polyline(points = points, stroke = 'green', fill = 'blue', stroke_width = 1.0/SCALE)
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

#============ Extract Svg part =============

def get_svg_from_hatch_dxf(dxffilepath, frame_name = None) :
    global SCALE
    
    entites_filter = entity_filter(dxffilepath, frame_name)
    entites = entites_filter[0]
    frame_coord = entites_filter[1]
    
    if not entites:
        return get_empty_hatch_svg()
    
    minx = frame_coord[0]
    miny = -frame_coord[3]
    width = abs(frame_coord[0] - frame_coord[1])
    height = abs(frame_coord[2] - frame_coord[3])
    SCALE = 1.0 * SVG_MAXSIZE / max(width, height)
    
    svg = get_clear_hatch_svg(minx * SCALE, miny * SCALE, width * SCALE, height * SCALE)
    for e in entites:
        if e.dxftype() == 'LINE': svg.add(trans_hatch_line(e))
        if e.dxftype() == 'POLYLINE': svg.add(trans_hatch_polyline(e))
        if e.dxftype() == 'LWPOLYLINE': svg.add(trans_hatch_lwpolyline(e))
        if e.dxftype() == 'CIRCLE': svg.add(trans_hatch_circle(e))
        if e.dxftype() == 'TEXT': svg.add(trans_hatch_text(e))
        if e.dxftype() == 'ARC': svg.add(trans_hatch_arc(e, svg))
        if e.dxftype() == 'SPLINE': svg.add(trans_hatch_spline(e, svg))
        if e.dxftype() == 'ELLIPSE': svg.add(trans_hatch_ellipse(e, svg))
    return svg

#============ Saving Svg file ==============

def save_svg_from_hatch_dxf(dxffilepath, svgfilepath = None, frame_name = None, size = 512) :
    global SVG_MAXSIZE
    _oldsize = SVG_MAXSIZE
    SVG_MAXSIZE = size
    
    if frame_name :
        print('>>making %s svgframe for %s ...'%(frame_name, os.path.basename(dxffilepath)))
    else :
        print('making svg for %s ...'%(os.path.basename(dxffilepath)))
        pass
    
    svg = get_svg_from_hatch_dxf(dxffilepath, frame_name)
        
    if '.dxf' in dxffilepath :
        svgfilepath = dxffilepath.replace('.dxf', '_hatch.svg')
    elif '.DXF' in dxffilepath :
        svgfilepath = dxffilepath.replace('.DXF', '_hatch.svg')
    
    svg.saveas(svgfilepath)
    
    SVG_MAXSIZE = _oldsize

    return svgfilepath, SCALE
