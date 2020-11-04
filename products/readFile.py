import ezdxf
import sys
import math
import os
import cv2
import datetime
import json

from .cloudconvert.api import Api

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from .hatchArea import save_svg_from_hatch_dxf
from .convert import save_svg_from_dxf
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient

# ============== Get Height ==============

def getHeight(shes) :
    minY, maxY = 999999, 0
    for sh in shes :
        if sh.dxftype() == 'LINE' :
            sy, ey = sh.dxf.start[1], sh.dxf.end[1]
            minY = min(minY, sy, ey)
            maxY = max(maxY, sy, ey)
        if sh.dxftype() == 'ARC' :
            sy = sh.dxf.center[1] + math.sin(math.radians(sh.dxf.start_angle)) * sh.dxf.radius
            ey = sh.dxf.center[1] + math.sin(math.radians(sh.dxf.end_angle)) * sh.dxf.radius
            minY = min(minY, sy, ey)
            maxY = max(maxY, sy, ey)
            if sh.dxf.start_angle <= 90 and sh.dxf.end_angle >= 90 :
                pt = sh.dxf.center[1] + sh.dxf.radius
                maxY = max(maxY, pt)
            if sh.dxf.start_angle <=270 and sh.dxf.end_angle >= 270 :
                pt = sh.dxf.center[1] - sh.dxf.radius
                minY = min(minY, pt)
        if sh.dxftype() == 'CIRCLE' :
            sy = sh.dxf.center[1] - sh.dxf.radius
            ey = sh.dxf.center[1] + sh.dxf.radius
            minY = min(minY, sy, ey)
            maxY = max(maxY, sy, ey)
        if sh.dxftype() == 'SPLINE' :
            fts = sh.fit_points
            for i in range(fts.__len__()) :
                v = fts.__getitem__(i)
                minY = min(minY, v[1])
                maxY = max(maxY, v[1])
        if sh.dxftype() == 'ELLIPSE' :
            tmp = sh.to_spline(False)
            fts = tmp.fit_points
            for i in range(fts.__len__()) :
                v = fts.__getitem__(i)
                minY = min(minY, v[1])
                maxY = max(maxY, v[1])
            del tmp
        if sh.dxftype() == 'LWPOLYLINE' :
            pt = [p[1] for p in sh.get_points("xy")]
            minY = min(minY, min(pt))
            maxY = max(maxY, max(pt))
        if sh.dxftype() == 'POLYLINE' :
            pt = [p.dxf.location[1] for p in sh.vertices]
            minY = min(minY, min(pt))
            maxY = max(maxY, max(pt))
        if sh.dxftype() == 'TEXT':
            minY = min(minY, sh.dxf.insert[1])
            maxY = max(maxY, sh.dxf.insert[1])
    
    return maxY - minY

# ============== Get Width ==============

def getWidth(shes) :
    minX, maxX = 999999, 0
    for sh in shes :
        if sh.dxftype() == 'LINE' :
            sx, ex = sh.dxf.start[0], sh.dxf.end[0]
            minX = min(minX, sx, ex)
            maxX = max(maxX, sx, ex)
        if sh.dxftype() == 'ARC' :
            sx = sh.dxf.center[0] + math.cos(math.radians(sh.dxf.start_angle)) * sh.dxf.radius
            ex = sh.dxf.center[0] + math.cos(math.radians(sh.dxf.end_angle)) * sh.dxf.radius
            minX = min(minX, sx, ex)
            maxX = max(maxX, sx, ex)
            if sh.dxf.start_angle <= 360 and sh.dxf.end_angle >= 0 :
                pt = sh.dxf.center[0] + sh.dxf.radius
                maxX = max(maxX, pt)
            if sh.dxf.start_angle <=180 and sh.dxf.end_angle >= 180 :
                pt = sh.dxf.center[0] - sh.dxf.radius
                minX = min(minX, pt)
        if sh.dxftype() == 'CIRCLE' :
            sx = sh.dxf.center[0] - sh.dxf.radius
            ex = sh.dxf.center[0] + sh.dxf.radius
            minX = min(minX, sx, ex)
            maxX = max(maxX, sx, ex)
        if sh.dxftype() == 'SPLINE' :
            fts = sh.fit_points
            for i in range(fts.__len__()) :
                v = fts.__getitem__(i)
                minX = min(minX, v[0])
                maxX = max(maxX, v[0])
        if sh.dxftype() == 'ELLIPSE' :
            tmp = sh.to_spline(False)
            fts = tmp.fit_points
            for i in range(fts.__len__()) :
                v = fts.__getitem__(i)
                minX = min(minX, v[0])
                maxX = max(maxX, v[0])
            del tmp
        if sh.dxftype() == 'LWPOLYLINE' :
            pt = [p[0] for p in sh.get_points("xy")]
            minX = min(minX, min(pt))
            maxX = max(maxX, max(pt))
        if sh.dxftype() == 'POLYLINE' :
            pt = [p.dxf.location[0] for p in sh.vertices]
            minX = min(minX, min(pt))
            maxX = max(maxX, max(pt))
        if sh.dxftype() == 'TEXT':
            minX = min(minX, sh.dxf.insert[0])
            maxX = max(maxX, sh.dxf.insert[0])
    
    return maxX - minX

