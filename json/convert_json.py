#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  7 17:09:16 2018

@author: david
"""
import numpy as np
from matplotlib.path import Path

def convertBB(BB, img_shape):
    '''
    Converts bounding box element from annotation json to properly scaled tuple (px,py,width,height).  
    The point (px,py) corresponds to the top left point of the bounding box.
    '''
    
    #get ratios
    ratio_x, ratio_y = img_shape[1]/BB['img_size'][0], img_shape[0]/BB['img_size'][1]
    scale_x, scale_y, box_size = BB['scale_x'], BB['scale_y'], BB['box_size']
    
    #get top-left pt of box
    px = ratio_x*(BB['center'][0]-box_size[0]*scale_x/2)
    py = img_shape[0]-ratio_y*(BB['center'][1]+box_size[0]*scale_y/2)
    
    #scale width/height of box
    width, height = ratio_x*box_size[0]*scale_x, ratio_y*box_size[1]*scale_y
    
    return (px,py,width,height)

def convertPaint(blob, img_shape):
    '''
    Converts painted blob from annotation json to corresponding 2D mask.
    '''
        
    #scale selected points to image size
    ratio_x, ratio_y = img_shape[1]/blob['img_size'][0], img_shape[0]/blob['img_size'][1]
    pts = [(pt[0]*ratio_x, img_shape[0] - pt[1]*ratio_y) for pt in blob['points']]
    
    #convert points to mask
    x, y = np.meshgrid(np.arange(img_shape[1]), np.arange(img_shape[0]))
    x, y = x.flatten(), y.flatten()
        
    path = Path(pts)
    mask = path.contains_points(np.vstack((x,y)).T)
    
    return mask.reshape(img_shape[:2])