#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from copy import copy, deepcopy
from nav_msgs.msg import Odometry
import tf
import math
import sys
from geometry_msgs.msg import Twist
from gnomevfs._gnomevfs import Drive
from __builtin__ import False
from docutils.nodes import sidebar
#from BUG2_Local_planner import obstacle_range

#defining the global variables
start = True
STEPS=0
################# GOAL POINTS ######################
prefix="pioneer1"
goal_point_x = -2
goal_point_y = 40
####################################################



##################### OFFSETS ######################
yaw_offset = 0.25  # offset to the yaw angle in which we have to reduce error
lp_offset = 0.4  # minimum distance from obstacle to follow for local planner
####################################################

##################### RANGES #######################
obstacle_range = 60 
angleDiv = 3.14 / 1000
distanctanceIntoMax=0.5
goal_yaw=0
computeGoalYaw=0
####################################################

##################### FLAGS ########################
YAW_FLAG = 0
PLANNER_FLAG = 0  
####################################################
##################### DATA #########################
data_range=0
goal_point = 0 
mask=0
goal_point=0
compute_currentYAW = 0
compute_currentX = 0
compute_currentY = 0   
yawObtain=False
#####################################################
def driveStop():
    pub = rospy.Publisher(prefix+'/cmd_vel', Twist)
    twist = Twist()
    for i in range(0, 60):
        if i < 30:
            twist.linear.x = 0.1
        else: 
            twist.linear.x = 0.0
    print "STOP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"        
    
    pub.publish(twist)
def drive(vel):
    pub = rospy.Publisher(prefix+'/cmd_vel', Twist)
    twist = Twist()
    twist.linear.x = vel
       
           
    
    pub.publish(twist)

    
def tf_QuatQartesian(dataX, dataY, dataZ, dataYaw):
    quaternion = (dataX, dataY, dataZ, dataYaw)
    euler = tf.transformations.euler_from_quaternion(quaternion)
    yaw = euler[2]
    return yaw

def twistYaw(goalYaw, currentYaw):
    global YAW_FLAG
    pub = rospy.Publisher(prefix+'/cmd_vel', Twist)
    # rospy.init_node('twistYaw')
    twist = Twist()
    # driveStop()
    # goalYaw=goalYaw+3.14
    # currentYaw=currentYaw+3.14
    #print "GOAL_YAW:" + str(goalYaw)
    #print "CURRNET YAW:" + str(currentYaw)
    if goalYaw > currentYaw:
        twist.angular.z = 0.1
        #print "Turning left"
        if goalYaw - 0.01 < currentYaw:
            twist.angular.z = 0.0  
            YAW_FLAG = 1  
            #print "Turning left stopped, yaw reached"
    if goalYaw < currentYaw:
        twist.angular.z = -0.1
        #print "Turning right"
        if goalYaw + 0.01 > currentYaw:
            twist.angular.z = 0.0 
            YAW_FLAG = 1
            #print "Turning right stopped, yaw reached"
    pub.publish(twist)
    
def twistStop():
    pub = rospy.Publisher(prefix+'/cmd_vel', Twist)
    # rospy.init_node('twistYaw')
    twist = Twist()
    
    twist.angular.z = 0.00 
            
    pub.publish(twist)
    
  
    
def twist(dir,twistVel):
    pub = rospy.Publisher(prefix+'/cmd_vel', Twist)
    # rospy.init_node('twistYaw')
    twist = Twist()
    if dir==1:
        twist.angular.z = twistVel
    if dir==0:
        twist.angular.z = -twistVel
        
    pub.publish(twist)
   
    
def driveToPoint(goalP, currentP):
    global start
    
    pub = rospy.Publisher(prefix+'/cmd_vel', Twist)
    twist = Twist()
    
    
    if start == True:
        
        for i in range(0, 60):
            if i < 30:
                twist.linear.x = 0.1
            else:
                twist.linear.x = 0.3
                start = False
        
    if goalP > currentP or goalP < currentP:
            twist.linear.x = 0.0
            
            if goalP - 0.02 > currentP or goalP + 0.02 < currentP:
                twist.linear.x = 0.1
                if goalP - 0.2 > currentP or goalP + 0.2 < currentP:
                    twist.linear.x = 0.3
                    if (goalP - 1.0 > currentP) or (goalP + 1.0 < currentP):
                        twist.linear.x = 0.3
    print "Goal point:"+str(goalP)
    print "Current point:"+str(currentP)                    
    pub.publish(twist)

