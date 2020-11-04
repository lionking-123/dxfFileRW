import os
import sys
from math import sqrt, sin, cos, pi, fabs, radians

import ezdxf
import svgwrite

LAYER = 'svgframe'
SVG_MAXSIZE = 512
SCALE = 1.0

#============= Initializing part ==============

def get_dxf_dwg_from_file(dxffilepath) :
    return ezdxf.readfile(dxffilepath)

def get_clear_svg(minx = -50, miny = -50, width = 100, height = 100) :
    svg = svgwrite.Drawing(size = (SVG_MAXSIZE, SVG_MAXSIZE), viewBox = "%s %s %s %s"%(minx, miny, width, height))
    return svg

def get_empty_svg(alerttext = '! nothing to display !') :
    svg = svgwrite.Drawing(size = (SVG_MAXSIZE, SVG_MAXSIZE), viewBox = "0 0 %s %s"%(SVG_MAXSIZE, SVG_MAXSIZE))
    svg.add(svgwrite.Drawing().text(alerttext, insert = [50, 50], font_size = 20))
    return svg
    
#========== Drawing Part ==============

def trans_line(dxf_entity) :
    line_start = dxf_entity.dxf.start[:2]
    line_end = dxf_entity.dxf.end[:2]
    svg_entity = svgwrite.Drawing().line(start = line_start, end = line_end, stroke = "black", stroke_width = 1.0/SCALE )
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_circle(dxf_entity) :
    circle_center = dxf_entity.dxf.center[:2]
    circle_radius = dxf_entity.dxf.radius
    svg_entity = svgwrite.Drawing().circle(center = circle_center, r = circle_radius, stroke = "black", fill = "none", stroke_width = 1.0/SCALE )
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_arc(dxf_entity, dwg) :
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
            fill = "none", 
            stroke = "black",
            stroke_width = 1.0 / SCALE
        )

    svg_entity.scale(SCALE,-SCALE)
    return svg_entity

def trans_spline(dxf_entity, dwg) :
    ctrlPoints = dxf_entity.control_points
    ctrlCnt = dxf_entity.control_point_count

    strPath = ""
    for i in range(ctrlCnt) :
        if i == 0 :
            strPath += "M " + str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + " C "
        else :
            strPath += str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + ", "
        
    svg_entity = dwg.path(d = strPath, fill = "none", stroke = "black", stroke_width = 1.0 / SCALE)

    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_ellipse(dxf_entity, dwg) :
    tmp = dxf_entity.to_spline(False)
    ctrlPoints = tmp.control_points
    ctrlCnt = tmp.control_point_count

    strPath = ""
    for i in range(ctrlCnt) :
        if i == 0 :
            strPath += "M " + str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + " C "
        else :
            strPath += str(ctrlPoints[i][0]) + " " + str(ctrlPoints[i][1]) + ", "
        
    svg_entity = dwg.path(d = strPath, fill = "none", stroke = "black", stroke_width = 1.0 / SCALE)

    svg_entity.scale(SCALE, -SCALE)
    del tmp
    return svg_entity

def trans_text(dxf_entity) :
    text_text = dxf_entity.dxf.text
    text_insert = dxf_entity.dxf.insert[:2]
    text_height = dxf_entity.dxf.height * 1.4 # hotfix - 1.4 to fit svg and dvg
    svg_entity = svgwrite.Drawing().text(text_text, insert = [0, 0], font_size = text_height * SCALE)
    svg_entity.translate(text_insert[0]*(SCALE), -text_insert[1]*(SCALE))
    return svg_entity

def trans_polyline(dxf_entity) :
    points = [(vert.dxf.location[0], vert.dxf.location[1]) for vert in dxf_entity.vertices]
    
    svg_entity = svgwrite.Drawing().polyline(points = points, stroke = 'black', fill = 'none', stroke_width = 1.0/SCALE)
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

def trans_lwpolyline(dxf_entity) :
    points = [(pt[0], pt[1]) for pt in dxf_entity.get_points("xy")]
    
    svg_entity = svgwrite.Drawing().polyline(points = points, stroke = 'black', fill = 'none', stroke_width = 1.0/SCALE)
    svg_entity.scale(SCALE, -SCALE)
    return svg_entity

#============ Dxf Entity Filtering part ===============

