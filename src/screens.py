import os, sys, math, colorsys, csv, logging
from unicodedata import name 
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw

gray = (50, 50, 50)
gray2 = (10,10,10)
gray3 = (130,130,130)
red =  (255, 0, 0)
blue = (0,0,255)

logger = logging.getLogger(__name__)

#Root Dir 

root_dir = Path(__file__).resolve().parent.parent

#Set default font 
ImageDraw.ImageDraw.font = ImageFont.truetype(root_dir / 'lib'/ 'font' /'RobotoMono-Light.ttf')

class Screen: 
    def __init__(self, name, tile_width, tile_height, tiles_w, tiles_h ) -> None:
        self.name = name
        self.width = int(tile_width * tiles_w) 
        self.height = int(tile_height * tiles_h)
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tiles_w = tiles_w
        self.tiles_h = tiles_h
        self.colorBGHue = 0
        empty_2d_array = [[None for _ in range(self.tiles_w)] for _ in range(self.tiles_h)]


class ScreenDrawer:
    def __init__(self, screen: Screen, path) -> None:
        self.screen = screen
        self.path = path
        self.name = screen.name
        self.width = int(screen.tile_width * screen.tiles_w) 
        self.height = int(screen.tile_height * screen.tiles_h)
        self.tile_width = screen.tile_width
        self.tile_height = screen.tile_height
        self.tiles_w = screen.tiles_w
        self.tiles_h = screen.tiles_h
        self.colorBGHue = screen.colorBGHue
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
        font = ImageFont.truetype(root_dir / 'lib'/ 'font' /'RobotoMono-Light.ttf', font_size)

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
        font = self.draw.getfont()

        text_width,text_height = self.get_text_dimensions(res_text, font)
        font_size = int(min(self.height,self.width)/max(len(self.name),len(res_text)))

        font = ImageFont.truetype(root_dir / 'lib'/ 'font' /'RobotoMono-Light.ttf', font_size)

        #Draw Screen Name
        self.draw.text((self.width/2,self.height/2), self.name, fill=(255,255,255), anchor='md')

        #Draw Resolution
        self.draw.text((self.width/2,self.height/2), res_text, fill=(255,255,255), anchor='mt')

    def get_text_dimensions(self, text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
        ascent, descent = font.getmetrics()

        text_width = font.getmask(text_string).getbbox()[2]
        text_height = font.getmask(text_string).getbbox()[3] + descent

        return (text_width, text_height)

    def hsv_to_rgb(self, h,s,v):
        rgb_fraction = colorsys.hsv_to_rgb(h / 360, s / 100, v / 100)  # colorsys expects HSV in the range [0, 1]
        rgb = tuple(int(i * 255) for i in rgb_fraction)  # Scale to [0, 255]
        return rgb

class ScreenList:
    def __init__(self, csv_path) -> None:
     
     self.rawScreens = self.parse_csv_with_header(csv_path)
     self.screens = []

    def parse_csv_with_header(self, csv_path):
    # Define the expected header as a tuple of column names
        expected_header = (
            "WALL", "Naming", "Notes", "Product", "Tiles_Wide", "Tiles_High", 
            "Total Tiles", "Pitch (mm)", "Tile MM Width", "Tile MM Height", 
            "Tile_Px_Width", "Tile_Px_Height"
        )

        # Initialize a list to hold the parsed data
        parsed_data = []

        try:
            # Open the CSV file
            with open(csv_path, mode='r', encoding='utf-8') as file:
                # Use csv.reader to parse the file
                csv_reader = csv.reader(file)

                # Flag to determine when we've found the header
                header_found = False

                # Scan through the file to find the header
                for row in csv_reader:
                    if row[:len(expected_header)] == list(expected_header):
                        header_found = True
                        naming_index = row.index("WALL")
                        break  # Break the loop once the header is found
                
                    if header_found:
                    # Use csv.DictReader to handle the rows as dictionaries
                        file.seek(0)  # Reset file pointer to start after finding header
                        dict_reader = csv.DictReader(file)

                        # Skip rows until the header is found again by DictReader
                        for row in dict_reader:
                            if list(row.keys())[:len(expected_header)] == list(expected_header):
                                break

                        # Now, iterate through the remaining rows as dictionaries
                        for row in dict_reader:
                            # Exclude rows where the "Naming" column is empty
                            if row["WALL"].strip():  # Check if "Naming" value is non-empty
                                self.screens.append(
                                    Screen(row["WALL"], row['Tile_Px_Width'],row['Tile_Px_Height'],row['Tiles_Wide'],row['Tiles_Heigh'])
                                    )
                                
                else:
                    print("Expected header not found in the file.")
                    return None

        except FileNotFoundError:
            print(f"Error: File '{csv_path}' not found.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        # Return the parsed data
        return parsed_data
            


def test():
    print(root_dir)

    csvTest = ScreenList(root_dir / 'temp' / 'testcsv.csv')

    print(csvTest.rawScreens)
    
    #Make Dirs... This will need to change 
    os.makedirs(root_dir / 'testing' / 'Content', exist_ok=True)
    os.makedirs(root_dir / 'testing' / 'Eng', exist_ok=True)
    os.makedirs(root_dir / 'testing' / 'Stealth', exist_ok=True)

    path = root_dir / 'testing'
    testScreen = Screen("USC", 80, 160, 11, 8)
    testing = ScreenDrawer(testScreen,path)

    

    testing.draw_content()
    testing.draw_eng()
    testing.draw_stealth()

        

test()