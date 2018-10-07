#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 11:14:45 2018

@author: david
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.storage.jsonstore import JsonStore
from kivy.graphics import Rectangle
from kivy.graphics import Line, Color

from widgets import AnnotationBox, StretchScatter, SaveFile
from config import Config
from os import listdir
            
class RootWidget(Widget):
    def __init__(self):
        super(RootWidget, self).__init__()
        self.filepop = SaveFile()
        self.filepop.open()
        
        self.img_num = 0
        self.boxes = []
        self.scatter = None
        self.box_size = AnnotationBox().box_size
        
        self.file_selected = False
        self.paint = False
        
        self.stroke_num = 0
        self.pix_dict = {}
        self.ann_dict = {}
        
    # create progress bar if desired ----------------------------------------------------------------
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
        
        
    # define what touch initiates ----------------------------------------------------------------
    def on_touch_down(self, touch):
        if self.file_selected and touch.is_double_tap and not self.paint:
            #add bounding box on double tap
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
                self.pix_dict['Object %i: '%self.stroke_num]["points"].append([int(touch.x), int(touch.y)])
            else:
                self.pix_dict['Object %i: '%self.stroke_num] = {
                        "points": [[int(touch.x), int(touch.y)]],
                        "img_size": self.size
                }


    # define what buttons do ----------------------------------------------------------------
    def add_bounding_box(self, touch):
        #add properties of last bounding box
        if self.scatter:
            #add position and scale to json
            scale_x, scale_y, center = self.scatter.get_scale_xy()
            self.ann_dict['Box %i: '%len(self.boxes)] =  {
                "center": center, 
                "scale_x": scale_x, "scale_y": scale_y,
                "box_size": self.box_size,"img_size": self.size
                }
                    
        #freeze all old bounding boxes
        for box in self.boxes:
            box.do_translation_x = False
            box.do_translation_y = False
            box.do_scale = False
        
        #add a new bounding box
        BBpos = (touch.x - self.box_size[0]/2, touch.y - self.box_size[1]/2)
        self.scatter = StretchScatter(pos=BBpos, do_rotation=False)
        self.scatter.scale_x = 1.0
        self.scatter.scale_y = 1.0
        
        self.scatter.add_widget(AnnotationBox())
        self.parent.add_widget(self.scatter)
        
        self.boxes.append(self.scatter)
        
    def submit_annotation(self, bt_instance):
        
        if self.paint:
            #save highlighted points as json
            self.annotations.put(self.all_imgs[self.img_num], pixels = self.pix_dict)
        else:
            #add properties of last bounding box
            if self.scatter:
                #add position and scale to json
                scale_x, scale_y, center = self.scatter.get_scale_xy()
                self.ann_dict['Box %i: '%len(self.boxes)] =  {"center": center, 
                              "scale_x": scale_x, "scale_y": scale_y,
                              "box_size": self.box_size,"img_size": self.size}
                            
            #save bounding boxes as json
            self.annotations.put(self.all_imgs[self.img_num], annotations = self.ann_dict)
            
        #go to next unannotated image
        self.img_num += 1

        self.canvas.clear()
        self.clear_widgets()
        [self.parent.remove_widget(box) for box in self.boxes]

        self.pix_dict = {}
        self.ann_dict = {}
        self.scatter = None
        self.stroke_num = 0
        
        #show the new image
        if self.img_num<len(self.all_imgs):
            self.create_annotation_station()
            
    def reset_annotations(self, bt_instance):
        self.pix_dict = {}
        self.ann_dict = {}
        self.scatter = None
        self.stroke_num = 0
        self.create_annotation_station()
        
    def toggle_paint(self, bt_instance):
        self.paint = not self.paint
        self.create_annotation_station()
    
    
    # create backdrop for annotation ----------------------------------------------------------------
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
        
        #make progress bar
        if Config.SHOW_PROGRESS_BAR:
            self.add_progress_bar()
    
    
    # methods to select folder for annotation ----------------------------------------------------------------    
    def selected_file(self, *args):
        self.dir = args[1][0] + '/'
        
    def on_popup_close(self):
        self.all_imgs = listdir(self.dir)
        self.file_selected = True
        
        self.annotations = JsonStore(self.dir.split('/')[-2] + '.json')
        self.create_annotation_station()

class MyApp(App):

    def build(self):
        #set up background image
        self.parent = RootWidget()
            
        return self.parent


if __name__ == '__main__':
    MyApp().run()