def entity_filter(dxffilepath, frame_name = None) :
    dxf = get_dxf_dwg_from_file(dxffilepath)
    
    frame_rect_entity = None
    name_text_entity = None
    
    if frame_name:
        for e in dxf.modelspace():
            if e.dxftype() == 'TEXT' and e.dxf.layer == LAYER:
                if e.dxf.text == frame_name:
                    name_text_entity = e
    if name_text_entity:
        text_point = name_text_entity.dxf.insert[:2]
        text_height = name_text_entity.dxf.height
        for e in dxf.modelspace():
            if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer == LAYER:
                points = list(e.get_rstrip_points())
                for p in points:
                    dist = sqrt((p[0] - text_point[0])**2+(p[1] - text_point[1])**2)
                    if dist < 1.0 * text_height:
                        frame_rect_entity = e
    
    if frame_rect_entity and name_text_entity:
        frame_points = list(frame_rect_entity.get_rstrip_points())
        entitys_in_frame = []
        xmin = min([i[0] for i in frame_points])
        xmax = max([i[0] for i in frame_points])
        ymin = min([i[1] for i in frame_points])
        ymax = max([i[1] for i in frame_points])
        for e in dxf.modelspace():
            point = None 
            if e.dxftype() == 'LINE': point = e.dxf.start[:2]
            if e.dxftype() == 'CIRCLE': point = e.dxf.center[:2]
            if e.dxftype() == 'TEXT': point = e.dxf.insert[:2]
            if e.dxftype() == 'ARC':
                center = e.dxf.center[:2]
                radius = e.dxf.radius
                start_angle = radians(e.dxf.start_angle)
                delta_x = radius * cos(start_angle)
                delta_y = radius * sin(start_angle)
                point = (center[0] + delta_x, center[1] + delta_y)
            if point:
                if (xmin <= point[0] <= xmax) and (ymin <= point[1] <= ymax):
                    if not e.dxf.layer == LAYER:
                        entitys_in_frame.append(e)
        return entitys_in_frame, [xmin, xmax, ymin, ymax]
    elif frame_name:
        return [], [300, 600, 300, 600]
    elif not frame_name:
        entitys = []
        xmin = 99999
        xmax = 0
        ymin = 99999
        ymax = 0
        for e in dxf.modelspace():
            if not e.dxf.layer == LAYER :
                entitys.append(e)
                if e.dxftype() == 'LINE' : 
                    xmin = min(xmin, e.dxf.start[0], e.dxf.end[0])
                    xmax = max(xmax, e.dxf.start[0], e.dxf.end[0])
                    ymin = min(ymin, e.dxf.start[1], e.dxf.end[1])
                    ymax = max(ymax,  e.dxf.start[1], e.dxf.end[1])
                if e.dxftype() == 'CIRCLE' :
                    xmin = min(xmin, e.dxf.center[0] - e.dxf.radius)
                    xmax = max(xmax, e.dxf.center[0] + e.dxf.radius)
                    ymin = min(ymin, e.dxf.center[1] - e.dxf.radius)
                    ymax = max(ymax,  e.dxf.center[1] + e.dxf.radius)              
                if e.dxftype() == 'TEXT':
                    xmin = min(xmin, e.dxf.insert[0])
                    xmax = max(xmax, e.dxf.insert[0])
                    ymin = min(ymin, e.dxf.insert[1])
                    ymax = max(ymax, e.dxf.insert[1])
                if e.dxftype() == 'ARC' :
                    sx = e.dxf.center[0] + cos(radians(e.dxf.start_angle)) * e.dxf.radius
                    ex = e.dxf.center[0] + cos(radians(e.dxf.end_angle)) * e.dxf.radius
                    sy = e.dxf.center[1] + sin(radians(e.dxf.start_angle)) * e.dxf.radius
                    ey = e.dxf.center[1] + sin(radians(e.dxf.end_angle)) * e.dxf.radius
                    
                    xmin = min(xmin, sx, ex)
                    xmax = max(xmax, sx, ex)
                    if e.dxf.start_angle <= 360 and e.dxf.end_angle >= 0 :
                        pt = e.dxf.center[0] + e.dxf.radius
                        xmax = max(xmax, pt)
                    if e.dxf.start_angle <=180 and e.dxf.end_angle >= 180 :
                        pt = e.dxf.center[0] - e.dxf.radius
                        xmin = min(xmin, pt)

                    ymin = min(ymin, sy, ey)
                    ymax = max(ymax, sy, ey)
                    if e.dxf.start_angle <= 90 and e.dxf.end_angle >= 90 :
                        pt = e.dxf.center[1] + e.dxf.radius
                        ymax = max(ymax, pt)
                    if e.dxf.start_angle <=270 and e.dxf.end_angle >= 270 :
                        pt = e.dxf.center[1] - e.dxf.radius
                        ymin = min(ymin, pt)
                    
                if e.dxftype() == 'POLYLINE':
                    x = [p.dxf.location[0] for p in e.vertices]
                    y = [p.dxf.location[1] for p in e.vertices]
                    xmin = min(xmin, min(x))
                    xmax = max(xmax, max(x))
                    ymin = min(ymin, min(y))
                    ymax = max(ymax, max(y))
                if e.dxftype() == 'LWPOLYLINE':
                    x = [p[0] for p in e.get_points("xy")]
                    y = [p[1] for p in e.get_points("xy")]
                    xmin = min(xmin, min(x))
                    xmax = max(xmax, max(x))
                    ymin = min(ymin, min(y))
                    ymax = max(ymax, max(y))
                if e.dxftype() == 'SPLINE' :
                    fts = e.fit_points
                    for i in range(fts.__len__()) :
                        v = fts.__getitem__(i)
                        xmin = min(xmin, v[0])
                        xmax = max(xmax, v[0])
                        ymin = min(ymin, v[1])
                        ymax = max(ymax, v[1])
                if e.dxftype() == 'ELLIPSE' :
                    tmp = e.to_spline(False)
                    fts = tmp.fit_points
                    for i in range(fts.__len__()) :
                        v = fts.__getitem__(i)
                        xmin = min(xmin, v[0])
                        xmax = max(xmax, v[0])
                        ymin = min(ymin, v[1])
                        ymax = max(ymax, v[1])
                    del tmp
                
        xmargin = 0.05 * fabs(xmax - xmin)
        ymargin = 0.05 * fabs(ymax - ymin)
        return entitys, [xmin - xmargin, xmax + xmargin, ymin - ymargin, ymax + ymargin]

