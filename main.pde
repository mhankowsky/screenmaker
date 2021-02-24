
Table table;

public void settings(){
  //This size not matter
  size(600,800);
  
}

void setup(){ 
  
  table = loadTable("AS_2021.csv", "header");
  drawPNGs(table);
}
