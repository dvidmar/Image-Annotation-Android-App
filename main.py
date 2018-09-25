#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 11:14:45 2018

@author: david
"""

from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Rectangle
from kivy.uix.label import Label
from kivy.graphics import Line, Color
from kivy.vector import Vector
from kivy.graphics.transformation import Matrix
from math import radians
from os import listdir

class StretchScatter(Scatter):
    
    '''Original Scatter widget can only be scaled with fixed aspect ratio, we want to allow rectangles'''
    
    def get_scale_xy(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale_x = p1.distance(p2)
        
        p3 = Vector(*self.to_parent(0, 0))
        p4 = Vector(*self.to_parent(0, 1))
        scale_y = p3.distance(p4)
        
        return scale_x, scale_y
    
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
    

class AnnotationBox(Widget):
    box_size = (300, 300)

class Background(Widget):
    pass
            
class RootWidget(Widget):
    def __init__(self):
        super(RootWidget, self).__init__()
        self.filepop = SaveFile()
        self.filepop.open()
        
        self.img_num = 0
        self.boxes = []
        self.box_size = AnnotationBox().box_size
        
        self.file_selected = False
        self.paint = False
        
        self.stroke_num = 0
        self.pix_dict = {}
        
    def on_touch_down(self, touch):
        if self.file_selected and touch.is_double_tap and not self.paint:
            #add bounding box on touch
            self.add_bounding_box(touch)
            return True
        else:
            if self.paint:
                #draw points as a line
                with self.canvas:
                    Color(.1, .1, 1, .9)
                    touch.ud['line'] = Line(points=(touch.x, touch.y), width = 5.0)
                
            return super(RootWidget, self).on_touch_down(touch) #propagate touch down chain
        
    def on_touch_up(self, touch):
        #change to new object on release
        if self.paint:
            self.stroke_num += 1
                
        return super(RootWidget, self).on_touch_down(touch) #propagate touch down chain
    
    def on_touch_move(self, touch):
        if self.paint:
            #get highlighted points
            touch.ud['line'].points += [touch.x, touch.y]
            
            #add to pixel dictionary of highlighted points
            if 'Object %i: '%self.stroke_num in self.pix_dict:
                self.pix_dict['Object %i: '%self.stroke_num].append([int(touch.x), int(touch.y)])
            else:
                self.pix_dict['Object %i: '%self.stroke_num] = [int(touch.x), int(touch.y)]
                
    def add_progress_bar(self):
        with self.canvas:            
            Color(0,1,0,1)
            prog_ratio = float(self.img_num)/float(len(self.all_imgs))
            Line(points = [self.size[0]*.25, self.size[1]*.925, 
                           self.size[0]*.25+prog_ratio*self.size[0]*.5, 
                           self.size[1]*.925], width = self.size[1]*.015, cap = 'none')
            
            Color(0,0,0,1)
            Line(rectangle = (self.size[0]*.25, self.size[1]*.91, 
                              self.size[0]*.5, self.size[1]*.03), width = 5.0)

    def add_bounding_box(self, touch):
        #freeze all old bounding boxes
        for box in self.boxes:
            box.do_translation_x = False
            box.do_translation_y = False
            box.do_scale = False
        
        #add a new bounding box
        BBpos = (touch.x - self.box_size[0]/2, touch.y - self.box_size[1]/2)
        scatter = StretchScatter(pos=BBpos, do_rotation=False)
        scatter.scale_x = 1.0
        scatter.scale_y = 1.0
        
        scatter.add_widget(AnnotationBox())
        self.parent.add_widget(scatter)
        
        self.boxes.append(scatter)
        
    def submit_annotation(self, bt_instance):
        
        if self.paint:
            #save highlighted points as json
            self.annotations.put(self.all_imgs[self.img_num], pixels = self.pix_dict)
        else:
            #save bounding boxes as json
            ann_dict = {}
            for n, box in enumerate(self.boxes):
                scale_x, scale_y = box.get_scale_xy()
                ann_dict['Box %i: '%n] =  {"center": box.center, "scale_x": scale_x, "scale_y": scale_y,
                        "box_size": self.box_size,"img_size": self.size}
                
            self.annotations.put(self.all_imgs[self.img_num], annotations = ann_dict)
            
        #go to next unannotated image
        self.img_num += 1
        self.canvas.clear()
        
        #show the new image
        if self.img_num<len(self.all_imgs):
            self.create_annotation_station()
            
    def reset_annotations(self, bt_instance):
        self.create_annotation_station()
        
    def toggle_paint(self, bt_instance):
        self.paint = not self.paint
        print(self.paint)
        self.create_annotation_station()
            
    def create_annotation_station(self):
        self.canvas.clear()
        self.clear_widgets()
        [self.parent.remove_widget(box) for box in self.boxes]
        
        #skip if its already been annotated
        while self.all_imgs[self.img_num] in self.annotations:
            self.img_num += 1
        
        #initialize boxes
        self.boxes = []
        self.pixels = []
        
        #add image to background
        with self.canvas:
            self.bg_rect = Rectangle(source=self.dir+self.all_imgs[self.img_num], pos=self.pos, size=self.size)
        
        #make button to add boxes
       # btn_add = Button(pos=(25,25),size=(self.size[0]*.1,self.size[0]*.1),text='Add Box')
       # btn_add.bind(on_release=self.add_bounding_box)
       # self.add_widget(btn_add)
        
        #make reset button
        btn_reset = Button(pos=(25,25),
                           size=(self.size[0]*.1,self.size[0]*.1),text='Reset')
        btn_reset.bind(on_release=self.reset_annotations)
        self.add_widget(btn_reset)
        
        #make toggle paint button
        btn_paint = Button(pos=(self.size[0]-self.size[0]*.5-self.size[0]*.15/2,25),
                           size=(self.size[0]*.15,self.size[0]*.05),text='Toggle Paint')
        btn_paint.bind(on_release=self.toggle_paint)
        self.add_widget(btn_paint)
        
        
        #make button to submit annotation
        btn_submit = Button(pos=(self.size[0]-self.size[0]*.1-25,25),size=(self.size[0]*.1,self.size[0]*.1),
                            text='Submit')
        btn_submit.bind(on_release=self.submit_annotation)
        self.add_widget(btn_submit)
        self.add_progress_bar()
        
    def selected_file(self, *args):
        self.dir = args[1][0] + '/'
        
    def on_popup_close(self):
        self.all_imgs = listdir(self.dir)
        self.file_selected = True
        
        self.annotations = JsonStore(self.dir.split('/')[-2] + '.json')
        self.create_annotation_station()

class SaveFile(Popup):
    pass

class MyApp(App):

    def build(self):
        #set up background image
        self.parent = RootWidget()
            
        return self.parent


if __name__ == '__main__':
    MyApp().run()