#============ Extract Svg part =============

def get_svg_form_dxf(dxffilepath, frame_name = None) :
    global SCALE
    
    entites_filter = entity_filter(dxffilepath, frame_name)
    entites = entites_filter[0]
    frame_coord = entites_filter[1]
    
    if not entites:
        return get_empty_svg()
    
    minx = frame_coord[0]
    miny = -frame_coord[3]
    width = abs(frame_coord[0] - frame_coord[1])
    height = abs(frame_coord[2] - frame_coord[3])
    SCALE = 1.0 * SVG_MAXSIZE / max(width, height)
    
    svg = get_clear_svg(minx * SCALE, miny * SCALE, width * SCALE, height * SCALE)
    for e in entites:
        if e.dxftype() == 'LINE': svg.add(trans_line(e))
        if e.dxftype() == 'POLYLINE': svg.add(trans_polyline(e))
        if e.dxftype() == 'LWPOLYLINE': svg.add(trans_lwpolyline(e))
        if e.dxftype() == 'CIRCLE': svg.add(trans_circle(e))
        if e.dxftype() == 'TEXT': svg.add(trans_text(e))
        if e.dxftype() == 'ARC': svg.add(trans_arc(e, svg))
        if e.dxftype() == 'SPLINE': svg.add(trans_spline(e, svg))
        if e.dxftype() == 'ELLIPSE': svg.add(trans_ellipse(e, svg))
    return svg

#============ Saving Svg file ==============

def save_svg_from_dxf(dxffilepath, svgfilepath = None, frame_name = None, size = 512) :
    global SVG_MAXSIZE
    _oldsize = SVG_MAXSIZE
    SVG_MAXSIZE = size
    
    if frame_name :
        print('>>making %s svgframe for %s ...'%(frame_name, os.path.basename(dxffilepath)))
    else :
        print('making svg for %s ...'%(os.path.basename(dxffilepath)))
        pass
    
    svg = get_svg_form_dxf(dxffilepath, frame_name)
    
    if '.dxf' in dxffilepath :
        svgfilepath = dxffilepath.replace('.dxf', '.svg')
    elif '.DXF' in dxffilepath :
        svgfilepath = dxffilepath.replace('.DXF', '.svg')
    
    svg.saveas(svgfilepath)
    
    SVG_MAXSIZE = _oldsize

    return svgfilepath