# ============== Get Length ==============

def getTotalLength(shes) :
    total = 0
    for sh in shes :
        if sh.dxftype() == 'LINE' :
            total += math.sqrt(math.pow((sh.dxf.start[0] - sh.dxf.end[0]), 2) + math.pow((sh.dxf.start[1] - sh.dxf.end[1]), 2))
        if sh.dxftype() == 'ARC' :
            if sh.dxf.start_angle > sh.dxf.end_angle :
                rad = math.radians(sh.dxf.end_angle + 360 - sh.dxf.start_angle)
            else :
                rad = math.radians(sh.dxf.end_angle - sh.dxf.start_angle)
            total += rad * sh.dxf.radius
        if sh.dxftype() == 'CIRCLE' :
            total += 2 * math.pi * sh.dxf.radius
        if sh.dxftype() == 'SPLINE' :
            fts = sh.fit_points
            for i in range(fts.__len__()) :
                v1 = fts.__getitem__(i)
                v2 = fts.__getitem__(i + 1)
                ds = math.sqrt((v2[0] - v1[0]) ** 2 + (v2[1] - v1[1]) ** 2)
                total += ds
        if sh.dxftype() == 'ELLIPSE' :
            tmp = sh.to_spline(False)
            fts = tmp.fit_points
            for i in range(fts.__len__()) :
                v1 = fts.__getitem__(i)
                v2 = fts.__getitem__(i + 1)
                ds = math.sqrt((v2[0] - v1[0]) ** 2 + (v2[1] - v1[1]) ** 2)
                total += ds
            del tmp
        if sh.dxftype() == 'LWPOLYLINE' :
            pt = sh.get_points("xy")
            for i in range(len(pt) - 1) :
                ds = math.sqrt((pt[i][0] - pt[i + 1][0]) ** 2 + (pt[i][1] - pt[i + 1][1]) ** 2)
                total += ds
            if sh.closed is True :
                lstId = len(pt) - 1
                ds = math.sqrt((pt[lstId][0] - pt[0][0]) ** 2 + (pt[lstId][1] - pt[0][1]) ** 2)
                total += ds
        if sh.dxftype() == 'POLYLINE' :
            pt = sh.vertices
            for i in range(len(pt) - 1) :
                ds = math.sqrt((pt[i].dxf.location[0] - pt[i + 1].dxf.location[0]) ** 2 + (pt[i].dxf.location[1] - pt[i + 1].dxf.location[1]) ** 2)
                total += ds
            if sh.is_closed is True :
                lstId = len(pt) - 1
                ds = math.sqrt((pt[lstId].dxf.location[0] - pt[0].dxf.location[0]) ** 2 + (pt[lstId].dxf.location[1] - pt[0].dxf.location[1]) ** 2)
                total += ds

    return total

# ============== Set dxf file path ==============

def setDxfFilePath(filepath) :
    dxf = ezdxf.readfile(filepath)
    dxf.header['$INSUNITS'] = 1
    global msp
    msp = dxf.modelspace()

# ============== Get Hatch Area ===============

