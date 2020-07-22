#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import serial.tools.list_ports
import time
import threading
import json
import os

class SerialTool:
    def __init__(self, ser_name):
        try:
            self.ser = serial.Serial(ser_name, baudrate=115200, timeout=None, stopbits=1, bytesize=8)
            self.name = ser_name + "-" + time.strftime("%Y%m%d-%H-%M-%S", time.localtime()) + ".log"
            self.last = ""
            self.data = ""
            self.listData = []
            self.getConfig()
            self.flag = False
            self.cache = ""
            self.temp = ""
            self.k = {}
            if self.keywords:
                for j in self.keywords:
                    self.k[j] = 0
            self.lock = threading.Lock()
            self.t = threading.Thread(target = self.getLog)
            self.t.start()
            self.send()
            while True:
                try:
                    args = input("")
                    if args == self.stop:
                        self.lock.acquire()
                        self.display_log = False
                        self.lock.release()
                        self.ser.write((chr(0x03) + "\r\n").encode())
                    else:
                        self.display_log = True
                        self.ser.write((args + "\r\n").encode())
                except Exception as e:
                    print(e)
        except serial.serialutil.SerialException:
            print("串口号已被占用或串口号错误")

    def getLog(self):
        while True:
            try:
                self.num = self.ser.in_waiting
                self.temp_bytes = self.ser.read(size = self.num)
                try:
                    self.cache = (self.temp_bytes.decode("iso-8859-1")).replace("\000", "")
                    self.temp = self.temp + self.cache
                    if "\n" in self.temp:
                        if self.temp.strip():
                            self.analyze()
                except Exception as e:
                    pass
            except serial.serialutil.SerialException as e:
                pass
            time.sleep(0.002)

    def analyze(self):
        self.data = self.data + self.temp
        if self.data[-1] != "\n":
            self.listTemp = self.data.strip().split("\n")
            self.listData = self.listTemp[:-1]
            self.showLog()
            self.data = self.listTemp[-1]
            self.temp = ""
        else:
            self.listData = self.data.strip().split("\n")
            self.showLog()
            self.data = ""
            self.temp = ""
    
    def showLog(self):   
        with open(self.name, "a")as f:
            for i in self.listData:
                if i.strip():
                    try:
                        self.determine(i.strip())
                        if self.display_log == True:
                            print(i.strip())
                        if self.flag == True:
                            self.display_log = False
                            self.flag = False
                        f.write(self.getTime() + i.strip() + "\n")
                    except Exception as e:
                        pass

    def getTime(self):
        return "[" + time.strftime("%Y%m%d_%H:%M:%S", time.localtime()) + "]"

    def getConfig(self):
        if os.path.exists("SerialToolConfig.json"):
            try:
                with open("SerialToolConfig.json")as g:
                    data = json.load(g)
                self.display_log = data["display_log"]
                self.stop = data["stop"]
                self.keywords = data["keywords"]
                self.list_send = data["send"]
                print("已识别配置")
            except Exception as e:
                self.display_log = False
                self.stop = "s"
                self.keywords = []
                self.list_send = []
        else:
            self.display_log = False
            self.stop = "s"
            self.keywords = []
            self.list_send = []

    def send(self):
        if self.list_send:
            for i in self.list_send:
                if type(i.get("word")) == str and type(i.get("start")) == int and type(i.get("step")) == int and type(i.get("count")) == int:
                     thread_send = threading.Thread(target = self.write_word, args=(i["word"], i["start"], i["step"], i["count"]))
                     thread_send.start()

    def write_word(self, word, start, step, count):
        time.sleep(start)
        for i in range(count):
            try:
                self.ser.write((word + "\r\n").encode())
                print(word + " " + str(i + 1) + "次")
                time.sleep(step)
            except:
                pass

    def determine(self, s):
        if s in self.keywords:
            self.display_log = True
            self.flag = True
            self.k[s] = self.k[s] + 1
            print(str(self.k[s]) + "次")
            
def main():
    port_list = list(serial.tools.list_ports.comports())
    if len(port_list) == 1:
        SerialTool(port_list[0][0])
    else:
        for i in port_list:
            print(i)
        print()
        while True:
            ser_name = input("请输入设备串口号：")
            SerialTool(ser_name)
    
if __name__ == '__main__':
    main()
