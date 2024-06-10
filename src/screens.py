import os, sys, math
from unicodedata import name 
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw

gray = (50, 50, 50)
gray2 = (10,10,10)
gray3 = (130,130,130)
red =  (255, 0, 0)
blue = (0,0,255)

#Root Dir 

root_dir = Path(__file__).resolve().parent.parent

#Set default font 
ImageDraw.ImageDraw.font = ImageFont.truetype("../lib/font/RobotoMono-Light.ttf")

class Screen: 
    def __init__(self, name, path, tile_width, tile_height, tiles_w, tiles_h ) -> None:
        self.name = name
        self.path = path
        self.width = int(tile_width * tiles_w) 
        self.height = int(tile_height * tiles_h)
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tiles_w = tiles_w
        self.tiles_h = tiles_h
        self.colorA = blue
        self.colorB = red
        self.im = Image.new("RGB", (self.width, self.height), 0)
        self.draw = ImageDraw.Draw(self.im)



    def draw_eng(self):
        self.resetImg()
        self.draw_tiles()
        self.draw_screen_text()
        self.im.save(self.path / "Eng" / (self.name+".png"))
        pass


    def draw_content(self):
        self.resetImg()
        self.drawBG(gray, red)
        self.draw_screen_text()
        self.im.save(self.path / 'Content' / (self.name+".png"))
        pass

    def draw_stealth(self):
        self.resetImg()
        self.drawBG((0,0,0), (76,185,227))
        self.im.save(self.path / 'Stealth' / (self.name+".png"))
        pass

    def draw_pretty(self):
        self.resetImg()
        pass

    def resetImg(self):
        self.im = Image.new("RGB", (self.width, self.height), 0)
        self.draw = ImageDraw.Draw(self.im)

    def drawBG(self, color, outline_color):
        self.draw.rectangle((0,0,self.width-1,self.height-1), fill=color, outline=outline_color)

    #Note that colors are defined per class
    def draw_tiles(self):
        cur_x = 0
        cur_y = 0

        font_size = int(min(self.height,self.width)/6)
        font = ImageFont.truetype("../lib/font/RobotoMono-Light.ttf", font_size)

        for i in range(math.ceil(self.tiles_h)):
            for j in range(self.tiles_w):
                tile_y_height = math.ceil(self.tile_height/2) if (self.tiles_h-i == 0.5) else self.tile_height;
                BG_color = gray if (j+i)%2 == 0 else gray2
                stoke = red if (j+i)%2 == 0 else blue

                self.draw.rectangle((cur_x, cur_y, cur_x+(self.tile_width-1), cur_y+(tile_y_height-1)), BG_color,stoke,1)
                self.draw.text((cur_x+self.tile_width/2, cur_y+tile_y_height/2), str(j+1) + ',' + str(i+1), (255,255,255), anchor='mm')
            
                cur_x += self.tile_width

            cur_x = 0
            cur_y += tile_y_height
                

    def draw_screen_text(self):
        res_text = str(self.width) + "x" + str(self.height)
        #calculate font size
        font_size = int(min(self.height,self.width)/max(len(self.name),len(res_text)))

        font = ImageFont.truetype("../lib/font/RobotoMono-Light.ttf", font_size)

        #Draw Screen Name
        self.draw.text((self.width/2,self.height/2), self.name, font=font, fill=(255,255,255), anchor='md')

        #Draw Resolution
        self.draw.text((self.width/2,self.height/2), res_text, font=font, fill=(255,255,255), anchor='mt')

    def get_text_dimensions(self, text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
        ascent, descent = font.getmetrics()

        text_width = font.getmask(text_string).getbbox()[2]
        text_height = font.getmask(text_string).getbbox()[3] + descent

        return (text_width, text_height)

class ScreenList:
    def __init__(self) -> None:
     pass


def test():
    print(root_dir)
    
    #Make Dirs... This will need to change 
    os.makedirs(root_dir / 'testing' / 'Content', exist_ok=True)
    os.makedirs(root_dir / 'testing' / 'Eng', exist_ok=True)
    os.makedirs(root_dir / 'testing' / 'Stealth', exist_ok=True)

    path = root_dir / 'testing'
    testing = Screen("USC", path, 80, 160, 11, 8)

    

    testing.draw_content()
    testing.draw_eng()
    testing.draw_stealth()

        

test()