def getArea(hatchpngfspath, scale) :
    img = cv2.imread(hatchpngfspath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
    area = cv2.countNonZero(thresh)
    result = area * 2 / scale / scale

    return result

# ============== Downloading part ==============

def downloadSrc(url) :
    tmp = url
    res = tmp.split("/")
    filename = res[len(res) - 1]
    downloads_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    connection_string = "DefaultEndpointsProtocol=https;AccountName=mambamfgblob;AccountKey=chmmP6HA9Z8R1ZUyGg20tL/rCpjDt0qwxW8uYOxrm+KqCAQshGs8i8ItfzxyfE21TUtqR5ATIJjE3fNc+oneXQ==;EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(conn_str = connection_string)
    container_name = 'files'
    container_client = blob_service_client.get_container_client(container_name)

    fsdir = downloads_dir + "/" + container_name
    fspath = fsdir + "/" + filename

    if not(os.path.isdir(fsdir)):
        os.makedirs(fsdir, exist_ok = True)

    try :
        blob_client = container_client.get_blob_client(filename)
        with open(fspath, "wb") as my_blob :
            blob_data = blob_client.download_blob()
            blob_data.readinto(my_blob)
    except :
        print("Can't download files or doesn't exist file!")

    return fspath

# ============ Uploading Part =============

def uploadSrc(path, url) :
    tmp = url
    res = tmp.split("/")
    filename = res[len(res) - 1]

    if '.dxf' in filename :
        blob_name = filename.replace('.dxf', '.svg')
    elif '.DXF' in filename :
        blob_name = filename.replace('.DXF', '.svg')
    elif '.ai' in filename :
        blob_name = filename.replace('.ai', '.svg')
    elif '.AI' in filename :
        blob_name = filename.replace('.AI', '.svg')
    
    connection_string = "DefaultEndpointsProtocol=https;AccountName=mambamfgblob;AccountKey=chmmP6HA9Z8R1ZUyGg20tL/rCpjDt0qwxW8uYOxrm+KqCAQshGs8i8ItfzxyfE21TUtqR5ATIJjE3fNc+oneXQ==;EndpointSuffix=core.windows.net"
    container_name = "files"

    blob = BlobClient.from_connection_string(conn_str = connection_string, container_name = container_name, blob_name = blob_name)

    try :
        with open("./test3.svg", "rb") as data :
            blob.upload_blob(data)
    except :
        print("Can't upload file or already uploaded!")
    
    if '.dxf' in url :
        rlt = url.replace('.dxf', '.svg')
    elif '.DXF' in url :
        rlt = url.replace('.DXF', '.svg')
    elif '.ai' in url :
        rlt = url.replace('.ai', '.svg')
    elif '.AI' in url :
        rlt = url.replace('.AI', '.svg')

    return rlt

# ============ PDF to Dxf file convert part ==============

def pdf_to_dxf(path) :
    api = Api('M8NhM50249eK0vCcAYDjpj0L3eesFWVdw1N6SnQ3rj9j3OLaBMu6VWMhPRqjCiO1')
    resPath = path.replace(".pdf", ".dxf")

    process = api.convert({
        "inputformat": "pdf",
        "outputformat": "dxf",
        "input": "upload",
        "file": open(path, 'rb')
    })
    process.wait()
    process.download(resPath)

    return resPath

# ============ Initializing part ==============

def init(url) :
    tmpPath = downloadSrc(url)

    if ".ai" in tmpPath or ".AI" in tmpPath :
        if ".ai" in tmpPath :
            pdfpath = tmpPath.replace(".ai", ".pdf")
        elif ".AI" in tmpPath :
            pdfpath = tmpPath.replace(".AI", ".pdf")

        try :
            os.rename(tmpPath, pdfpath)
        except :
            print("Can't rename file because source file doesn't exist or same name file already exist!")
        fspath = pdf_to_dxf(pdfpath)
    else :
        fspath = tmpPath

    setDxfFilePath(fspath)

    svgfspath = save_svg_from_dxf(fspath)
    uploadedUrl = uploadSrc(svgfspath, url)
    print(svgfspath)
    print(uploadedUrl)

    W = getWidth(msp)
    H = getHeight(msp)

    print("Width = " + str(W) + "  |  Height = " + str(H))

    totalLength = getTotalLength(msp)

    print("Total Length = " + str(totalLength))

    svghatchpath, scl = save_svg_from_hatch_dxf(fspath)
    pnghatchpath = svghatchpath.replace('.svg', '.png')

    drawing = svg2rlg(svghatchpath)
    renderPM.drawToFile(drawing, pnghatchpath, fmt = "PNG")

    hatch_area = getArea(pnghatchpath, scl)
    print(hatch_area)

    os.remove(svghatchpath)
    os.remove(pnghatchpath)

    data_set = {
        "Uploaded_Url" : uploadedUrl,
        "Width" : W,
        "Height" : H,
        "Total_Length" : totalLength,
        "Hatch_area" : hatch_area,
        "Units" : "Inch"
    }
    json_data = json.dumps(data_set)

    return json_data
