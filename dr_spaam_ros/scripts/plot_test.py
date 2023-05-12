#! /usr/bin/env python3
#coding:utf-8

import rospy
import numpy as np
from dr_spaam_ros.msg import LegPoseArray
import matplotlib.pyplot as plt

point = []
def callback_leg(msg):
    global point
    point = msg.poses

def plot():
    global point
    sub_leg = rospy.Subscriber("/dr_spaam_detections", LegPoseArray, callback_leg)
    while (not rospy.is_shutdown()):
        p_x = []
        p_y = []
        for i in range(len(point)):
            p_x = p_x + [point[i].position.x]
            p_y = p_y + [point[i].position.y*(-1)]
        plt.cla()
        plt.ylim([-0.1, 3.0])
        plt.xlim([-2.0, 2.0])
        print(p_x, p_y)
        plt.plot(p_y, p_x, 'or')
        plt.pause(0.001)


if __name__ == '__main__':
    rospy.init_node('plot_test')
    plot()
    rospy.spin()