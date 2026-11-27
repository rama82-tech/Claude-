from PIL import Image, ImageDraw
# 6m x 4m room at 100 px/m, wall 0.15 m, door gap 0.9 m in the bottom wall, window gap 1.2m in the top wall, partition at x=3.5
im=Image.new("L",(800,600),255); d=ImageDraw.Draw(im); o=100; t=15
def R(x0,y0,x1,y1): d.rectangle([o+x0,o+y0,o+x1,o+y1],fill=0)
R(-t//2,-t//2,600+t//2,t//2)          # top, will cut window
R(-t//2,400-t//2,600+t//2,400+t//2)   # bottom
R(-t//2,-t//2,t//2,400+t//2); R(600-t//2,-t//2,600+t//2,400+t//2)
R(350-t//2,0,350+t//2,400)
d.rectangle([o+100,o-10,o+220,o+10],fill=255)   # window gap
d.rectangle([o+150,o+390,o+240,o+410],fill=255) # door gap
d.line([o,o+470,o+600,o+470],fill=0,width=1); d.text((o+250,o+480),"6000",fill=0)  # dimension line + text
im.save("plan.png")
