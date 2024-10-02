import os, sys, math, colorsys, csv, logging, re
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
    def __init__(self, name, tile_width, tile_height, tiles_w, tiles_h) -> None:
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
        self.filename = self.sanitize_filename(self.name)


    def draw_eng(self):
        self.resetImg()
        self.draw_tiles()
        self.draw_screen_text()
        self.im.save(self.path / '02_Eng_Blocks' / (self.name+".png"))
        pass


    def draw_content(self):
        self.resetImg()
        self.drawBG(gray, red)
        self.draw_screen_text()
        self.im.save(self.path / '01_Content_Blocks' / (self.name+".png"))
        pass

    def draw_stealth(self):
        self.resetImg()
        self.drawBG((0,0,0), (76,185,227))
        self.im.save(self.path / '03_Stealth_Blocks' / (self.name+".png"))
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

        BG_A = self.hsv_to_rgb(self.colorBGHue, 100, 30)
        BG_B = self.hsv_to_rgb(self.colorBGHue, 100, 15)

        font_size = int(min(self.height,self.width)/6)
        font = ImageFont.truetype(root_dir / 'lib'/ 'font' /'RobotoMono-Light.ttf', font_size)

        for i in range(math.ceil(self.tiles_h)):
            for j in range(self.tiles_w):
                tile_y_height = math.ceil(self.tile_height/2) if (self.tiles_h-i == 0.5) else self.tile_height;
                BG_color = BG_A if (j+i)%2 == 0 else BG_B
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

        font_size = int(min(self.height,self.width)/max(len(self.name),len(res_text)))

        print("FontSize:"+str(font_size))

        font = ImageFont.truetype(root_dir / 'lib'/ 'font' /'RobotoMono-Light.ttf', font_size)

        #Draw Screen Name
        self.draw.text((self.width/2,self.height/2), self.name.strip(), font=font, fill=(255,255,255), anchor='md')

        #Draw Resolution
        self.draw.text((self.width/2,self.height/2), res_text, font=font, fill=(255,255,255), anchor='ma')

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

    def sanitize_filename(self, filename, max_length=255):
        """
        Replace invalid characters in a string to make it a valid filename for both Windows and macOS.
        """
        # Define invalid characters for both systems
        invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'  # Windows forbidden chars + ASCII control chars
        invalid_mac_char = r'[:]'  # macOS forbidden chars

        # Replace invalid characters with an underscore
        sanitized = re.sub(invalid_chars, '_', filename)
        sanitized = re.sub(invalid_mac_char, '_', sanitized)

        # Strip leading and trailing whitespace
        sanitized = sanitized.strip()

        # Handle reserved names in Windows by appending an underscore if needed
        reserved_windows_names = {
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", 
            "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", 
            "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        }
        if sanitized.upper() in reserved_windows_names:
            sanitized += '_'

        # Truncate the filename to the maximum allowable length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

class ScreenList:
    def __init__(self, csv_path) -> None:
        # Initialize the screens list
        self.screens = []
        self.rawScreens = self.parse_csv_with_header(csv_path)
        self.setBGColors()


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
            # First, open the file to find the header and track the index
            header_index = -1
            with open(csv_path, mode='r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)

                # Track the current line number
                for i, row in enumerate(csv_reader):
                    # Check if the current row matches the expected header
                    if row[:len(expected_header)] == list(expected_header):
                        header_index = i
                        break

            if header_index != -1:
                # Now reopen the file and skip to the header_index
                with open(csv_path, mode='r', encoding='utf-8') as file:
                    csv_reader = csv.reader(file)

                    # Skip rows until we reach the header
                    for _ in range(header_index):
                        next(csv_reader)

                    # Initialize DictReader from this point
                    dict_reader = csv.DictReader(file)
                    print("------Dict Reader Initialized with Fieldnames------")
                    print(dict_reader.fieldnames)

                    # Now, iterate through the remaining rows as dictionaries
                    for row in dict_reader:
                        # Only process rows where the "WALL" column is non-empty
                        if row["WALL"].strip():
                            print(f"Adding screen with name: {row['WALL']}")
                            try:
                                self.screens.append(
                                    Screen(
                                        row["WALL"],  # WALL (screen name)
                                        int(row['Tile_Px_Width']),  # Tile_Px_Width as int
                                        int(row['Tile_Px_Height']),  # Tile_Px_Height as int
                                        int(row['Tiles_Wide']),  # Tiles_Wide as int
                                        int(row['Tiles_High'])  # Tiles_High as int
                                    )
                                )
                            except ValueError as e:
                                print(f"Skipping row due to value error: {e}")

            else:
                print("Expected header not found in the file.")
                return None

        except FileNotFoundError:
            print(f"Error: File '{csv_path}' not found.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def setBGColors(self):
        coloroffset = int( 360 / len(self.screens))
        curcol = 0
        i : Screen
        for i in self.screens:
            i.colorBGHue = curcol
            curcol = curcol + coloroffset


def test():
    print(root_dir)
    #Make Dirs... This will need to change
    csv_path = root_dir / 'temp' / 'LP.csv'
    filename = os.path.basename(csv_path).split('.')[0]
    path = root_dir / 'testing' / filename

    List = ScreenList(csv_path)
    print(List.screens)

    os.makedirs(root_dir / 'testing' / filename / '01_Content_Blocks', exist_ok=True)
    os.makedirs(root_dir / 'testing' / filename/ '02_Eng_Blocks', exist_ok=True)
    os.makedirs(root_dir / 'testing' / filename/ '03_Stealth_Blocks', exist_ok=True)

    for i in List.screens: 
        
        print(i.name)
        testing = ScreenDrawer(i,path)
        testing.draw_content()
        testing.draw_eng()
        testing.draw_stealth()

        

test()