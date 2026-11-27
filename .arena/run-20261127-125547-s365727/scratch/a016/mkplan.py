import cv2, numpy as np
s=50  # px/m ; 8m x 6m house, 0.2 m walls (10px)
img=np.full((400,500,3),255,np.uint8)
cv2.rectangle(img,(50,50),(450,350),(0,0,0),10)            # outer
cv2.line(img,(250,50),(250,350),(0,0,0),10)                # partition
cv2.rectangle(img,(240,150),(260,210),(255,255,255),-1)    # door gap in partition (1.2m)
cv2.putText(img,"Living 4.0 x 6.0",(70,120),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),1)  # text must be dropped
cv2.line(img,(50,30),(450,30),(0,0,0),1)                   # dimension line must be dropped
cv2.imwrite("plan.png",img)