def computeYaw(goalPoint):
    
    if goalPoint > len(data_range)/2-1 == 0:
        #print "should compute to left"
        goalYaw = compute_currentYAW + angleDiv*2 * (goalPoint-len(data_range)/2)
    else:
        #print "should compute to right"
        goalYaw = compute_currentYAW - angleDiv*2 * (len(data_range)/2-goalPoint)
    #print len(data_range)/2-goalPoint
    #print angleDiv * (len(data_range)/2-goalPoint)
    return goalYaw

def getGoalYaw(startX, startY, goalX, goalY):
    # compute the yaw between start point and global point
    goal_yaw = math.atan2((goalY - startY), (goalX - startX))
    return goal_yaw

def regulator(data,currentX,currentY,yaw):
    global STEPS
    global yawObtain
    global PLANNER_FLAG
    if STEPS==0:
        twist(0,0.2)
        print data_range
        if data[len(data)-1]>lp_offset-0.15 and data[len(data)-1]<lp_offset+0.15 :
            twistStop()
            STEPS=1
    if STEPS==1:
        twistStop()
        drive(0.2)
        if data[len(data)-1] >0.75:
            vel=0.4
        else:
            vel=0.1
        print "Drive forward"
        if data[len(data)-1]<lp_offset-0.15 :
            driveStop()
            twist(0,vel)
            print "Twsit to right"
            
        if data[len(data)-1]>lp_offset+0.15 :
            driveStop()
            twist(1,vel)
            print "Twist to left"
            
        if yaw > goal_yaw+0.78:
            #STEPS=0
            PLANNER_FLAG=0
        #if data[len(data)-1]>4:
        #    twistStop()
        #    driveStop()
        #    STEPS=2
            
    #if STEPS==2: 
        #if yawObtain==False:
        #       compute_currentX = currentX
        #       compute_currentY = currentY 
        #print "Drive to free point"
        #driveToPoint(compute_currentX+lp_offset, currentX)
        #STEPS=3
        
        
        
        
    print "STEP:"+str(STEPS)
   
 
def global_planner(yaw, goal_yaw, current_x, current_y):
    global YAW_FLAG
    global STEPS
    print "print global planner is working"  
    print goal_point_x
    print goal_point_y
    print current_x
    print current_y  
    STEPS=0
    if goal_yaw + yaw_offset > yaw or goal_yaw - yaw_offset < yaw:
        YAW_FLAG = 0
    if YAW_FLAG == 0:
        twistYaw(goal_yaw, yaw)
    if YAW_FLAG == 1:
        driveToPoint(goal_point_y, current_y)
        



def local_planner(yaw, currentX, currentY):
    driveStop()
    regulator(data_range,currentX,currentY,yaw)
    
def laser_data(data):
    global PLANNER_FLAG
    global data_range
    global goal_point
    global computeGoalYaw
    data_range = list(data.ranges)  # get laser data in frame
        
    for i in range(0, len(data.ranges)):
        if data_range[i] < lp_offset:
            
            if PLANNER_FLAG == 0:
                if i >= ((len(data.ranges) / 2 - 1) - obstacle_range ) and i <= ((len(data.ranges) / 2 - 1) + obstacle_range ):
                    PLANNER_FLAG = 1
                    computeGoalYaw=goal_yaw
    
    print "PLANNER FLAG:" +str(PLANNER_FLAG)
                  
def odometry_data(data):
    global compute_currentYAW
    global goal_yaw
    # using global variables    
    yaw = tf_QuatQartesian(data.pose.pose.orientation.x, data.pose.pose.orientation.y, data.pose.pose.orientation.z, data.pose.pose.orientation.w)
    goal_yaw = getGoalYaw(data.pose.pose.position.x, data.pose.pose.position.y, goal_point_x, goal_point_y)
    # print yaw
    if PLANNER_FLAG == 0:
        global_planner(yaw, goal_yaw, data.pose.pose.position.x, data.pose.pose.position.y)
        #local_planner(yaw, data.pose.pose.position.x, data.pose.pose.position.y)
        #compute_currentYAW=yaw
    if PLANNER_FLAG == 1:
        #driveStop()
        #print data_range
        #driveStop()
        #test(yaw, data.pose.pose.position.x, data.pose.pose.position.y) 
        local_planner(yaw, data.pose.pose.position.x, data.pose.pose.position.y) 
    if PLANNER_FLAG == 2:
        driveStop()  
           
def listener():
    
    rospy.init_node('planner', anonymous=True)  # Node initialization
    rospy.Subscriber("/"+prefix+"/scan", LaserScan, laser_data)  # LaserScan subscriber initialization
    rospy.Subscriber("/"+prefix+"/odom", Odometry, odometry_data)  # Odometry subscriber initialization
    
    rospy.spin()  # Subscribers are working until the node will be killed
    

if __name__ == '__main__':
    listener()
    
