#! /usr/bin/env python3
#coding:utf-8

import rospy
import numpy as np
import math
from dr_spaam_ros.msg import LegPoseArray
import matplotlib.pyplot as plt


t = 0.05
st = 0.1

point = []
def callback_leg(msg):
    global point
    point = msg.poses

def plot():
    global point
    global t, st
    start = True
    sub_leg = rospy.Subscriber("/dr_spaam_detections", LegPoseArray, callback_leg)
    while (not rospy.is_shutdown()):
        if start:
            p_x_backup_0 = []
            p_y_backup_0 = []
            p_x_backup_1 = []
            p_y_backup_1 = []
            p_x = []
            p_y = []
            p_x_future = []
            p_y_future = []
            for i in range(len(point)):
                p_x_backup_0 = p_x_backup_0 + [point[i].position.x]
                p_y_backup_0 = p_y_backup_0 + [point[i].position.y*(-1)]
            rospy.sleep(t)
            for i in range(len(point)):
                p_x_backup_1 = p_x_backup_1 + [point[i].position.x]
                p_y_backup_1 = p_y_backup_1 + [point[i].position.y*(-1)]
            rospy.sleep(t)
            for i in range(len(point)):
                p_x = p_x + [point[i].position.x]
                p_y = p_y + [point[i].position.y*(-1)]
            start = False
        else:
            p_x_backup_0 = p_x_backup_1
            p_y_backup_0 = p_y_backup_1
            p_x_backup_1 = p_x
            p_y_backup_1 = p_y
            p_x = []
            p_y = []
            p_x_future = []
            p_y_future = []
            rospy.sleep(t)
            for i in range(len(point)):
                p_x = p_x + [point[i].position.x]
                p_y = p_y + [point[i].position.y*(-1)]

        if (len(p_x_backup_0) > len(p_x_backup_1)):
            if (len(p_x_backup_1) > len(p_x)):
                l = len(p_x)
            else:
                l = len(p_x_backup_1)
        else:
            if (len(p_x_backup_0) > len(p_x)):
                l = len(p_x)
            else:
                l = len(p_x_backup_0)
        

        ##############
        if ((len(p_x_backup_0) != 0) and (len(p_x_backup_1) != 0) and (len(p_x) != 0)):
            ii = 0
            ran = float("inf")
            for i in range(len(p_x_backup_0)):
                if np.sqrt(p_x_backup_0[i]**2 + p_y_backup_0[i]**2) < ran:
                    ran = np.sqrt(p_x_backup_0[i]**2 + p_y_backup_0[i]**2)
                    ii = i
            temp_x = p_x_backup_0[0]
            temp_y = p_y_backup_0[0]
            p_x_backup_0[0] = p_x_backup_0[ii]
            p_y_backup_0[0] = p_y_backup_0[ii]
            p_x_backup_0[ii] = temp_x
            p_y_backup_0[ii] = temp_y
            ii = 0
            ran = float("inf")
            for i in range(len(p_x_backup_1)):
                if np.sqrt((p_x_backup_1[i] - p_x_backup_0[0])**2 + (p_y_backup_1[i] - p_y_backup_0[0])**2) < ran:
                    ran = np.sqrt((p_x_backup_1[i] - p_x_backup_0[0])**2 + (p_y_backup_1[i] - p_y_backup_0[0])**2)
                    ii = i
            temp_x = p_x_backup_1[0]
            temp_y = p_y_backup_1[0]
            p_x_backup_1[0] = p_x_backup_1[ii]
            p_y_backup_1[0] = p_y_backup_1[ii]
            p_x_backup_1[ii] = temp_x
            p_y_backup_1[ii] = temp_y
            ii = 0
            ran = float("inf")
            for i in range(len(p_x)):
                if np.sqrt((p_x[i] - p_x_backup_1[0])**2 + (p_y[i] - p_y_backup_1[0])**2) < ran:
                    ran = np.sqrt((p_x[i] - p_x_backup_1[0])**2 + (p_y[i] - p_y_backup_1[0])**2)
                    ii = i
            temp_x = p_x[0]
            temp_y = p_y[0]
            p_x[0] = p_x[ii]
            p_y[0] = p_y[ii]
            p_x[ii] = temp_x
            p_y[ii] = temp_y
        #############


        v1 = []
        v2 = []
        a = []
        for i in range(l):
            v1 = v1 + [[(p_x_backup_1[i] - p_x_backup_0[i])/t ,  (p_y_backup_1[i] - p_y_backup_0[i])/t]]
            v2 = v2 + [[(p_x[i]          - p_x_backup_1[i])/t ,  (p_y[i]          - p_y_backup_1[i])/t]]
        for i in range(l):
            a = a + [[(v2[i][0] - v1[i][0])/t ,  (v2[i][1] - v1[i][1])/t]]
        plt.cla()
        plt.ylim([-0.1, 4.0])
        plt.xlim([-2.0, 2.0])
        for i in range(l):
            p_x_future = p_x_future + [p_x[i] + v2[i][0]*st + (1/2)*a[i][0]*st*st]
            p_y_future = p_y_future + [p_y[i] + v2[i][1]*st + (1/2)*a[i][1]*st*st]
            if (v2[i][0] != 0.0):
                yaw = np.arctan(v2[i][1]/v2[i][0])*(-1) + np.pi/2
            else:
                yaw = 0.0 + np.pi/2
            # plt.arrow(p_y[i], p_x[i], 0.2*math.cos(yaw), 0.2*math.sin(yaw), head_length=0.03, head_width=0.03)
            if (a[i][0] != 0.0):
                yaw = np.arctan(a[i][1]/a[i][0])*(-1) + np.pi/2
            else:
                yaw = 0.0 + np.pi/2
            # plt.arrow(p_y[i], p_x[i], 0.2*math.cos(yaw), 0.2*math.sin(yaw), head_length=0.03, head_width=0.03)

        # if ((len(p_x_backup_0) != 0) and (len(p_x_backup_1) != 0) and (len(p_x) != 0)):
        #     print(p_x_backup_0[0],p_y_backup_0[0])
        #     print(p_x_backup_1[0],p_y_backup_1[0])
        #     print(p_x[0],p_y[0])
        #     print(v1[0])
        #     print(v2[0])
        #     print(a[0])
        #     print()
        #     print()

        plt.plot(p_y, p_x, 'or')
        plt.plot(p_y_future, p_x_future, 'ob')
        plt.pause(t/1.0)



def plot_only():
    global point
    global t
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
        plt.pause(t/1.02)


if __name__ == '__main__':
    rospy.init_node('plot_test')
    plot()
    # plot_only()
    rospy.spin()