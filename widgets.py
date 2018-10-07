#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  7 12:09:54 2018

@author: david
"""

from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.popup import Popup
from kivy.vector import Vector
from kivy.graphics.transformation import Matrix

from config import Config
from math import radians

class AnnotationBox(Widget):
    sz = Config.ANNOTATION_BOX_SIZE
    box_size = (sz, sz)
    
class SaveFile(Popup):
    pass

class StretchScatter(Scatter):
    
    '''Original Scatter widget can only be scaled with fixed aspect ratio, we want to allow rectangles'''
    
    def get_scale_xy(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale_x = p1.distance(p2)
        
        p3 = Vector(*self.to_parent(0, 0))
        p4 = Vector(*self.to_parent(0, 1))
        scale_y = p3.distance(p4)
        
        box_size = AnnotationBox().box_size
        center = (p1[0]+scale_x*box_size[0]/2, p1[1]+scale_y*box_size[1]/2)
        
        return scale_x, scale_y, center     
    
    def on_touch_down(self, touch):
            x, y = touch.x, touch.y
            
            #if double touch always propagate to children
            if touch.is_double_tap:
                return super(Scatter, self).on_touch_down(touch)
    
            # if the touch isnt on the widget we do nothing
            if not self.do_collide_after_children:
                if not self.collide_point(x, y):
                    return False
    
            # let the child widgets handle the event if they want
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if super(Scatter, self).on_touch_down(touch):
                touch.pop()
                self._bring_to_front(touch)
                return True
            touch.pop()
    
            # if our child didn't do anything, and if we don't have any active
            # interaction control, then don't accept the touch.
            if not self.do_translation_x and \
                    not self.do_translation_y and \
                    not self.do_rotation and \
                    not self.do_scale:
                return False
    
            if self.do_collide_after_children:
                if not self.collide_point(x, y):
                    return False
    
            if 'multitouch_sim' in touch.profile:
                touch.multitouch_sim = True
            # grab the touch so we get all it later move events for sure
            self._bring_to_front(touch)
            touch.grab(self)
            self._touches.append(touch)
            self._last_touch_pos[touch] = touch.pos
    
            return True
    
    def transform_with_touch(self, touch):
        # just do a simple one finger drag
        changed = False
        if len(self._touches) == self.translation_touches:
            # _last_touch_pos has last pos in correct parent space,
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) \
                * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) \
                * self.do_translation_y
            dx = dx / self.translation_touches
            dy = dy / self.translation_touches
            self.apply_transform(Matrix().translate(dx, dy, 0))
            changed = True

        if len(self._touches) == 1:
            return changed

        # we have more than one touch... list of last known pos
        points = [Vector(self._last_touch_pos[t]) for t in self._touches
                  if t is not touch]
        # add current touch last
        points.append(Vector(touch.pos))

        # we only want to transform if the touch is part of the two touches
        # farthest apart! So first we find anchor, the point to transform
        # around as another touch farthest away from current touch's pos
        anchor = max(points[:-1], key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if farthest is not points[-1]:
            return changed

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*touch.ppos) - anchor
        new_line = Vector(*touch.pos) - anchor
        if not old_line.length():   # div by zero
            return changed

        angle = radians(new_line.angle(old_line)) * self.do_rotation
        self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)

        if self.do_scale:
            scale_x = new_line.x/ old_line.x
            scale_y = new_line.y/ old_line.y
            
            new_scale_x = scale_x * self.scale
            if new_scale_x < self.scale_min:
                scale_x = self.scale_min / self.scale
            elif new_scale_x > self.scale_max:
                scale_x = self.scale_max / self.scale
            
            new_scale_y = scale_y * self.scale
            if new_scale_y < self.scale_min:
                scale_y = self.scale_min / self.scale
            elif new_scale_y > self.scale_max:
                scale_y = self.scale_max / self.scale
            
            self.apply_transform(Matrix().scale(scale_x, scale_y, 1),
                                 anchor=anchor)
            changed = True
            
        return changed