 //<>//



Table inputTable;
PFont f;

void setupmaker(){
  //f = createFont("Arial.ttf", 10);
  PGraphics pg;
  
}

//Note some fuckery on casting num_tiles_heigh to deal with 1/2 tiles. I hate 1/2 tiles 
void draw_tiles(PGraphics pg, int tile_width, int tile_height, int num_tiles_wide, float num_tiles_tall){
  int count_tall = ceil(num_tiles_tall);
  int count_wide = num_tiles_wide;
  int cur_x = 0;
  int cur_y = 0;
  
  
  //Set Up Text
  //pg.textFont(f);
  pg.textSize((min(tile_width, tile_height)/6));
  //pg.textSize(40);
  pg.textAlign(CENTER, CENTER);

  for(int i=0; i<count_tall; i++){
    for(int j=0; j<count_wide; j++){
      int tile_y_height = (num_tiles_tall-i == 0.5) ? (tile_height/2): tile_height;
      color tile_bg = j%2==0 ? color(50,50,50) : color(0,0,0);
      
      pg.fill(tile_bg);
      pg.stroke(255,255,255);
      pg.rect(cur_x,cur_y,(tile_width-1),(tile_y_height-1));
      //Write in Tile numbers 
      pg.stroke(255);
      pg.fill(255);
      char row = char(i+65);
      pg.text(row+""+j, (cur_x+(tile_width/2)), (cur_y+(tile_y_height/2)));
      cur_x = cur_x + tile_width;
    }
    cur_x = 0;
    cur_y = cur_y+tile_height;
  }
}

void draw_text(PGraphics pg, String screen_name){
  pg.textSize(pg.height/4);
  pg.textAlign(CENTER);
  
  int x_screen = pg.width/2;
  int y_screen = round(pg.height * .4);
  int x_res = pg.width/2;
  int y_res = round(pg.height * .8);
  
    //Main Text in white
  pg.fill(255);
  pg.text(screen_name, x_screen, y_screen);
  pg.text((pg.width+"x"+pg.height), x_res, y_res);
  
}

void draw_BG(PGraphics pg, int w, int h){
  pg.fill(0);
  pg.stroke(0);
  pg.rect(0,0,w,h);
}
  

void drawPNGs(Table inputTable){
  int counter = 1;
  
   for(TableRow row : inputTable.rows()){
     String screen_name   = row.getString("Screen_Name");
     String tile_type     = row.getString("Tile_Type");
     int tile_pixel_width = row.getInt("Tile_W");
     int tile_pixel_height = row.getInt("Tile_H");
     int tiles_wide       = row.getInt("Tiles_Wide"); 
     float tiles_high     = row.getFloat("Tiles_High");
     int pixels_wide      = row.getInt("Pixels_W");
     int pixels_heigh     = row.getInt("Pixels_H");
     
     //Create new pGraphics object size of screen 
     PGraphics screen = createGraphics(pixels_wide, pixels_heigh);
     screen.beginDraw();
     //Now call all of the helper functions
     draw_BG(screen, pixels_wide, pixels_heigh);
     draw_tiles(screen, tile_pixel_width, tile_pixel_height, tiles_wide, tiles_high);
     draw_text(screen, screen_name);
     screen.endDraw();
     screen.save("AS/"+nf(counter,3)+"_"+screen_name+".png");
     counter++;
   }
}
